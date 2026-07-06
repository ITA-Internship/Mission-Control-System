import json
import subprocess

from celery import shared_task

from .models import VideoMetadata


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
