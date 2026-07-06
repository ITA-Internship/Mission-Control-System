from drf_spectacular.utils import extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from common.pagination import StandardResultsSetPagination
from missions.models import Mission

from .api_details import (
    artifact_detail_delete_schema,
    artifact_detail_get_schema,
    artifact_get_schema,
    artifact_post_schema,
)
from .models import MissionArtifact
from .permissions import (
    MediaDeletePermission,
    MediaUploadPermission,
    MediaViewPermission,
)
from .serializers import MissionArtifactSerializer, MissionArtifactUploadSerializer
from .services import delete_artifact, upload_artifact


class _MissionArtifactMixin:

    def get_mission(self):
        if not hasattr(self, "_mission"):
            self._mission = generics.get_object_or_404(
                Mission, id=self.kwargs["mission_pk"]
            )
        return self._mission


@extend_schema_view(get=artifact_get_schema, post=artifact_post_schema)
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
        )

        response_serializer = MissionArtifactSerializer(artifact)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED,
        )


@extend_schema_view(
    get=artifact_detail_get_schema, delete=artifact_detail_delete_schema
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

    def perform_destroy(self, instance):
        delete_artifact(
            artifact=instance,
            action_user=self.request.user,
        )
