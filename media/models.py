import os
import uuid
from django.conf import settings
from django.db import models


class FileType(models.TextChoices):
    VIDEO = "video", "Video"
    IMAGE = "image", "Image"
    DATA = "data", "Data"


ALLOWED_EXTENSIONS = {
    FileType.VIDEO: [".mp4", ".avi", ".mov"],
    FileType.IMAGE: [".jpg", ".jpeg", ".png"],
    FileType.DATA: [".csv", ".json"],
}

ALL_ALLOWED_EXTENSIONS = [
    ext for exts in ALLOWED_EXTENSIONS.values() for ext in exts
]

EXTENSION_TO_FILE_TYPE = {
    ext: file_type
    for file_type, exts in ALLOWED_EXTENSIONS.items()
    for ext in exts
}


def artifact_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return f"artifacts/mission_{instance.mission_id}/{safe_name}"


class MissionArtifact(models.Model):
    mission = models.ForeignKey(
        "missions.Mission",
        on_delete=models.CASCADE,
        related_name="artifacts",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="uploaded_artifacts",
    )

    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    file = models.FileField(upload_to=artifact_upload_path)
    file_type = models.CharField(
        max_length=10,
        choices=FileType.choices,
    )
    original_filename = models.CharField(max_length=255)
    file_size = models.PositiveBigIntegerField(
        help_text="File size in bytes",
    )

    storage_backend = models.CharField(
        max_length=20,
        default="local",
    )

    captured_at = models.DateTimeField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mission_artifacts"
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["uploaded_at"]),
            models.Index(fields=["file_type"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.file_type}) — Mission #{self.mission_id}"
