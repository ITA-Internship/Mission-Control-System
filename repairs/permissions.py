"""Role-based access control (RBAC) permissions for the repairs API.

Maps HTTP methods and specific view actions to the underlying domain
permissions (view, create, manage, export) defined in the accounts app.
"""

from rest_framework.permissions import SAFE_METHODS, BasePermission

from accounts.permissions import user_has_permission
from accounts.rbac import (
    PERMISSION_REPAIRS_CREATE,
    PERMISSION_REPAIRS_EXPORT,
    PERMISSION_REPAIRS_MANAGE,
    PERMISSION_REPAIRS_VIEW,
)


class RepairPermission(BasePermission):
    """General access control for defect reports and component replacements.

    Grants access based on the HTTP method:
    - GET/HEAD/OPTIONS (SAFE_METHODS): Requires PERMISSION_REPAIRS_VIEW.
    - POST: Requires PERMISSION_REPAIRS_CREATE.
    - PATCH: Requires PERMISSION_REPAIRS_MANAGE.
    """

    message = "You do not have permission to perform this action."

    def _has_permission(self, user, permission_code):
        """Evaluate if an authenticated user holds a specific permission code."""
        if not user or not user.is_authenticated:
            return False

        return user_has_permission(user, permission_code)

    def has_permission(self, request, view):
        """Route list and creation requests to the appropriate RBAC checks."""
        if request.method in SAFE_METHODS:
            return self._has_permission(request.user, PERMISSION_REPAIRS_VIEW)

        if request.method == "POST":
            return self._has_permission(request.user, PERMISSION_REPAIRS_CREATE)

        if request.method == "PATCH":
            return self._has_permission(request.user, PERMISSION_REPAIRS_MANAGE)

        return False

    def has_object_permission(self, request, view, obj):
        """Route object-level retrieval and update requests to RBAC checks."""
        if request.method in SAFE_METHODS:
            return self._has_permission(request.user, PERMISSION_REPAIRS_VIEW)

        if request.method == "PATCH":
            return self._has_permission(request.user, PERMISSION_REPAIRS_MANAGE)

        return False


class RepairManagePermission(BasePermission):
    """Access control for managing repair orders and their state transitions.

    - SAFE_METHODS require PERMISSION_REPAIRS_VIEW.
    - All mutation methods require PERMISSION_REPAIRS_MANAGE.
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        """Evaluate access based on the HTTP method and assigned RBAC codes."""
        if not request.user or not request.user.is_authenticated:
            return False

        if request.method in SAFE_METHODS:
            return user_has_permission(request.user, PERMISSION_REPAIRS_VIEW)

        return user_has_permission(request.user, PERMISSION_REPAIRS_MANAGE)


class RepairHistoryExportPermission(BasePermission):
    """Access control for streaming CSV exports of repair history.

    Access is granted only to users with the dedicated
    PERMISSION_REPAIRS_EXPORT permission.
    """

    message = "You do not have permission to export repair history."

    def has_permission(self, request, view):
        """Evaluate export access using authentication and RBAC codes only."""
        if not request.user or not request.user.is_authenticated:
            return False

        return user_has_permission(request.user, PERMISSION_REPAIRS_EXPORT)
