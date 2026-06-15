import logging

from django.core.files.storage import default_storage
from django.db import transaction

from missions.models import MissionAuditLog

from .models import MissionArtifact

logger = logging.getLogger(__name__)


def upload_artifact(
    *,
    mission,
    file,
    title,
    uploaded_by,
    description=None,
    captured_at=None,
):
    artifact = MissionArtifact(
        mission=mission,
        uploaded_by=uploaded_by,
        title=title,
        description=description,
        file=file,
        captured_at=captured_at,
    )

    try:
        with transaction.atomic():
            artifact.save()

            MissionAuditLog.objects.create(
                user=uploaded_by,
                action="artifact_uploaded",
                target_model="MissionArtifact",
                target_id=artifact.id,
                changes={
                    "mission_id": mission.id,
                    "file_type": artifact.file_type,
                    "original_filename": artifact.original_filename,
                    "file_size": artifact.file_size,
                    "title": title,
                },
            )
    except Exception:
        current_file_name = artifact.file.name if artifact.file else None
        if current_file_name and current_file_name != file.name:
            if default_storage.exists(current_file_name):
                try:
                    default_storage.delete(current_file_name)
                except Exception:
                    logger.exception(
                        "Failed to clean up orphaned file %s", current_file_name
                    )
        raise

    return artifact


def delete_artifact(*, artifact, action_user):
    artifact_id = artifact.id
    mission_id = artifact.mission_id
    original_filename = artifact.original_filename
    file_name = artifact.file.name if artifact.file else None

    with transaction.atomic():
        MissionAuditLog.objects.create(
            user=action_user,
            action="artifact_deleted",
            target_model="MissionArtifact",
            target_id=artifact_id,
            changes={
                "mission_id": mission_id,
                "file_type": artifact.file_type,
                "original_filename": original_filename,
                "title": artifact.title,
            },
        )
        artifact.delete()

    if file_name:

        def _cleanup_file():
            try:
                default_storage.delete(file_name)
            except Exception:
                logger.exception(
                    "Failed to remove artifact file %s; " "requires manual cleanup.",
                    file_name,
                )

        transaction.on_commit(_cleanup_file)
