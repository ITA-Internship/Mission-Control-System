from django_filters import rest_framework as filters
from rest_framework import generics, permissions, status, viewsets
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from common.pagination import StandardResultsSetPagination
from missions.models import Mission

from .models import MediaAuditLog, MissionArtifact
from .permissions import (
    MediaDeletePermission,
    MediaUploadPermission,
    MediaViewLogsPermission,
    MediaViewPermission,
)
from .serializers import (
    MediaAuditLogSerializer,
    MissionArtifactSerializer,
    MissionArtifactUploadSerializer,
)
from .services import delete_artifact, record_artifact_view, upload_artifact


class _MissionArtifactMixin:

    def get_mission(self):
        if not hasattr(self, "_mission"):
            self._mission = generics.get_object_or_404(
                Mission, id=self.kwargs["mission_pk"]
            )
        return self._mission


class ArtifactListCreateView(_MissionArtifactMixin, generics.ListCreateAPIView):

    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), MediaViewPermission()]
        return [permissions.IsAuthenticated(), MediaUploadPermission()]

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return MissionArtifactSerializer
        return MissionArtifactUploadSerializer

    def get_queryset(self):
        mission = self.get_mission()
        return MissionArtifact.objects.filter(mission=mission).select_related(
            "uploaded_by"
        )

    def create(self, request, *args, **kwargs):
        mission = self.get_mission()

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        artifact = upload_artifact(
            mission=mission,
            file=serializer.validated_data["file"],
            title=serializer.validated_data["title"],
            uploaded_by=request.user,
            description=serializer.validated_data.get("description"),
            captured_at=serializer.validated_data.get("captured_at"),
            request=request,
        )

        response_serializer = MissionArtifactSerializer(artifact)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


class ArtifactDetailView(_MissionArtifactMixin, generics.RetrieveDestroyAPIView):

    serializer_class = MissionArtifactSerializer
    lookup_url_kwarg = "artifact_pk"

    def get_permissions(self):
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), MediaViewPermission()]
        return [permissions.IsAuthenticated(), MediaDeletePermission()]

    def get_queryset(self):
        mission = self.get_mission()
        return MissionArtifact.objects.filter(mission=mission).select_related(
            "uploaded_by"
        )

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        record_artifact_view(
            user=request.user,
            artifact=instance,
            request=request,
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        delete_artifact(
            artifact=instance,
            action_user=self.request.user,
            request=self.request,
        )


class MediaAuditLogFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = MediaAuditLog
        fields = ["action", "user", "mission", "artifact"]


class MediaAuditLogViewSet(viewsets.ReadOnlyModelViewSet):

    serializer_class = MediaAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, MediaViewLogsPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = MediaAuditLogFilter
    queryset = MediaAuditLog.objects.select_related(
        "artifact", "mission", "user"
    ).all()
