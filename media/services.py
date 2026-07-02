import logging

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction

from missions.models import MissionAuditLog

from .models import MediaAuditLog, MissionArtifact

logger = logging.getLogger(__name__)


def _get_client_ip(request):
    if request is None:
        return None

    trusted = getattr(settings, "TRUSTED_PROXY_COUNT", 0)
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for and trusted > 0:
        parts = [ip.strip() for ip in x_forwarded_for.split(",") if ip.strip()]
        idx = len(parts) - trusted - 1
        if 0 <= idx < len(parts):
            return parts[idx]

    return request.META.get("REMOTE_ADDR")


def _artifact_snapshot(artifact):
    return {
        "artifact_id": artifact.id,
        "mission_id": artifact.mission_id,
        "file_type": artifact.file_type,
        "original_filename": artifact.original_filename,
        "file_size": artifact.file_size,
        "title": artifact.title,
    }


def _write_media_audit_log(*, user, artifact, action, request=None, changes=None):
    """Create a MediaAuditLog row. Callers decide transaction semantics."""
    return MediaAuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        artifact=artifact,
        mission_id=artifact.mission_id if artifact else None,
        action=action,
        changes=changes or {},
        ip_address=_get_client_ip(request),
    )


def _record_access(*, user, artifact, action, request=None):
    """Best-effort access log; never block serving the artifact on failure."""
    try:
        _write_media_audit_log(
            user=user, artifact=artifact, action=action, request=request
        )
    except Exception:
        logger.exception(
            "Failed to write media audit log (action=%s artifact=%s)",
            action,
            getattr(artifact, "id", None),
        )


def record_artifact_view(*, user, artifact, request=None):
    _record_access(
        user=user,
        artifact=artifact,
        action=MediaAuditLog.Action.VIEW,
        request=request,
    )


def upload_artifact(
    *,
    mission,
    file,
    title,
    uploaded_by,
    description=None,
    captured_at=None,
    request=None,
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

            changes = _artifact_snapshot(artifact)

            MissionAuditLog.objects.create(
                user=uploaded_by,
                action="artifact_uploaded",
                target_model="MissionArtifact",
                target_id=artifact.id,
                changes=changes,
            )

            _write_media_audit_log(
                user=uploaded_by,
                artifact=artifact,
                action=MediaAuditLog.Action.UPLOAD,
                request=request,
                changes=changes,
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


def delete_artifact(*, artifact, action_user, request=None):
    artifact_id = artifact.id
    mission_id = artifact.mission_id
    file_name = artifact.file.name if artifact.file else None
    changes = _artifact_snapshot(artifact)

    with transaction.atomic():
        MissionAuditLog.objects.create(
            user=action_user,
            action="artifact_deleted",
            target_model="MissionArtifact",
            target_id=artifact_id,
            changes=changes,
        )

        # Logged before delete so the artifact FK is still populated; it is
        # nulled by on_delete=SET_NULL once the artifact row is removed, while
        # mission_id and `changes` keep the reference intact.
        _write_media_audit_log(
            user=action_user,
            artifact=artifact,
            action=MediaAuditLog.Action.DELETE,
            request=request,
            changes=changes,
        )

        artifact.delete()

    if file_name:

        def _cleanup_file():
            try:
                default_storage.delete(file_name)
            except Exception:
                logger.exception(
                    "Failed to remove artifact file %s; requires manual cleanup.",
                    file_name,
                )

        transaction.on_commit(_cleanup_file)

    logger.info("Artifact %s deleted from mission %s", artifact_id, mission_id)
