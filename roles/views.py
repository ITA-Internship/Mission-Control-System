"""Expose read-only role catalog endpoints.

Classes:
    RoleListView: Lists roles for filters and selection controls.
"""

from rest_framework import generics

from accounts.permissions import HasRBACPermission
from accounts.rbac import PERMISSION_ROLES_VIEW

from .api_details import role_list_schema
from .models import Role
from .serializers import RoleSerializer


@role_list_schema
class RoleListView(generics.ListAPIView):
    """List all roles for role filters and selection controls."""

    serializer_class = RoleSerializer
    permission_classes = [HasRBACPermission]
    required_permission = PERMISSION_ROLES_VIEW
    pagination_class = None
    queryset = Role.objects.all().order_by("name")
