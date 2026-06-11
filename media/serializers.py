import os

from django.conf import settings
from rest_framework import serializers

from common.serializers import UserBriefSerializer

from .models import MissionArtifact, _get_all_allowed_extensions


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
