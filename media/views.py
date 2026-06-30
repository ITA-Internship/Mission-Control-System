from django_filters import rest_framework as filters
from django.db import transaction
from django.db.models import ProtectedError
from django.http import HttpResponseForbidden
from django.utils.dateparse import parse_date
from django.views.generic import TemplateView
from rest_framework import generics, parsers, permissions, status, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common.pagination import StandardResultsSetPagination
from missions.models import Mission

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
    VideoUploadSerializer
)
from .services import delete_artifact, record_artifact_view, upload_artifact
from .tasks import extract_video_duration_task


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
    queryset = MediaAuditLog.objects.select_related("artifact", "mission", "user").all()


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
        qs = super().get_queryset()
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
        instance = serializer.save(uploader=self.request.user, status="PROCESSING")

        extract_video_duration_task.delay(instance.id)

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
