from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.permissions import user_has_permission
from accounts.rbac import (
    PERMISSION_DRONES_CREATE,
    PERMISSION_DRONES_DECOMMISSION,
    PERMISSION_DRONES_UPDATE,
    PERMISSION_DRONES_VIEW,
    PERMISSION_WRITEOFF_CREATE,
    PERMISSION_WRITEOFF_VIEW,
)

from .models import Drone


class DronePermission(BasePermission):
    message = "You do not have permission to perform this action."

    def _has_permission(self, user, permission_code):
        if not user or not user.is_authenticated:
            return False

        return user_has_permission(user, permission_code)

    def _get_requested_status(self, request):
        requested_status = request.data.get("status")

        if isinstance(requested_status, str):
            return requested_status.upper()

        return requested_status

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return self._has_permission(request.user, PERMISSION_DRONES_VIEW)

        if request.method == "POST":
            return self._has_permission(request.user, PERMISSION_DRONES_CREATE)

        if request.method == "PATCH":
            return self._has_permission(request.user, PERMISSION_DRONES_UPDATE)

        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return self._has_permission(request.user, PERMISSION_DRONES_VIEW)

        if request.method == "PATCH":
            has_update_permission = self._has_permission(
                request.user,
                PERMISSION_DRONES_UPDATE,
            )

            if not has_update_permission:
                return False

            requested_status = self._get_requested_status(request)

            current_status_is_inactive = obj.status in Drone.INACTIVE_STATUSES
            requested_status_is_inactive = requested_status in Drone.INACTIVE_STATUSES

            if current_status_is_inactive or requested_status_is_inactive:
                return self._has_permission(
                    request.user,
                    PERMISSION_DRONES_DECOMMISSION,
                )

            return True

        return False


class WriteOffHistoryPermission(BasePermission):
    message = "You do not have permission to view write-off history."

    def _has_permission(self, user):
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "is_staff", False):
            return True

        return user_has_permission(user, PERMISSION_WRITEOFF_VIEW)

    def has_permission(self, request, view):
        if request.method not in SAFE_METHODS:
            return False

        return self._has_permission(request.user)


class WriteOffPermission(BasePermission):
    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return user_has_permission(request.user, PERMISSION_WRITEOFF_VIEW)

        if request.method == "POST":
            return user_has_permission(request.user, PERMISSION_WRITEOFF_CREATE)

        return False
