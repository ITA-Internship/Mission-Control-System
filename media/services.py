"""Provide service-layer functions for media management.

Functions:
    record_artifact_view: Logs an authorized user access event for an artifact.
    upload_artifact: Creates a new artifact and an entry in media
    and mission audit logs.
    delete_artifact: Deletes an artifact and creates an entry in media
    and mission audit logs.
"""

import logging

from django.core.files.storage import default_storage
from django.db import transaction

from common.request_utils import get_client_ip
from missions.models import MissionAuditLog

from .models import MediaAuditLog, MissionArtifact

logger = logging.getLogger(__name__)


def _artifact_snapshot(artifact):
    """Generate a serializable dictionary representation of an artifact."""
    return {
        "artifact_id": artifact.id,
        "mission_id": artifact.mission_id,
        "file_type": artifact.file_type,
        "original_filename": artifact.original_filename,
        "file_size": artifact.file_size,
        "title": artifact.title,
    }


def _write_media_audit_log(
    *, user, artifact, action, request=None, changes=None, mission_id=None
):
    """Create a MediaAuditLog row. Callers decide transaction semantics."""
    if mission_id is None and artifact:
        mission_id = artifact.mission_id
    return MediaAuditLog.objects.create(
        user=user if getattr(user, "is_authenticated", False) else None,
        artifact=artifact,
        mission_id=mission_id,
        action=action,
        changes=changes or {},
        ip_address=get_client_ip(request),
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
    """Log an entry indicating that an authorized user
    viewed or accessed the artifact."""
    _record_access(
        user=user,
        artifact=artifact,
        action=MediaAuditLog.Action.VIEW,
        request=request,
    )


def record_artifact_download(*, user, artifact, request=None):
    """Log an entry indicating that an authorized user
    downloaded the artifact."""
    _record_access(
        user=user,
        artifact=artifact,
        action=MediaAuditLog.Action.DOWNLOAD,
        request=request,
    )


def record_permission_denied(
    *, user, request=None, permission_code=None, reason=None, obj=None
):
    """Best-effort audit entry for a denied media authorization check.

    Never raises: an audit-write failure must not turn a permission check into
    a 500. Links the artifact FK only when ``obj`` is a MissionArtifact; other
    objects (e.g. VideoMetadata) are recorded by type/id in ``changes``.
    """
    artifact = obj if isinstance(obj, MissionArtifact) else None
    changes = {
        "permission": permission_code,
        "reason": reason,
        "path": getattr(request, "path", None),
        "method": getattr(request, "method", None),
    }
    if obj is not None and artifact is None:
        changes["object_type"] = type(obj).__name__
        changes["object_id"] = getattr(obj, "id", None)

    try:
        _write_media_audit_log(
            user=user,
            artifact=artifact,
            action=MediaAuditLog.Action.PERMISSION_DENIED,
            request=request,
            changes=changes,
        )
    except Exception:
        logger.exception("Failed to write media permission-denied audit log")


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
    """Ingest a new media artifact, save its physical payload
    and create an audit log entry.

    Executes inside an atomic database block. If the transaction crashes post-file-save,
    a defensive cleanup block intercepts the error to purge the orphaned file from
    the active storage backend.
    """
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
    """Remove an artifact record from the database and queue physical file deletion.

    Wraps database operations inside an atomic transaction block. The audit log
    entry is written before the deletion to preserve foreign key associations.
    The file removal from storage is safely deferred until the transaction commits.
    """
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
