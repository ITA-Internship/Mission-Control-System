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
from roles.models import ADMIN_CODE, COMMANDER_CODE, DISPATCHER_CODE, OPERATOR_CODE

from .models import Mission, MissionDrone


# ============ RBAC-based Permissions ============
# Use centralized RBAC matrix for role checks.


class CanViewMission(HasRBACPermission):
    """Check if the user's role can view missions."""

    required_permission = PERMISSION_MISSIONS_VIEW


def _has_operator_in_mission(obj, user_id):
    cache = getattr(obj, "_prefetched_objects_cache", {})
    if "mission_drones" in cache:
        return any(md.operator_id == user_id for md in obj.mission_drones.all())
    return obj.mission_drones.filter(operator_id=user_id).exists()


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


class IsAssignedOperatorOrAdmin(permissions.BasePermission):
    """
    Allow dispatchers, assigned operators, or admins to access a mission object.

    Use together with an RBAC permission class for full authorization.
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
        """Check whether the user is assigned to the specific mission object."""
        role_code = get_user_role_code(request.user)
        if role_code in (ADMIN_CODE, DISPATCHER_CODE):
            return True
        if role_code != OPERATOR_CODE:
            return False
        if isinstance(obj, Mission):
            return _has_operator_in_mission(obj, request.user.id)
        if isinstance(obj, MissionDrone):
            return obj.operator_id == request.user.id
        return False


class IsAssignedToMissionOrAdmin(permissions.BasePermission):
    """Allow admins, commanders, dispatchers, or assigned operators to update."""

    message = "You are not authorized to update this mission's status."

    def has_permission(self, request, view):
        """Allow eligible roles to proceed to mission-specific object checks."""
        if not request.user or not request.user.is_authenticated:
            return False
        return get_user_role_code(request.user) in (
            ADMIN_CODE,
            COMMANDER_CODE,
            DISPATCHER_CODE,
            OPERATOR_CODE,
        )

    def has_object_permission(self, request, view, obj):
        """Check whether the user can update this specific mission."""
        role_code = get_user_role_code(request.user)
        if role_code in (ADMIN_CODE, COMMANDER_CODE, DISPATCHER_CODE):
            return True

        if role_code == OPERATOR_CODE:
            return _has_operator_in_mission(obj, request.user.id)

        return False
