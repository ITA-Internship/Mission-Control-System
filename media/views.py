import logging
import mimetypes
import os
import posixpath

from django.conf import settings
from django.db import transaction
from django.db.models import ProtectedError
from django.http import FileResponse, Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from django.utils.encoding import escape_uri_path
from django.views.generic import TemplateView
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema_view
from rest_framework import generics, parsers, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from common.pagination import StandardResultsSetPagination
from missions.models import Mission

from .api_details import (
    artifact_detail_delete_schema,
    artifact_detail_get_schema,
    artifact_get_schema,
    artifact_post_schema,
    media_audit_log_list_schema,
    media_audit_log_retrieve_schema,
    protected_media_get_schema,
    video_metadata_create_schema,
    video_metadata_destroy_schema,
    video_metadata_list_schema,
    video_metadata_partial_update_schema,
    video_metadata_retrieve_schema,
    video_metadata_update_schema,
)
from .models import MediaAuditLog, MissionArtifact, VideoMetadata
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
    VideoMetadataSerializer,
    VideoUploadSerializer,
)
from .services import delete_artifact, record_artifact_view, upload_artifact
from .tasks import extract_video_duration_task

logger = logging.getLogger(__name__)


def filter_video_metadata_queryset(params, queryset=None):
    qs = (
        queryset
        or VideoMetadata.objects.select_related("mission", "drone", "uploader").all()
    )

    for param_names, field in (
        (("mission_id", "mission"), "mission_id"),
        (("drone_id", "drone"), "drone_id"),
        (("uploader_id", "uploader"), "uploader_id"),
    ):
        value = None
        for param in param_names:
            value = params.get(param)
            if value is not None:
                break
        if value:
            if not value.isdigit():
                raise ValidationError({param_names[0]: "Must be an integer."})
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
            request=request,
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


@extend_schema_view(get=protected_media_get_schema)
class ProtectedMediaView(APIView):
    permission_classes = [IsAuthenticated, MediaViewPermission]

    def get(self, request, artifact_pk):
        artifact = get_object_or_404(MissionArtifact, pk=artifact_pk)

        self.check_object_permissions(request, artifact)

        file_field = artifact.file

        if not file_field or not file_field.storage.exists(file_field.name):
            raise Http404("File not found on server.")

        content_type, _ = mimetypes.guess_type(file_field.name)
        content_type = content_type or "application/octet-stream"
        filename = artifact.original_filename or os.path.basename(file_field.name)

        if settings.DEBUG:
            return FileResponse(
                file_field,
                content_type=content_type,
                as_attachment=True,
                filename=filename,
            )
        else:
            response = HttpResponse(content_type=content_type)

            safe_name = posixpath.normpath(file_field.name)
            if safe_name.startswith("..") or safe_name.startswith("/"):
                raise Http404("Invalid file path.")

            internal_path = f"/internal-media/{safe_name}"
            response["X-Accel-Redirect"] = internal_path

            escaped_filename = escape_uri_path(filename)
            response["Content-Disposition"] = (
                f"attachment; filename*=UTF-8''{escaped_filename}"
            )

            return response


class MediaAuditLogFilter(filters.FilterSet):
    start_date = filters.DateTimeFilter(field_name="created_at", lookup_expr="gte")
    end_date = filters.DateTimeFilter(field_name="created_at", lookup_expr="lte")

    class Meta:
        model = MediaAuditLog
        fields = ["action", "user", "mission", "artifact"]


@extend_schema_view(
    list=media_audit_log_list_schema,
    retrieve=media_audit_log_retrieve_schema,
)
class MediaAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MediaAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, MediaViewLogsPermission]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.DjangoFilterBackend]
    filterset_class = MediaAuditLogFilter
    queryset = MediaAuditLog.objects.select_related("artifact", "mission", "user").all()


@extend_schema_view(
    list=video_metadata_list_schema,
    create=video_metadata_create_schema,
    retrieve=video_metadata_retrieve_schema,
    update=video_metadata_update_schema,
    partial_update=video_metadata_partial_update_schema,
    destroy=video_metadata_destroy_schema,
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
        return filter_video_metadata_queryset(
            self.request.query_params,
            queryset=super().get_queryset(),
        )

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
        instance = serializer.save(
            uploader=self.request.user,
            status=VideoMetadata.Status.UPLOADING,
        )

        try:
            extract_video_duration_task.delay(instance.id)
        except Exception:
            logger.exception(
                "Failed to enqueue video duration extraction task for video %s",
                instance.id,
            )

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


class VideoMetadataBrowserView(TemplateView):
    template_name = "media/video_browser.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user or not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication required.")

        permission_validator = MediaViewPermission()
        if not permission_validator.has_permission(request, self):
            return HttpResponseForbidden(
                "You do not have permission to access video records."
            )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["mission_id"] = self.request.GET.get("mission_id", "")
        context["drone_id"] = self.request.GET.get("drone_id", "")
        context["videos"] = []
        context["error"] = None

        if not self.request.GET:
            return context

        try:
            context["videos"] = filter_video_metadata_queryset(
                self.request.GET
            ).order_by("-created_at")
        except ValidationError as exc:
            if isinstance(exc.detail, dict):
                context["error"] = " ".join(
                    f"{field}: {' '.join(map(str, messages))}"
                    for field, messages in exc.detail.items()
                )
            else:
                context["error"] = str(exc.detail)

        return context
