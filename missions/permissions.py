from rest_framework import permissions

from roles.models import ADMIN_CODE, DISPATCHER_CODE


class IsDispatcherOrAdmin(permissions.BasePermission):
    message = 'Only Dispatcher or Admin users can perform this action.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        role = getattr(request.user, 'role', None)
        if role is not None and getattr(role, 'code', None) in [DISPATCHER_CODE, ADMIN_CODE]:
            return True
        return False
