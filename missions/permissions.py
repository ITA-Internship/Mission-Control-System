from rest_framework import permissions

from roles.models import ADMIN_CODE


#? dispatcher is in the task specifications, so it'll be here till further clarifications
DISPATCHER_CODE = "DISPATCHER"


#again we will need smth like this function from accounts team
def _user_has_role(user, *codes):
    if not user or not getattr(user, 'is_authenticated', False):
        return False
    role = getattr(user, 'role', None)
    if role is not None and getattr(role, 'code', None) in codes:
        return True
    return False


class IsDispatcherOrAdmin(permissions.BasePermission):
    message = 'Only Dispatcher or Admin users can perform this action.'

    def has_permission(self, request):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return _user_has_role(request.user, DISPATCHER_CODE, ADMIN_CODE)
