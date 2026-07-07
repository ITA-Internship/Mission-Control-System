from rest_framework import permissions

from accounts.permissions import HasRBACPermission, get_user_role_code
from accounts.rbac import PERMISSION_MISSIONS_VIEW
from roles.models import ADMIN_CODE, COMMANDER_CODE, DISPATCHER_CODE, OPERATOR_CODE

from .models import Mission, MissionDrone


class IsDispatcherOrAdmin(permissions.BasePermission):
    message = "Only Dispatcher or Admin users can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return get_user_role_code(request.user) in (DISPATCHER_CODE, ADMIN_CODE)


class CanViewMission(HasRBACPermission):
    required_permission = PERMISSION_MISSIONS_VIEW


class IsAssignedOperatorOrAdmin(permissions.BasePermission):
    message = "Only the assigned Operator or an Admin can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return get_user_role_code(request.user) in (ADMIN_CODE, OPERATOR_CODE)

    def has_object_permission(self, request, view, obj):
        role_code = get_user_role_code(request.user)
        if role_code == ADMIN_CODE:
            return True
        if role_code != OPERATOR_CODE:
            return False
        if isinstance(obj, Mission):
            return any(
                md.operator_id == request.user.id for md in obj.mission_drones.all()
            )
        if isinstance(obj, MissionDrone):
            return obj.operator_id == request.user.id
        return False


class CanUpdateMissionStatus(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
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
