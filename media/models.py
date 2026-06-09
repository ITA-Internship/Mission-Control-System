import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.validators import FileExtensionValidator
from django.db import models


class FileType(models.TextChoices):
    VIDEO = "video", "Video"
    IMAGE = "image", "Image"
    DATA = "data", "Data"


def _get_all_allowed_extensions():
    return [
        ext for exts in settings.ARTIFACT_ALLOWED_EXTENSIONS.values() for ext in exts
    ]


def _get_extension_to_file_type():
    return {
        ext: FileType(file_type)
        for file_type, exts in settings.ARTIFACT_ALLOWED_EXTENSIONS.items()
        for ext in exts
    }


EXTENSION_TO_FILE_TYPE = _get_extension_to_file_type()


def _validate_file_size(file):
    if file.size is None:
        raise ValidationError("Cannot determine file size.")
    if file.size == 0:
        raise ValidationError("File is empty (0 bytes).")
    max_bytes = settings.ARTIFACT_MAX_FILE_SIZE_MB * 1024 * 1024
    if file.size > max_bytes:
        raise ValidationError(
            f"File size {file.size} bytes exceeds the "
            f"{settings.ARTIFACT_MAX_FILE_SIZE_MB} MB limit."
        )


def artifact_upload_path(instance, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _get_all_allowed_extensions():
        raise ValidationError(f"Unsupported file extension: {ext}")
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return f"artifacts/mission_{instance.mission_id}/{safe_name}"


def _detect_storage_backend():
    storage = default_storage
    if hasattr(storage, "_wrapped"):
        try:
            _ = storage.location
        except AttributeError:
            pass
        storage = storage._wrapped
    backend_class = type(storage).__name__
    backend_map = {
        "FileSystemStorage": "local",
        "S3Boto3Storage": "s3",
        "GoogleCloudStorage": "gcs",
        "AzureStorage": "azure",
    }
    return backend_map.get(backend_class, backend_class.lower())


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

    file = models.FileField(
        upload_to=artifact_upload_path,
        validators=[
            FileExtensionValidator(
                allowed_extensions=[
                    ext.lstrip(".") for ext in _get_all_allowed_extensions()
                ]
            ),
            _validate_file_size,
        ],
    )
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

    def clean(self):
        super().clean()
        if self.title and not self.title.strip():
            raise ValidationError({"title": "Title must not be blank."})

    def save(self, *args, **kwargs):
        if self.file and not self.original_filename:
            self.original_filename = os.path.basename(self.file.name)

        if self.file and not self.file_size:
            if hasattr(self.file, "size") and self.file.size:
                self.file_size = self.file.size
        if self.file and not self.file_type:
            ext = os.path.splitext(self.file.name)[1].lower()
            ext_map = _get_extension_to_file_type()
            if ext in ext_map:
                self.file_type = ext_map[ext]

        self.storage_backend = _detect_storage_backend()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.file_type}) — Mission #{self.mission_id}"
