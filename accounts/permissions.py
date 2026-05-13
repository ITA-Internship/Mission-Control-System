from rest_framework.permissions import BasePermission

from .rbac import ROLE_PERMISSION_MATRIX
from roles.models import ADMIN_CODE


def get_user_role_code(user):
    role = getattr(user, "role", None)
    return getattr(role, "code", None)


def user_has_permission(user, permission_code):
    if not user or not user.is_authenticated:
        return False

    role_code = get_user_role_code(user)
    if not role_code:
        return False

    allowed_permissions = ROLE_PERMISSION_MATRIX.get(role_code, set())
    return permission_code in allowed_permissions


class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        return get_user_role_code(request.user) == ADMIN_CODE


class HasRBACPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        permission_code = self.required_permission or getattr(
            view, "required_permission", None
        )

        if not permission_code:
            return False

        return user_has_permission(request.user, permission_code)
