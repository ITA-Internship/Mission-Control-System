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

        instance.duration_seconds = int(duration)
        instance.status = VideoMetadata.Status.READY
        instance.save(update_fields=["duration_seconds", "status"])

    except Exception:
        VideoMetadata.objects.filter(id=video_id).update(
            status=VideoMetadata.Status.FAILED
        )
