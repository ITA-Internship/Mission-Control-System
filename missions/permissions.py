from rest_framework import permissions

from accounts.permissions import get_user_role_code
from roles.models import ADMIN_CODE, COMMANDER_CODE, DISPATCHER_CODE, OPERATOR_CODE


class IsDispatcherOrAdmin(permissions.BasePermission):
    message = "Only Dispatcher or Admin users can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return get_user_role_code(request.user) in (DISPATCHER_CODE, ADMIN_CODE)


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
        mission_drones = getattr(obj, "mission_drones", None)
        if mission_drones is not None and hasattr(mission_drones, "filter"):
            return mission_drones.filter(operator=request.user).exists()
        return getattr(obj, "operator_id", None) == request.user.id


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
            is_assigned = obj.mission_drones.filter(operator=request.user).exists()

            return is_assigned

        return False
