"""Asynchronous Celery tasks for processing media metadata."""

import json
import subprocess
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.utils import timezone

from .models import MediaAuditLog, VideoMetadata


@shared_task
def purge_media_audit_logs_task():
    """Enforce the media audit-log retention policy on a schedule.

    Removes MediaAuditLog entries older than MEDIA_AUDIT_LOG_RETENTION_DAYS.
    A value <= 0 disables purging. Returns the number of rows removed.
    """
    days = settings.MEDIA_AUDIT_LOG_RETENTION_DAYS
    if days <= 0:
        return 0

    cutoff = timezone.now() - timedelta(days=days)
    return MediaAuditLog.objects.purge_older_than(cutoff)


@shared_task
def extract_video_duration_task(video_id):
    """Extract the exact play duration of a video file using ffprobe.

    Invokes the ffprobe binary in a timed subprocess to parse the video's
    container metadata. Upon successful extraction, it stores the duration
    and marks the instance status as READY. If any failure occurs, the record
    is flagged as FAILED.
    """
    try:
        instance = VideoMetadata.objects.get(id=video_id)
        if not instance.file:
            return

        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            instance.file.path,
        ]

        result = subprocess.run(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=30
        )
        probe_data = json.loads(result.stdout)
        duration = float(probe_data["format"]["duration"])

        import hashlib

        sha256_hash = hashlib.sha256()
        with open(instance.file.path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096 * 1024), b""):
                sha256_hash.update(byte_block)

        instance.duration_seconds = int(duration)
        instance.status = VideoMetadata.Status.READY
        instance.checksum = sha256_hash.hexdigest()
        instance.save(update_fields=["duration_seconds", "status", "checksum"])

    except Exception:
        VideoMetadata.objects.filter(id=video_id).update(
            status=VideoMetadata.Status.FAILED
        )
