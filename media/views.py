from django.db import transaction
from django.db.models import ProtectedError
from django.utils.dateparse import parse_date
from rest_framework import generics, parsers, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.pagination import StandardResultsSetPagination
from missions.models import Mission

from .models import MissionArtifact, VideoMetadata
from .permissions import (
    MediaDeletePermission,
    MediaUploadPermission,
    MediaViewPermission,
)
from .serializers import (
    MissionArtifactSerializer,
    MissionArtifactUploadSerializer,
    VideoMetadataSerializer,
    VideoUploadSerializer,
)
from .services import delete_artifact, upload_artifact


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

    def perform_destroy(self, instance):
        delete_artifact(
            artifact=instance,
            action_user=self.request.user,
        )


class VideoMetadataViewSet(viewsets.ModelViewSet):
    queryset = VideoMetadata.objects.select_related(
        "mission", "drone", "uploader"
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "create":
            return VideoUploadSerializer
        return VideoMetadataSerializer

    def get_queryset(self):
        qs = VideoMetadata.objects.select_related("mission", "drone", "uploader").all()

        params = self.request.query_params

        for param, field in (
            ("mission", "mission_id"),
            ("drone", "drone_id"),
            ("uploader", "uploader_id"),
        ):
            value = params.get(param)
            if value:
                if not value.isdigit():
                    raise ValidationError({param: "Must be an integer."})
                qs = qs.filter(**{field: int(value)})

        status_value = params.get("status")
        if status_value:
            if status_value not in VideoMetadata.Status.values:
                raise ValidationError(
                    {"status": f"Must be one of {VideoMetadata.Status.values}."}
                )
            qs = qs.filter(status=status_value)

        for date_param, lookup in (
            ("created_after", "created_at__date__gte"),
            ("created_before", "created_at__date__lte"),
            ("recorded_after", "recorded_at__date__gte"),
            ("recorded_before", "recorded_at__date__lte"),
        ):
            raw_value = params.get(date_param)
            if raw_value:
                parsed = parse_date(raw_value)
                if parsed is None:
                    raise ValidationError({date_param: "Expected format YYYY-MM-DD."})
                qs = qs.filter(**{lookup: parsed})

        return qs

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            permission_classes = [IsAuthenticated, MediaViewPermission]
        elif self.action == "create":
            permission_classes = [IsAuthenticated, MediaUploadPermission]
        elif self.action in ["destroy", "update", "partial_update"]:
            permission_classes = [IsAuthenticated, MediaDeletePermission]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        with transaction.atomic():
            serializer.save()

    def perform_destroy(self, instance):
        try:
            with transaction.atomic():
                instance.delete()
        except ProtectedError:
            raise ValidationError(
                {
                    "detail": "Cannot delete this record because "
                    "it is protected by dependencies."
                }
            )
