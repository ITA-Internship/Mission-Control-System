from accounts.permissions import HasRBACPermission, get_user_role_code
from accounts.rbac import (
    PERMISSION_MEDIA_DELETE,
    PERMISSION_MEDIA_UPLOAD,
    PERMISSION_MEDIA_VIEW,
    PERMISSION_MEDIA_VIEW_LOGS,
)
from missions.permissions import can_user_view_mission
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


class MediaObjectPermission(MediaAuditedDenialMixin, HasRBACPermission):
    """Base for object-level media checks: records the denial and delegates the
    authorization rule to ``_check_object`` (implemented per subclass)."""

    def has_object_permission(self, request, view, obj):
        if self._check_object(request, obj):
            return True

        self._record_denied(request, reason="object_permission_denied", obj=obj)
        return False

    def _is_owner_or_admin(self, request, obj):
        if get_user_role_code(request.user) == ADMIN_CODE:
            return True

        return getattr(obj, "uploaded_by_id", None) == request.user.id

    def _check_object(self, request, obj):
        raise NotImplementedError


class MediaViewPermission(MediaObjectPermission):
    """Allow mission media reads for the uploader/admin or visible missions.

    Viewer access is not global: viewers may read mission-derived media only
    when the mission itself is visible under the shared mission scoping rules
    (currently same-unit visibility).
    """

    required_permission = PERMISSION_MEDIA_VIEW

    def _check_object(self, request, obj):
        if self._is_owner_or_admin(request, obj):
            return True

        mission = getattr(obj, "mission", None)
        if not mission:
            return False

        return can_user_view_mission(request.user, mission)


class MediaDeletePermission(MediaObjectPermission):
    required_permission = PERMISSION_MEDIA_DELETE

    def _check_object(self, request, obj):
        return self._is_owner_or_admin(request, obj)


class MediaViewLogsPermission(MediaAuditedDenialMixin, HasRBACPermission):
    required_permission = PERMISSION_MEDIA_VIEW_LOGS
