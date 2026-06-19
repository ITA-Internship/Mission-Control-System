import json
import logging
import os
import subprocess

from django.conf import settings
from rest_framework import serializers

from common.serializers import UserBriefSerializer
from missions.models import MissionDrone

from .models import MissionArtifact, VideoMetadata, _get_all_allowed_extensions

logger = logging.getLogger(__name__)


class VideoMetadataSerializer(serializers.ModelSerializer):
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
        ]

    def get_url(self, obj):
        return obj.url


class VideoUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = VideoMetadata
        fields = ["id", "mission", "drone", "file", "recorded_at", "checksum"]
        read_only_fields = ["id"]

    def validate(self, attrs):
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
        file_obj = validated_data["file"]

        validated_data["file_name"] = file_obj.name
        validated_data["file_size"] = file_obj.size
        content_type = getattr(file_obj, "content_type", "") or ""
        validated_data["content_type"] = content_type

        validated_data["uploader"] = self.context["request"].user
        validated_data["status"] = VideoMetadata.Status.READY

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


class MissionArtifactUploadSerializer(serializers.Serializer):

    file = serializers.FileField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True)
    captured_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_title(self, value):
        stripped = (value or "").strip()
        if not stripped:
            raise serializers.ValidationError("Title is required.")
        return stripped

    def validate_file(self, file):
        if file.size is None or file.size == 0:
            raise serializers.ValidationError(
                "File is empty or its size cannot be determined."
            )

        ext = os.path.splitext(file.name)[1].lower()
        all_allowed = _get_all_allowed_extensions()
        if ext not in all_allowed:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. "
                f"Allowed: {', '.join(sorted(all_allowed))}."
            )

        max_bytes = settings.ARTIFACT_MAX_FILE_SIZE_MB * 1024 * 1024
        if file.size > max_bytes:
            raise serializers.ValidationError(
                f"File size {file.size} bytes exceeds the "
                f"{settings.ARTIFACT_MAX_FILE_SIZE_MB} MB limit."
            )

        return file
