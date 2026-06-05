import os
from django.conf import settings
from rest_framework import serializers

from common.serializers import UserBriefSerializer
from .models import (
    ALL_ALLOWED_EXTENSIONS,
    EXTENSION_TO_FILE_TYPE,
    MissionArtifact,
)

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
        read_only_fields = fields


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
        if file.size is None:
            raise serializers.ValidationError("Cannot determine file size.")

        ext = os.path.splitext(file.name)[1].lower()
        if ext not in ALL_ALLOWED_EXTENSIONS:
            raise serializers.ValidationError(
                f"Unsupported file type '{ext}'. "
                f"Allowed: {', '.join(sorted(ALL_ALLOWED_EXTENSIONS))}."
            )

        max_bytes = settings.ARTIFACT_MAX_FILE_SIZE_MB * 1024 * 1024
        if file.size > max_bytes:
            raise serializers.ValidationError(
                f"File size {file.size} bytes exceeds the "
                f"{settings.ARTIFACT_MAX_FILE_SIZE_MB} MB limit."
            )

        return file

    def validate(self, attrs):
        file = attrs.get("file")
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            attrs["file_type"] = EXTENSION_TO_FILE_TYPE[ext]
        return attrs

