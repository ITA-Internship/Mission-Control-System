from accounts.permissions import HasRBACPermission, get_user_role_code
from accounts.rbac import (
    PERMISSION_MEDIA_DELETE,
    PERMISSION_MEDIA_UPLOAD,
    PERMISSION_MEDIA_VIEW,
    PERMISSION_MEDIA_VIEW_LOGS,
)
from roles.models import ADMIN_CODE

from .services import record_permission_denied


class MediaAuditedDenialMixin:
    """Record a MediaAuditLog entry whenever an RBAC check denies access.

    Wraps the RBAC ``has_permission`` result; object-level checks call
    ``_record_denied`` directly since their logic lives in each subclass.
    """

    def _record_denied(self, request, reason, obj=None):
        record_permission_denied(
            user=getattr(request, "user", None),
            request=request,
            permission_code=self.required_permission,
            reason=reason,
            obj=obj,
        )

    def has_permission(self, request, view):
        allowed = super().has_permission(request, view)
        if not allowed:
            self._record_denied(request, reason="missing_required_permission")
        return allowed


class MediaUploadPermission(MediaAuditedDenialMixin, HasRBACPermission):
    required_permission = PERMISSION_MEDIA_UPLOAD


class MediaViewPermission(MediaAuditedDenialMixin, HasRBACPermission):
    required_permission = PERMISSION_MEDIA_VIEW

    def has_object_permission(self, request, view, obj):
        if self._check_object(request, obj):
            return True

        self._record_denied(request, reason="object_permission_denied", obj=obj)
        return False

    def _check_object(self, request, obj):
        if get_user_role_code(request.user) == ADMIN_CODE:
            return True

        if getattr(obj, "uploaded_by_id", None) == request.user.id:
            return True

        mission = getattr(obj, "mission", None)
        if mission and getattr(mission, "unit_id", None) == request.user.unit_id:
            return True

        return False


class MediaDeletePermission(MediaAuditedDenialMixin, HasRBACPermission):
    required_permission = PERMISSION_MEDIA_DELETE

    def has_object_permission(self, request, view, obj):
        if self._check_object(request, obj):
            return True

        self._record_denied(request, reason="object_permission_denied", obj=obj)
        return False

    def _check_object(self, request, obj):
        if get_user_role_code(request.user) == ADMIN_CODE:
            return True

        if getattr(obj, "uploaded_by_id", None) == request.user.id:
            return True

        return False


class MediaViewLogsPermission(MediaAuditedDenialMixin, HasRBACPermission):
    required_permission = PERMISSION_MEDIA_VIEW_LOGS
