from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from media.factories import MissionArtifactFactory
from media.models import MediaAuditLog, MissionArtifact
from media.services import delete_artifact, upload_artifact
from missions.factories import MissionFactory, OperatorUserFactory
from missions.models import MissionAuditLog


class ArtifactServicesTests(TestCase):
    def setUp(self):
        self.operator = OperatorUserFactory()
        self.mission = MissionFactory()

    @patch("django.core.files.storage.default_storage.delete")
    def test_upload_artifact_exception_cleans_up_storage(self, mock_delete):
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
        artifact = MissionArtifactFactory(mission=self.mission, is_image=True)

        with patch("django.core.files.storage.default_storage.delete") as mock_delete:
            with self.captureOnCommitCallbacks(execute=True):
                delete_artifact(artifact=artifact, action_user=self.operator)

            mock_delete.assert_called_once()

        self.assertFalse(MissionArtifact.objects.filter(id=artifact.id).exists())


class MediaAuditLogTransactionTests(TestCase):
    def setUp(self):
        self.operator = OperatorUserFactory()
        self.mission = MissionFactory()

    @patch("django.core.files.storage.default_storage.delete")
    def test_media_audit_log_failure_rolls_back_upload(self, mock_delete):
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