"""API and HTML Views for media app.

Provides endpoints for creating and managing mission artifacts,
listing audit logs."""

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
from missions.permissions import restrict_missions_for_user

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
from .services import (
    delete_artifact,
    record_artifact_download,
    record_artifact_view,
    upload_artifact,
)
from .tasks import extract_video_duration_task

logger = logging.getLogger(__name__)


def filter_video_metadata_queryset(params, queryset=None):
    """Apply functional parameter matrices against a VideoMetadata base queryset.

    Parses, casts, and sanitizes input data signatures (IDs, enumerations,
    and date ranges) against specific lookups.
    """
    qs = (
        queryset
        if queryset is not None
        else VideoMetadata.objects.select_related(
            "mission", "drone", "uploaded_by"
        ).all()
    )

    for param_names, field in (
        (("mission_id", "mission"), "mission_id"),
        (("drone_id", "drone"), "drone_id"),
        (("uploaded_by_id", "uploaded_by"), "uploaded_by_id"),
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
    """Internal mixin resolving the target mission with access scoping.

    Applies ``restrict_missions_for_user`` unconditionally so that every
    role is scoped to its authorized missions. Admin, Commander, and
    Dispatcher see all missions; Operator sees only assigned; Viewer
    sees only same-unit; Technician sees only repair/write-off related.
    """

    def get_mission(self):
        """Resolve the mission from the URL, scoped to the requester's
        authorized missions. Returns 404 for inaccessible or
        non-existent missions."""
        if not hasattr(self, "_mission"):
            self._mission = generics.get_object_or_404(
                restrict_missions_for_user(Mission.objects.all(), self.request.user),
                id=self.kwargs["mission_pk"],
            )
        return self._mission


@extend_schema_view(get=artifact_get_schema, post=artifact_post_schema)
class ArtifactListCreateView(_MissionArtifactMixin, generics.ListCreateAPIView):
    """List and upload image and data mission artifacts."""

    pagination_class = StandardResultsSetPagination
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        """Gate POST behind upload permission; safe methods behind view."""
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), MediaViewPermission()]
        return [permissions.IsAuthenticated(), MediaUploadPermission()]

    def get_serializer_class(self):
        """Use the upload serializer for POST
        and the read serializer for safe methods."""
        if self.request.method in permissions.SAFE_METHODS:
            return MissionArtifactSerializer
        return MissionArtifactUploadSerializer

    def get_queryset(self):
        mission_queryset = Mission.objects.all()
        if self.request.method in permissions.SAFE_METHODS:
            # Keep mission-derived artifact listings aligned with mission
            # visibility so viewers only see media for missions they may read.
            mission_queryset = restrict_missions_for_user(
                mission_queryset,
                self.request.user,
            )
        mission = generics.get_object_or_404(
            mission_queryset,
            id=self.kwargs["mission_pk"],
        )
        return MissionArtifact.objects.filter(mission=mission).select_related(
            "uploaded_by"
        )

    def create(self, request, *args, **kwargs):
        """Validate and save a mission artifact, create an audit log entry."""
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
    """List detailed information or delete target mission artifact."""

    serializer_class = MissionArtifactSerializer
    lookup_url_kwarg = "artifact_pk"

    def get_permissions(self):
        """Gate DELETE behind delete permission; safe methods behind view."""
        if self.request.method in permissions.SAFE_METHODS:
            return [permissions.IsAuthenticated(), MediaViewPermission()]
        return [permissions.IsAuthenticated(), MediaDeletePermission()]

    def get_queryset(self):
        """Return mission artifacts related to the target mission."""
        mission = self.get_mission()
        return MissionArtifact.objects.filter(mission=mission).select_related(
            "uploaded_by"
        )

    def retrieve(self, request, *args, **kwargs):
        """Fetch the detailed information about the artifact
        and create an audit log entry."""
        instance = self.get_object()
        record_artifact_view(
            user=request.user,
            artifact=instance,
            request=request,
        )
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_destroy(self, instance):
        """Delete the artifact and create an audit log entry."""
        delete_artifact(
            artifact=instance,
            action_user=self.request.user,
            request=self.request,
        )


@extend_schema_view(get=protected_media_get_schema)
class ProtectedMediaView(APIView):
    """Secure download mission artifact.

    Checks user permissions and serves files directly in DEBUG mode
    or hands off the download to Nginx (via X-Accel-Redirect) in production.
    """

    permission_classes = [IsAuthenticated, MediaViewPermission]

    def get(self, request, mission_pk, artifact_pk):
        """Authorize the download request and return the file
        or Nginx redirect response."""
        get_object_or_404(
            restrict_missions_for_user(Mission.objects.all(), request.user),
            pk=mission_pk,
        )

        artifact = get_object_or_404(
            MissionArtifact, pk=artifact_pk, mission_id=mission_pk
        )

        self.check_object_permissions(request, artifact)

        file_field = artifact.file

        if not file_field or not file_field.storage.exists(file_field.name):
            raise Http404("File not found on server.")

        content_type, _ = mimetypes.guess_type(file_field.name)
        content_type = content_type or "application/octet-stream"
        filename = artifact.original_filename or os.path.basename(file_field.name)

        safe_name = posixpath.normpath(file_field.name)
        if safe_name.startswith("..") or safe_name.startswith("/"):
            raise Http404("Invalid file path.")

        record_artifact_download(
            user=request.user,
            artifact=artifact,
            request=request,
        )

        if settings.DEBUG:
            return FileResponse(
                file_field,
                content_type=content_type,
                as_attachment=True,
                filename=filename,
            )
        else:
            response = HttpResponse(content_type=content_type)

            internal_path = f"/internal-media/{safe_name}"
            response["X-Accel-Redirect"] = internal_path

            escaped_filename = escape_uri_path(filename)
            response["Content-Disposition"] = (
                f"attachment; filename*=UTF-8''{escaped_filename}"
            )

            return response


class MediaAuditLogFilter(filters.FilterSet):
    """Query string filter mappings for managing MediaAuditLog query scopes."""

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
    """List read-only media audit log entries."""

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
    """List, create, update and delete video metadata."""

    queryset = VideoMetadata.objects.select_related(
        "mission", "drone", "uploaded_by"
    ).all()
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        """Use the upload serializer for POST
        and the read serializer for other methods."""
        if self.action == "create":
            return VideoUploadSerializer
        return VideoMetadataSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "list":
            visible_missions = restrict_missions_for_user(
                Mission.objects.all(),
                self.request.user,
            ).values("id")
            queryset = queryset.filter(mission_id__in=visible_missions)
        return filter_video_metadata_queryset(
            self.request.query_params,
            queryset=queryset,
        )

    def get_permissions(self):
        """Gate API methods behind their corresponding RBAC permissions."""
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
        """Extract video duration and save video metadata."""
        instance = serializer.save(
            uploaded_by=self.request.user,
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
        """Safely delete the instance, returning a validation error
        if it has protected dependencies."""
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
    """Render the HTML page for browsing video lists."""

    template_name = "media/video_browser.html"

    def dispatch(self, request, *args, **kwargs):
        """Validate authorization and RBAC permissions of a user
        before rendering the HTML page."""
        if not request.user or not request.user.is_authenticated:
            return HttpResponseForbidden("Authentication required.")

        permission_validator = MediaViewPermission()
        if not permission_validator.has_permission(request, self):
            return HttpResponseForbidden(
                "You do not have permission to access video records."
            )

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Return in context a filtered list of video metadata related
        to provided drone/mission or a list of corresponding validation errors."""
        context = super().get_context_data(**kwargs)
        context["mission_id"] = self.request.GET.get("mission_id", "")
        context["drone_id"] = self.request.GET.get("drone_id", "")
        context["videos"] = []
        context["error"] = None

        if not self.request.GET:
            return context

        try:
            visible_missions = restrict_missions_for_user(
                Mission.objects.all(),
                self.request.user,
            ).values("id")
            context["videos"] = filter_video_metadata_queryset(
                self.request.GET,
                queryset=VideoMetadata.objects.select_related(
                    "mission",
                    "drone",
                    "uploaded_by",
                ).filter(mission_id__in=visible_missions),
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
