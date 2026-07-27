"""DRF serializers for the media API.

Validate and shape image, data and video artifacts,
audit log entries.
"""

import json
import logging
import os
import subprocess

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
    uploader_username = serializers.CharField(
        source="uploader.username", read_only=True, default=None
    )

    class Meta:
        model = VideoMetadata
        fields = [
            "id",
            "mission",
            "drone",
            "uploader",
            "uploader_username",
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
            "file_size",
            "content_type",
            "status",
            "created_at",
            "updated_at",
            "uploader",
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

        # Verify the real content matches the claimed video extension instead
        # of trusting the client-supplied content_type. The detected MIME type
        # is stashed for create() so it, too, never relies on client input.
        allowed = [f".{ext}" for ext in VIDEO_ALLOWED_EXTENSIONS]
        try:
            _, detected = validate_file_content(file, allowed)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)
        self._detected_content_type = detected

        max_bytes = settings.VIDEO_MAX_FILE_SIZE_MB * 1024 * 1024
        if file.size > max_bytes:
            raise serializers.ValidationError(
                f"File size exceeds the limit of {settings.VIDEO_MAX_FILE_SIZE_MB}MB."
            )

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
        """Populate file metadata, record the uploader
        and extract video duration via ffprobe.

        Sets status to UPLOADING and safely falls back to 0 or None for duration
        if ffprobe execution fails.
        """

        file_obj = validated_data["file"]

        validated_data["file_name"] = os.path.basename(file_obj.name)
        validated_data["file_size"] = file_obj.size
        # Server-detected content type (set in validate_file); never the
        # client-supplied header.
        content_type = getattr(self, "_detected_content_type", "") or ""
        validated_data["content_type"] = content_type

        validated_data["uploader"] = self.context["request"].user
        validated_data.setdefault("status", VideoMetadata.Status.UPLOADING)

        if not content_type.startswith("video/"):
            validated_data["duration_seconds"] = None
            return super().create(validated_data)

        instance = super().create(validated_data)

        try:
            file_path = instance.file.path

            cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "json",
                file_path,
            ]

            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )

            probe_data = json.loads(result.stdout)
            duration = float(probe_data["format"]["duration"])

            instance.duration_seconds = int(duration)
            instance.save(update_fields=["duration_seconds"])

        except Exception as e:
            logger.error(f"FFprobe failed to parse video duration: {str(e)}")
            instance.duration_seconds = 0
            instance.save(update_fields=["duration_seconds"])

        return instance


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

        # Validate the file's real content against its extension. The extension
        # allow-list alone is spoofable (arbitrary bytes named ``x.png``); this
        # sniffs the actual bytes with libmagic.
        try:
            validate_file_content(file, _get_all_allowed_extensions())
        except DjangoValidationError as exc:
            raise serializers.ValidationError(exc.messages)

        max_bytes = settings.ARTIFACT_MAX_FILE_SIZE_MB * 1024 * 1024
        if file.size > max_bytes:
            raise serializers.ValidationError(
                f"File size {file.size} bytes exceeds the "
                f"{settings.ARTIFACT_MAX_FILE_SIZE_MB} MB limit."
            )

        return file
