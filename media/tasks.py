"""Asynchronous Celery tasks for processing media metadata."""

import json
import subprocess

from celery import shared_task

from .models import VideoMetadata


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

        instance.duration_seconds = int(duration)
        instance.status = VideoMetadata.Status.READY
        instance.save(update_fields=["duration_seconds", "status"])

    except Exception:
        VideoMetadata.objects.filter(id=video_id).update(
            status=VideoMetadata.Status.FAILED
        )
