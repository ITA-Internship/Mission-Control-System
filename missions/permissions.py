from rest_framework import permissions

from roles.models import ADMIN_CODE, DISPATCHER_CODE


class IsDispatcherOrAdmin(permissions.BasePermission):
    message = "Only Dispatcher or Admin users can perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        role = getattr(request.user, "role", None)
        if role is not None and getattr(role, "code", None) in [
            DISPATCHER_CODE,
            ADMIN_CODE,
        ]:
            return True
        return False
    
class CanUpdateMissionStatus(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated or not request.user.role:
            return False

        role_name = request.user.role.name.upper()

        if role_name in ['ADMIN', 'COMMANDER']:
            return True

        if role_name == 'OPERATOR':
            is_assigned = obj.mission_drones.filter(operator=request.user).exists()
            
            return is_assigned

        return False