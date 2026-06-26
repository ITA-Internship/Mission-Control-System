from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.permissions import user_has_permission
from accounts.rbac import PERMISSION_REPAIRS_CREATE, PERMISSION_REPAIRS_VIEW


class RepairPermission(BasePermission):
    message = "You do not have permission to perform this action."

    def _has_permission(self, user, permission_code):
        if not user or not user.is_authenticated:
            return False

        return user_has_permission(user, permission_code)

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return self._has_permission(request.user, PERMISSION_REPAIRS_VIEW)

        if request.method == "POST":
            return self._has_permission(request.user, PERMISSION_REPAIRS_CREATE)

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return self._has_permission(request.user, PERMISSION_REPAIRS_VIEW)

        return False
