import logging

from rest_framework.permissions import BasePermission

from roles.models import ADMIN_CODE

from .rbac import ROLE_PERMISSION_MATRIX

logger = logging.getLogger(__name__)


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


def log_permission_denied(request, permission_code, reason=None):
    user = getattr(request, "user", None)

    logger.warning(
        (
            "Permission denied: user_id=%s username=%s role=%s "
            "permission=%s path=%s method=%s reason=%s"
        ),
        getattr(user, "id", None),
        getattr(user, "username", None),
        get_user_role_code(user),
        permission_code,
        getattr(request, "path", None),
        getattr(request, "method", None),
        reason or "permission_check_failed",
    )


class IsSystemAdmin(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            log_permission_denied(
                request,
                ADMIN_CODE,
                reason="user_not_authenticated",
            )
            return False

        is_admin = get_user_role_code(request.user) == ADMIN_CODE
        if not is_admin:
            log_permission_denied(
                request,
                ADMIN_CODE,
                reason="admin_role_required",
            )

        return is_admin


class HasRBACPermission(BasePermission):
    message = "You do not have permission to perform this action."
    required_permission = None

    def has_permission(self, request, view):
        permission_code = self.required_permission or getattr(
            view, "required_permission", None
        )

        if not permission_code:
            log_permission_denied(
                request,
                permission_code,
                reason="required_permission_not_configured",
            )
            return False

        allowed = user_has_permission(request.user, permission_code)
        if not allowed:
            log_permission_denied(
                request,
                permission_code,
                reason="missing_required_permission",
            )

        return allowed


class HasAnyRBACPermission(BasePermission):
    message = "You do not have permission to perform this action."
    required_permissions = None

    def has_permission(self, request, view):
        permission_codes = self.required_permissions or getattr(
            view, "required_permissions", None
        )

        if not permission_codes:
            log_permission_denied(
                request,
                None,
                reason="required_permissions_not_configured",
            )
            return False

        for permission_code in permission_codes:
            if user_has_permission(request.user, permission_code):
                return True

        log_permission_denied(
            request,
            ",".join(permission_codes),
            reason="missing_all_required_permissions",
        )
        return False
