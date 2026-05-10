from rest_framework.permissions import BasePermission
from roles.models import ADMIN_CODE

class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        role = getattr(request.user, 'role', None)

        return bool(role and role.code == ADMIN_CODE)
