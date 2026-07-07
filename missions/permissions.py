"""DRF permission classes for the missions app."""

from rest_framework import permissions

from accounts.permissions import HasRBACPermission, get_user_role_code
from accounts.rbac import PERMISSION_MISSIONS_VIEW
from roles.models import ADMIN_CODE, COMMANDER_CODE, DISPATCHER_CODE, OPERATOR_CODE

from .models import Mission, MissionDrone


class IsDispatcherOrAdmin(permissions.BasePermission):
    """Allow reads to any authenticated user; writes to Dispatcher or Admin."""

    message = "Only Dispatcher or Admin users can perform this action."

    def has_permission(self, request, view):
        """Allow safe methods for all; restrict writes to Dispatcher/Admin."""
        if not request.user or not request.user.is_authenticated:
            return False
        # Reads are open to any authenticated user; only writes (creating
        # missions / managing assignments) are gated to Dispatcher and Admin.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return get_user_role_code(request.user) in (DISPATCHER_CODE, ADMIN_CODE)


class CanViewMission(HasRBACPermission):
    required_permission = PERMISSION_MISSIONS_VIEW


class IsAssignedOperatorOrAdmin(permissions.BasePermission):
    """Admins act on any mission; operators only on missions they fly.

    Two-stage check: has_permission gates by role (cheap, no DB), then
    has_object_permission enforces ownership — an operator may only touch a
    mission/assignment they are personally assigned to. Used for recording
    outcomes and drone conditions.
    """

    message = "Only the assigned Operator or an Admin can perform this action."

    def has_permission(self, request, view):
        """Gate by role: only Admins and Operators may proceed."""
        if not request.user or not request.user.is_authenticated:
            return False
        return get_user_role_code(request.user) in (ADMIN_CODE, OPERATOR_CODE)

    def has_object_permission(self, request, view, obj):
        """Grant Admins access; restrict Operators to their own assignments."""
        role_code = get_user_role_code(request.user)
        if role_code == ADMIN_CODE:
            return True
        if role_code != OPERATOR_CODE:
            return False
        # Ownership check differs by object type. For a Mission, the operator
        # must be assigned to at least one of its drones; for a single
        # MissionDrone assignment, they must be its operator.
        if isinstance(obj, Mission):
            return any(
                md.operator_id == request.user.id for md in obj.mission_drones.all()
            )
        if isinstance(obj, MissionDrone):
            return obj.operator_id == request.user.id
        return False


class CanUpdateMissionStatus(permissions.BasePermission):
    """Who may drive a mission through its lifecycle.

    Admins and Commanders can change any mission's status; an Operator can only
    change status on a mission they are assigned to.
    """

    def has_object_permission(self, request, view, obj):
        """Allow Admins/Commanders any mission; Operators only their own."""
        if (
            not request.user
            or not request.user.is_authenticated
            or not request.user.role
        ):
            return False

        user_role = get_user_role_code(request.user)

        if user_role in [ADMIN_CODE, COMMANDER_CODE]:
            return True

        if user_role == OPERATOR_CODE:
            return any(
                md.operator_id == request.user.id for md in obj.mission_drones.all()
            )

        return False
