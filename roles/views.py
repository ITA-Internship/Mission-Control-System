from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, serializers

from common.pagination import StandardResultsSetPagination

from .models import Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "code", "name", "description"]


@extend_schema(summary="List roles", description="List all system roles.")
class RoleListView(generics.ListAPIView):
    queryset = Role.objects.all().order_by("id")
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
