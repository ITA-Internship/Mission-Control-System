"""Permission classes for the media app.

Authorization model

Artifact endpoints are protected by **two complementary layers**:

1. **Queryset scoping** (authoritative for mission access):
   ``restrict_missions_for_user`` is applied unconditionally in
   ``_MissionArtifactMixin.get_mission`` and ``ArtifactListCreateView.get_queryset``.
   It is the single source of truth for mission reachability: operators see
   only assigned missions, viewers see only their unit's missions, technicians
   see only repair/write-off missions, and admin/commander/dispatcher roles
   see all missions.

2. **Object-level RBAC** (authoritative for artifact-level actions):
   ``MediaViewPermission`` / ``MediaDeletePermission`` decide what a user can
   do with an artifact *inside* an already-authorized mission.
   ``_check_object`` checks ownership (``uploaded_by``), admin role, or
   matching ``unit_id`` for view access.

Layer 1 runs first (via ``get_mission`` / ``get_queryset`` → 404 if denied).
Layer 2 runs second (via ``check_object_permissions`` → 403 if denied). Any change to
``restrict_missions_for_user`` automatically propagates to all media
endpoints; object-level rules can be tightened independently without
affecting mission scoping.
"""

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
    """Require the media upload RBAC permission."""

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
    """Require the media delete RBAC and object-level permissions.

    Access is granted if the user is an owner or admin."""

    required_permission = PERMISSION_MEDIA_DELETE

    def _check_object(self, request, obj):
        return self._is_owner_or_admin(request, obj)


class MediaViewLogsPermission(MediaAuditedDenialMixin, HasRBACPermission):
    """Require the media audit log view RBAC permission."""

    required_permission = PERMISSION_MEDIA_VIEW_LOGS
