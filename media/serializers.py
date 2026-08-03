"""DRF serializers for the media API.

Validate and shape image, data and video artifacts,
audit log entries.
"""

import logging
import os

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from common.serializers import UserBriefSerializer
from missions.models import MissionDrone

from .models import (
    VIDEO_ALLOWED_EXTENSIONS,
    MediaAuditLog,
    MissionArtifact,
    VideoMetadata,
    _get_all_allowed_extensions,
)
from .validators import validate_file_content

logger = logging.getLogger(__name__)


class VideoMetadataSerializer(serializers.ModelSerializer):
    """Serialize video metadata record for listing and updating."""

    url = serializers.SerializerMethodField()
    uploaded_by_username = serializers.CharField(
        source="uploaded_by.username", read_only=True, default=None
    )

    class Meta:
        model = VideoMetadata
        fields = [
            "id",
            "mission",
            "drone",
            "uploaded_by",
            "uploaded_by_username",
            "file",
            "file_name",
            "file_size",
            "content_type",
            "status",
            "checksum",
            "duration_seconds",
            "recorded_at",
            "created_at",
            "updated_at",
            "url",
        ]
        read_only_fields = [
            "id",
            "mission",
            "drone",
            "file_size",
            "content_type",
            "status",
            "created_at",
            "updated_at",
            "uploaded_by",
            "duration_seconds",
            "file",
            "file_name",
        ]

    def get_url(self, obj) -> str:
        """Return video file URL."""
        return obj.url


class VideoUploadSerializer(serializers.ModelSerializer):
    """Serialize video metadata record.

    Validates that the provided drone is actively assigned to the target mission.
    """

    class Meta:
        model = VideoMetadata
        fields = ["id", "mission", "drone", "file", "recorded_at", "checksum"]
        read_only_fields = ["id"]

    def validate_file(self, file):
        """Validate the video file's real content, extension and size."""
        if file.size is None or file.size == 0:
            raise serializers.ValidationError(
                "File is empty or its size cannot be determined."
            )

        max_bytes = settings.VIDEO_MAX_FILE_SIZE_MB * 1024 * 1024
        if file.size > max_bytes:
            raise serializers.ValidationError(
                f"File size exceeds the limit of {settings.VIDEO_MAX_FILE_SIZE_MB}MB."
            )

        # Verify the real content matches the claimed video extension instead
        # of trusting the client-supplied content_type. The detected MIME type
        # is stashed for create() so it, too, never relies on client input.
        allowed = [f".{ext}" for ext in VIDEO_ALLOWED_EXTENSIONS]
        try:
            _, detected = validate_file_content(file, allowed)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        self._detected_content_type = detected

        return file

    def validate(self, attrs):
        """Validate that the provided drone belongs to the target mission."""
        attrs = super().validate(attrs)
        if not MissionDrone.objects.filter(
            mission=attrs["mission"],
            drone=attrs["drone"],
        ).exists():
            raise serializers.ValidationError(
                {"drone": "Drone must be assigned to the selected mission."}
            )
        return attrs

    def create(self, validated_data):
        """Populate file metadata and record the uploader.

        Sets status to UPLOADING. Video duration is extracted asynchronously by
        ``extract_video_duration_task`` (enqueued in the view), which runs the
        ffprobe subprocess with a strict timeout off the request path.
        """

        file_obj = validated_data["file"]

        validated_data["file_name"] = os.path.basename(file_obj.name)
        validated_data["file_size"] = file_obj.size
        # Server-detected content type (set in validate_file); never the
        # client-supplied header.
        validated_data["content_type"] = (
            getattr(self, "_detected_content_type", "") or ""
        )

        validated_data["uploaded_by"] = self.context["request"].user
        validated_data.setdefault("status", VideoMetadata.Status.UPLOADING)

        # duration_seconds is left unset here (defaults to NULL) and populated by
        # extract_video_duration_task, which the view enqueues for every upload.
        # It is deliberately NOT gated on the detected MIME prefix: a valid
        # video can sniff as application/mp4 or application/x-matroska (not
        # video/*), and every file reaching here is an already-validated video.
        return super().create(validated_data)


class MissionArtifactSerializer(serializers.ModelSerializer):
    """Serialize artifact data for list responses."""

    uploaded_by = UserBriefSerializer(read_only=True)

    class Meta:
        model = MissionArtifact
        fields = [
            "id",
            "mission",
            "uploaded_by",
            "title",
            "description",
            "file",
            "file_type",
            "original_filename",
            "file_size",
            "storage_backend",
            "captured_at",
            "uploaded_at",
        ]
        read_only_fields = [
            "id",
            "uploaded_by",
            "file",
            "file_type",
            "original_filename",
            "file_size",
            "storage_backend",
            "uploaded_at",
        ]


class MediaAuditLogSerializer(serializers.ModelSerializer):
    """Serialize read-only media audit log data for list responses."""

    user = UserBriefSerializer(read_only=True)

    class Meta:
        model = MediaAuditLog
        fields = [
            "id",
            "action",
            "artifact",
            "mission",
            "user",
            "changes",
            "ip_address",
            "created_at",
        ]
        read_only_fields = fields


class MissionArtifactUploadSerializer(serializers.Serializer):
    """Serialize mission artifact record."""

    file = serializers.FileField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    captured_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_title(self, value):
        """Validate that the artifact title is not blank."""
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("Title is required.")
        return stripped

    def validate_file(self, file):
        """Validate the artifact file's real content, extension and size."""
        if file.size is None or file.size == 0:
            raise serializers.ValidationError(
                "File is empty or its size cannot be determined."
            )

        max_bytes = settings.ARTIFACT_MAX_FILE_SIZE_MB * 1024 * 1024
        if file.size > max_bytes:
            raise serializers.ValidationError(
                f"File size {file.size} bytes exceeds the "
                f"{settings.ARTIFACT_MAX_FILE_SIZE_MB} MB limit."
            )

        # Validate the file's real content against its extension. The extension
        # allow-list alone is spoofable (arbitrary bytes named ``x.png``); this
        # sniffs the actual bytes with libmagic.
        try:
            validate_file_content(file, _get_all_allowed_extensions())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

        return file
