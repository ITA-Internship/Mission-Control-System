from accounts.permissions import HasRBACPermission, get_user_role_code
from accounts.rbac import (
    PERMISSION_MEDIA_DELETE,
    PERMISSION_MEDIA_UPLOAD,
    PERMISSION_MEDIA_VIEW,
    PERMISSION_MEDIA_VIEW_LOGS,
)
from missions.models import MissionDrone
from roles.models import ADMIN_CODE


class MediaUploadPermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_UPLOAD


class MediaViewPermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_VIEW

    def has_object_permission(self, request, view, obj):
        role_code = get_user_role_code(request.user)
        if role_code == ADMIN_CODE:
            return True

        if getattr(obj, "uploaded_by_id", None) == request.user.id:
            return True

        mission = getattr(obj, "mission", None)
        if not mission:
            return False

        if mission.commander_id == request.user.id:
            return True

        if mission.created_by_id == request.user.id:
            return True

        if MissionDrone.objects.filter(
            mission_id=mission.id,
            operator_id=request.user.id,
        ).exists():
            return True

        return False


class MediaDeletePermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_DELETE

    def has_object_permission(self, request, view, obj):
        if get_user_role_code(request.user) == ADMIN_CODE:
            return True

        if getattr(obj, "uploaded_by_id", None) == request.user.id:
            return True

        return False


class MediaViewLogsPermission(HasRBACPermission):
    required_permission = PERMISSION_MEDIA_VIEW_LOGS
