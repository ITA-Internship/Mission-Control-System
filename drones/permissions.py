from rest_framework.permissions import BasePermission, SAFE_METHODS

from accounts.permissions import user_has_permission
from accounts.rbac import (
    PERMISSION_DRONES_CREATE,
    PERMISSION_DRONES_DECOMMISSION,
    PERMISSION_DRONES_UPDATE,
    PERMISSION_DRONES_VIEW,
)

from .models import Drone


class DronePermission(BasePermission):
    message = "You do not have permission to perform this action."

    def _has_permission(self, user, permission_code):
        if not user or not user.is_authenticated:
            return False

        if getattr(user, "is_staff", False):
            return True

        return user_has_permission(user, permission_code)

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return self._has_permission(request.user, PERMISSION_DRONES_VIEW)

        if request.method == "POST":
            return self._has_permission(request.user, PERMISSION_DRONES_CREATE)

        if request.method == "PATCH":
            requested_status = request.data.get("status")

            if requested_status in Drone.INACTIVE_STATUSES:
                return (
                    self._has_permission(request.user, PERMISSION_DRONES_UPDATE)
                    and self._has_permission(
                        request.user,
                        PERMISSION_DRONES_DECOMMISSION,
                    )
                )

            return self._has_permission(request.user, PERMISSION_DRONES_UPDATE)

        return False