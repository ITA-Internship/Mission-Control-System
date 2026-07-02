from accounts.permissions import HasRBACPermission, get_user_role_code
from accounts.rbac import (
    PERMISSION_MEDIA_DELETE,
    PERMISSION_MEDIA_UPLOAD,
    PERMISSION_MEDIA_VIEW,
    PERMISSION_MEDIA_VIEW_LOGS,
)
from roles.models import ADMIN_CODE


class MediaUploadPermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_UPLOAD


class MediaViewPermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_VIEW

    def has_object_permission(self, request, view, obj):
        if get_user_role_code(request.user) == ADMIN_CODE:
            return True

        if getattr(obj, "uploaded_by", None) == request.user:
            return True

        if (
            hasattr(obj, "mission")
            and hasattr(obj.mission, "unit")
            and obj.mission.unit == request.user.unit
        ):
            return True

        return False


class MediaDeletePermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_DELETE

    def has_object_permission(self, request, view, obj):
        if get_user_role_code(request.user) == ADMIN_CODE:
            return True

        if getattr(obj, "uploaded_by", None) == request.user:
            return True

        return False


class MediaViewLogsPermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_VIEW_LOGS
