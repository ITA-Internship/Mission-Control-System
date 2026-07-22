"""Role-based access control (RBAC) permissions for the media API."""

from accounts.permissions import HasRBACPermission, get_user_role_code
from accounts.rbac import (
    PERMISSION_MEDIA_DELETE,
    PERMISSION_MEDIA_UPLOAD,
    PERMISSION_MEDIA_VIEW,
    PERMISSION_MEDIA_VIEW_LOGS,
)
from roles.models import ADMIN_CODE


class MediaUploadPermission(HasRBACPermission):
    """Require the media upload RBAC permission."""

    required_permission = PERMISSION_MEDIA_UPLOAD


class MediaViewPermission(HasRBACPermission):
    """Require the media view RBAC permission."""

    required_permission = PERMISSION_MEDIA_VIEW

    def has_object_permission(self, request, view, obj):
        """Verify if the user has permission to view the specific media artifact."""
        if get_user_role_code(request.user) == ADMIN_CODE:
            return True

        if getattr(obj, "uploaded_by_id", None) == request.user.id:
            return True

        mission = getattr(obj, "mission", None)
        if mission and getattr(mission, "unit_id", None) == request.user.unit_id:
            return True

        return False


class MediaDeletePermission(HasRBACPermission):
    """Require the media delete RBAC permission."""

    required_permission = PERMISSION_MEDIA_DELETE

    def has_object_permission(self, request, view, obj):
        """Verify if the user has permission to delete the specific media artifact."""
        if get_user_role_code(request.user) == ADMIN_CODE:
            return True

        if getattr(obj, "uploaded_by_id", None) == request.user.id:
            return True

        return False


class MediaViewLogsPermission(HasRBACPermission):
    """Require the media audit log view RBAC permission."""

    required_permission = PERMISSION_MEDIA_VIEW_LOGS
