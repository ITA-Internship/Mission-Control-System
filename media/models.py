"""Data models for managing mission media artifacts and audit logs.

Classes:
    MissionArtifact: Represents an image or data artifact.
    MediaAuditLog: Represents a log of actions performed on artifacts.
    VideoMetadata: Represents a metadata of a video artifact.
"""

import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models

from drones.models import Drone
from missions.models import Mission, MissionDrone

VIDEO_ALLOWED_EXTENSIONS = ["mp4", "avi", "mov", "mkv"]


class FileType(models.TextChoices):
    """Enumeration of recognized artifact file types."""

    VIDEO = "video", "Video"
    IMAGE = "image", "Image"
    DATA = "data", "Data"


def _get_all_allowed_extensions():
    """Flatten and return all permitted file extensions from application settings."""
    return [
        ext for exts in settings.ARTIFACT_ALLOWED_EXTENSIONS.values() for ext in exts
    ]


def _get_extension_to_file_type():
    """Map each unique extension back to its corresponding FileType choice."""
    return {
        ext: FileType(file_type)
        for file_type, exts in settings.ARTIFACT_ALLOWED_EXTENSIONS.items()
        for ext in exts
    }


EXTENSION_TO_FILE_TYPE = _get_extension_to_file_type()


def _validate_file_size(file):
    """Validate that the uploaded file is neither
    empty nor exceeds global constraints."""
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


def video_upload_path(instance, filename):
    """Generate a destination path for video artifact uploads."""
    # Never interpolate the raw client filename into the storage path: it may
    # contain path-traversal sequences (``../``) or other hostile characters.
    # A UUID plus the (separator-free) extension makes the stored name fully
    # server-controlled, which is this callable's only security responsibility.
    #
    # Extension allow-listing is enforced upstream — by
    # VideoUploadSerializer.validate_file (API -> HTTP 400) and by the field's
    # FileExtensionValidator (forms / full_clean). It is deliberately NOT
    # re-checked here: this runs inside Storage.save(), too late to raise a
    # user-facing ValidationError (DRF would not convert it, yielding a 500).
    ext = os.path.splitext(filename)[1].lower()
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return (
        f"missions/{instance.mission_id}/" f"drones/{instance.drone_id}/" f"{safe_name}"
    )


def artifact_upload_path(instance, filename):
    """Generate a destination path for image and data artifacts,
    verifying file extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in _get_all_allowed_extensions():
        raise ValidationError(f"Unsupported file extension: {ext}")
    safe_name = f"{uuid.uuid4().hex}{ext}"
    return f"artifacts/mission_{instance.mission_id}/{safe_name}"


def validate_video_file_size(value):
    """Validate that the video file is neither
    empty nor exceeds global constraints."""
    max_mb = getattr(settings, "VIDEO_MAX_FILE_SIZE_MB", 500)
    if value.size == 0:
        raise ValidationError("Uploaded file is empty (0 bytes).")
    if value.size > max_mb * 1024 * 1024:
        raise ValidationError(f"File size exceeds the limit of {max_mb}MB.")


def _detect_storage_backend():
    """Return the storage backend active in system settings."""
    return getattr(settings, "STORAGE_PROVIDER", "local")


class MissionArtifact(models.Model):
    """Represent an image or data artifact collected during target mission.

    Stores media files alongside physical file properties, active storage engine states.
    """

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
        """Validate that the artifact title is not blank."""
        super().clean()
        if self.title and not self.title.strip():
            raise ValidationError({"title": "Title must not be blank."})

    def save(self, *args, **kwargs):
        """Create a mission artifact.

        Automatically extracts original filename, computes raw file size,
        evaluates targeted extension to populate file_type,
        and logs the active storage backend.
        """
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
        """Return a string representation of the mission artifact."""
        return f"{self.title} ({self.file_type}) — Mission #{self.mission_id}"


class MediaAuditLogManager(models.Manager):
    def purge_older_than(self, cutoff):
        """Delete media audit entries created strictly before ``cutoff``.

        Used by the retention policy (see the ``purge_audit_logs`` command and
        ``purge_media_audit_logs_task``). Returns the number of rows removed.
        """
        deleted, _ = self.filter(created_at__lt=cutoff).delete()
        return deleted


class MediaAuditLog(models.Model):
    """Record an audit log entry for actions performed on mission artifacts.

    Saves actions performed on mission artifacts along with the user
    who performed an action, a target mission, IP address.
    """

    class Action(models.TextChoices):
        """Enumeration of allowed actions."""

        VIEW = "view", "View"
        DOWNLOAD = "download", "Download"
        UPLOAD = "upload", "Upload"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        PERMISSION_DENIED = "denied", "Permission Denied"

    objects = MediaAuditLogManager()

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media_audit_logs",
    )

    artifact = models.ForeignKey(
        "media.MissionArtifact",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="Null after the referenced artifact is deleted.",
    )

    mission = models.ForeignKey(
        "missions.Mission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="media_audit_logs",
    )

    action = models.CharField(
        max_length=10,
        choices=Action.choices,
    )

    changes = models.JSONField(default=dict, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "media_audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["artifact"]),
            models.Index(fields=["mission"]),
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        """Return a string representation of the media audit log entry."""
        return (
            f"[{self.action}] artifact #{self.artifact_id} "
            f"(Mission #{self.mission_id}) by {self.user}"
        )


class VideoMetadata(models.Model):
    """Represent video metadata record.

    Stores video metadata, its properties, timestamps.
    Validates that the provided drone is actively assigned to the target mission.
    """

    class Status(models.TextChoices):
        """Status of processing video data."""

        UPLOADING = "uploading", "Uploading"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    id = models.BigAutoField(primary_key=True)

    mission = models.ForeignKey(
        Mission,
        on_delete=models.CASCADE,
        related_name="video_metadata",
        help_text="Mission associated with this video",
    )

    drone = models.ForeignKey(
        Drone,
        on_delete=models.PROTECT,
        related_name="video_metadata",
        help_text="Drone used to capture this video",
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_videos",
        help_text="User who uploaded the file",
    )

    file = models.FileField(
        upload_to=video_upload_path,
        validators=[
            FileExtensionValidator(allowed_extensions=VIDEO_ALLOWED_EXTENSIONS),
            validate_video_file_size,
        ],
    )

    file_name = models.CharField(max_length=255)

    file_size = models.BigIntegerField(help_text="File size in bytes")

    content_type = models.CharField(
        max_length=100,
        blank=True,
    )

    duration_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.READY,
    )

    checksum = models.CharField(
        max_length=64,
        blank=True,
        help_text="Optional SHA-256 checksum of the file",
    )

    recorded_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Video recording timestamp from drone metadata",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "video_metadata"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["mission", "drone"]),
            models.Index(fields=["uploaded_by"]),
            models.Index(fields=["created_at"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=["file"],
                name="uq_video_metadata_file",
            ),
        ]

    def clean(self):
        """Validate that the provided drone belongs to the target mission."""
        super().clean()
        if self.mission_id and self.drone_id:
            if not MissionDrone.objects.filter(
                mission_id=self.mission_id,
                drone_id=self.drone_id,
            ).exists():
                raise ValidationError(
                    {"drone": "Drone must be assigned to the selected mission."}
                )

    def __str__(self):
        """Return a string representation of the video metadata."""
        return (
            f"Video #{self.pk} " f"({self.file_name}) - " f"Mission {self.mission_id}"
        )

    @property
    def url(self):
        """Return video file URL."""
        return self.file.url
