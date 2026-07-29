"""DRF permission classes for the missions app."""

from django.db.models import Q
from rest_framework import permissions

from accounts.permissions import HasRBACPermission, get_user_role_code
from accounts.rbac import (
    PERMISSION_MISSIONS_ASSIGN,
    PERMISSION_MISSIONS_CREATE,
    PERMISSION_MISSIONS_RECORD_CONDITION,
    PERMISSION_MISSIONS_RECORD_OUTCOME,
    PERMISSION_MISSIONS_UPDATE_STATUS,
    PERMISSION_MISSIONS_VIEW,
)
from roles.models import (
    ADMIN_CODE,
    COMMANDER_CODE,
    DISPATCHER_CODE,
    OPERATOR_CODE,
    TECHNICIAN_CODE,
    VIEWER_CODE,
)

from .models import Condition, Mission, MissionDrone

# ============ RBAC-based Permissions ============
# Use centralized RBAC matrix for role checks.


class CanViewMission(HasRBACPermission):
    """Require the mission view RBAC permission."""

    required_permission = PERMISSION_MISSIONS_VIEW


def _has_operator_in_mission(obj, user_id):
    cache = getattr(obj, "_prefetched_objects_cache", {})
    if "mission_drones" in cache:
        return any(md.operator_id == user_id for md in obj.mission_drones.all())
    return obj.mission_drones.filter(operator_id=user_id).exists()


def _is_repair_or_writeoff_related_mission(mission):
    """Return whether a mission is tied to maintenance or write-off workflow."""
    cache = getattr(mission, "_prefetched_objects_cache", {})
    if "mission_drones" in cache:
        if any(
            md.condition_after in (Condition.DAMAGED, Condition.LOST)
            for md in mission.mission_drones.all()
        ):
            return True
    elif mission.mission_drones.filter(
        condition_after__in=(Condition.DAMAGED, Condition.LOST)
    ).exists():
        return True

    if mission.writeoff_records.exists():
        return True

    return mission.drone_status_history_records.filter(
        Q(related_repair_order__isnull=False) | Q(related_writeoff__isnull=False)
    ).exists()


def can_user_view_mission(user, mission):
    """Return whether ``user`` may view ``mission`` under object-level rules.

    This complements RBAC ``missions.view`` with domain scoping:
    - admins/commanders/dispatchers may view any mission
    - operators may only view assigned missions
    - technicians may only view missions tied to repair or write-off workflow
    - viewers may only view missions belonging to their own unit
    """

    if not user or not getattr(user, "is_authenticated", False):
        return False

    role_code = get_user_role_code(user)
    if role_code in (ADMIN_CODE, COMMANDER_CODE, DISPATCHER_CODE):
        return True

    if role_code == OPERATOR_CODE:
        return _has_operator_in_mission(mission, user.id)

    if role_code == TECHNICIAN_CODE:
        return _is_repair_or_writeoff_related_mission(mission)

    if role_code == VIEWER_CODE:
        return user.unit_id is not None and user.unit_id == mission.unit_id

    return False


def restrict_missions_for_user(queryset, user):
    """Scope a mission queryset to what ``user`` is allowed to view.

    The helper is used both by mission read endpoints and by mission-derived
    resources such as artifacts and video metadata, so it must stay aligned
    with ``can_user_view_mission`` and fail closed for unsupported roles.
    """

    role_code = get_user_role_code(user)
    if role_code in (ADMIN_CODE, COMMANDER_CODE, DISPATCHER_CODE):
        return queryset
    if role_code == OPERATOR_CODE:
        return queryset.filter(mission_drones__operator_id=user.id).distinct()
    if role_code == TECHNICIAN_CODE:
        return queryset.filter(
            Q(
                mission_drones__condition_after__in=(
                    Condition.DAMAGED,
                    Condition.LOST,
                )
            )
            | Q(writeoff_records__isnull=False)
            | Q(drone_status_history_records__related_repair_order__isnull=False)
            | Q(drone_status_history_records__related_writeoff__isnull=False)
        ).distinct()
    if role_code == VIEWER_CODE:
        if user.unit_id is None:
            return queryset.none()
        return queryset.filter(unit_id=user.unit_id)
    return queryset.none()


class CanCreateMission(HasRBACPermission):
    """Check if the user's role can create missions."""

    required_permission = PERMISSION_MISSIONS_CREATE


class CanAssignMission(HasRBACPermission):
    """Check if the user's role can assign resources to missions."""

    required_permission = PERMISSION_MISSIONS_ASSIGN


class CanUpdateMissionStatus(HasRBACPermission):
    """Check if the user's role can update mission status."""

    required_permission = PERMISSION_MISSIONS_UPDATE_STATUS


class CanRecordOutcome(HasRBACPermission):
    """Check if the user's role can record mission outcomes."""

    required_permission = PERMISSION_MISSIONS_RECORD_OUTCOME


class CanRecordCondition(HasRBACPermission):
    """Check if the user's role can record drone condition results."""

    required_permission = PERMISSION_MISSIONS_RECORD_CONDITION


# ============ Object-Level Permissions ============
# Check contextual access to specific objects.


class IsDispatcherOrAssignedOperatorOrAdmin(permissions.BasePermission):
    """Admins act on any mission; operators only on missions they fly.

    Two-stage check: has_permission gates by role (cheap, no DB), then
    has_object_permission enforces ownership — an operator may only touch a
    mission/assignment they are personally assigned to. Used for recording
    outcomes and drone conditions.
    """

    message = (
        "Only a Dispatcher, the assigned Operator, or an Admin can perform "
        "this action."
    )

    def has_permission(self, request, view):
        """Allow the request to proceed to object checks for eligible roles."""
        if not request.user or not request.user.is_authenticated:
            return False
        return get_user_role_code(request.user) in (
            ADMIN_CODE,
            DISPATCHER_CODE,
            OPERATOR_CODE,
        )

    def has_object_permission(self, request, view, obj):
        """Grant Admins access; restrict Operators to their own assignments."""
        role_code = get_user_role_code(request.user)
        if role_code in (ADMIN_CODE, DISPATCHER_CODE):
            return True
        if role_code != OPERATOR_CODE:
            return False
        # Ownership check differs by object type. For a Mission, the operator
        # must be assigned to at least one of its drones; for a single
        # MissionDrone assignment, they must be its operator.
        if isinstance(obj, Mission):
            return _has_operator_in_mission(obj, request.user.id)
        if isinstance(obj, MissionDrone):
            return obj.operator_id == request.user.id
        return False


class IsAssignedToMissionOrAdmin(permissions.BasePermission):
    """Allow admins, commanders, dispatchers, or assigned operators to update."""

    message = "You are not authorized to update this mission's status."

    def has_object_permission(self, request, view, obj):
        """Check whether the user can update this specific mission."""
        role_code = get_user_role_code(request.user)
        if role_code in (ADMIN_CODE, COMMANDER_CODE, DISPATCHER_CODE):
            return True

        if role_code == OPERATOR_CODE:
            return _has_operator_in_mission(obj, request.user.id)

        return False
