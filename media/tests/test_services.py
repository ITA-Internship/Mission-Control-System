"""Test suite for media service layer and audit logging."""

from datetime import timedelta
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from media.factories import MissionArtifactFactory
from media.models import MediaAuditLog, MissionArtifact
from media.services import delete_artifact, upload_artifact
from missions.factories import MissionFactory, OperatorUserFactory
from missions.models import MissionAuditLog


class ArtifactServicesTests(TestCase):
    """Test business logic within the artifact service layer."""

    def setUp(self):
        """Set up an operator user and a mission for testing."""
        self.operator = OperatorUserFactory()
        self.mission = MissionFactory()

    @patch("django.core.files.storage.default_storage.delete")
    def test_upload_artifact_exception_cleans_up_storage(self, mock_delete):
        """Verify file cleanup when database operations fail during upload."""
        with patch(
            "media.services.MissionAuditLog.objects.create",
            side_effect=RuntimeError("DB Error"),
        ):
            file_content = b"test data"
            upload_file = SimpleUploadedFile("test.jpg", file_content)

            with self.assertRaises(RuntimeError):
                upload_artifact(
                    mission=self.mission,
                    file=upload_file,
                    title="Test",
                    uploaded_by=self.operator,
                )

            mock_delete.assert_called_once()

    def test_delete_artifact_service_logic(self):
        """Verify transactional deletion and deferred storage cleanup execution."""
        artifact = MissionArtifactFactory(mission=self.mission, is_image=True)

        with patch("django.core.files.storage.default_storage.delete") as mock_delete:
            with self.captureOnCommitCallbacks(execute=True):
                delete_artifact(artifact=artifact, action_user=self.operator)

            mock_delete.assert_called_once()

        self.assertFalse(MissionArtifact.objects.filter(id=artifact.id).exists())


class MediaAuditLogTransactionTests(TestCase):
    """Test rollback mechanics for audit logging."""

    def setUp(self):
        """Set up an operator user and a mission for testing."""
        self.operator = OperatorUserFactory()
        self.mission = MissionFactory()

    @patch("django.core.files.storage.default_storage.delete")
    def test_media_audit_log_failure_rolls_back_upload(self, mock_delete):
        """Ensure that audit log persistence failures roll back
        the entire upload transaction."""
        with patch(
            "media.services.MediaAuditLog.objects.create",
            side_effect=RuntimeError("DB Error"),
        ):
            upload_file = SimpleUploadedFile("clip.jpg", b"image bytes")

            with self.assertRaises(RuntimeError):
                upload_artifact(
                    mission=self.mission,
                    file=upload_file,
                    title="Rollback Clip",
                    uploaded_by=self.operator,
                )

            mock_delete.assert_called_once()

        self.assertEqual(MissionArtifact.objects.count(), 0)
        self.assertEqual(MissionAuditLog.objects.count(), 0)
        self.assertEqual(MediaAuditLog.objects.count(), 0)


class MediaAuditLogRetentionTests(TestCase):
    """Test MediaAuditLog retention policies and cleanup management command."""

    def setUp(self):
        """Set up a user with operator role, mission and media artifact for testing."""
        self.operator = OperatorUserFactory()
        self.mission = MissionFactory()
        self.artifact = MissionArtifactFactory(mission=self.mission, is_image=True)

    def _log(self, age_days):
        """Helper method to create a media audit log entry
        backdated by a specific number of days."""
        log = MediaAuditLog.objects.create(
            user=self.operator,
            artifact=self.artifact,
            mission_id=self.mission.id,
            action=MediaAuditLog.Action.VIEW,
        )
        # created_at is auto_now_add, so backdate it explicitly.
        MediaAuditLog.objects.filter(id=log.id).update(
            created_at=timezone.now() - timedelta(days=age_days)
        )
        return log

    def test_purge_older_than_removes_only_expired(self):
        """Verify that purge_older_than deletes records past the threshold
        while preserving newer entries."""
        old = self._log(age_days=400)
        recent = self._log(age_days=10)

        removed = MediaAuditLog.objects.purge_older_than(
            timezone.now() - timedelta(days=365)
        )

        self.assertEqual(removed, 1)
        self.assertFalse(MediaAuditLog.objects.filter(id=old.id).exists())
        self.assertTrue(MediaAuditLog.objects.filter(id=recent.id).exists())

    @override_settings(MEDIA_AUDIT_LOG_RETENTION_DAYS=365)
    def test_purge_command_deletes_expired_entries(self):
        """Verify that purge_audit_logs purges records according to
        MEDIA_AUDIT_LOG_RETENTION_DAYS setting."""
        self._log(age_days=400)
        self._log(age_days=10)

        call_command("purge_audit_logs")

        self.assertEqual(MediaAuditLog.objects.count(), 1)

    @override_settings(MEDIA_AUDIT_LOG_RETENTION_DAYS=365)
    def test_purge_command_dry_run_keeps_entries(self):
        """Verify that purge_audit_logs --dry-run previews deletions
        without removing records from the database."""
        self._log(age_days=400)

        call_command("purge_audit_logs", "--dry-run")

        self.assertEqual(MediaAuditLog.objects.count(), 1)

    @override_settings(MEDIA_AUDIT_LOG_RETENTION_DAYS=0)
    def test_purge_command_disabled_keeps_all(self):
        """Verify that setting MEDIA_AUDIT_LOG_RETENTION_DAYS
        to 0 disables log purging."""
        self._log(age_days=400)

        call_command("purge_audit_logs")

        self.assertEqual(MediaAuditLog.objects.count(), 1)
