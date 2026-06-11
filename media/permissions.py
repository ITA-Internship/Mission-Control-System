from accounts.permissions import HasRBACPermission
from accounts.rbac import (
    PERMISSION_MEDIA_DELETE,
    PERMISSION_MEDIA_UPLOAD,
    PERMISSION_MEDIA_VIEW,
)


class MediaUploadPermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_UPLOAD


class MediaViewPermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_VIEW


class MediaDeletePermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_DELETE
