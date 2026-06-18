from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from media.factories import MissionArtifactFactory
from media.models import MissionArtifact
from missions.factories import (
    AdminUserFactory,
    DispatcherUserFactory,
    MissionFactory,
    OperatorUserFactory,
    ViewerUserFactory,
)
from missions.models import MissionAuditLog


class ArtifactListCreateTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.dispatcher = DispatcherUserFactory()
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()

        self.mission = MissionFactory()
        self.url = reverse(
            "missions:media:artifact-list-create",
            kwargs={"mission_pk": self.mission.pk},
        )

    def get_valid_payload(self):
        file_content = b"test image content"
        upload_file = SimpleUploadedFile(
            "test.jpg", file_content, content_type="image/jpeg"
        )
        return {
            "title": "Test Artifact",
            "description": "Test description",
            "file": upload_file,
        }

    def test_operator_can_upload_artifact(self):
        self.client.force_authenticate(self.operator)
        payload = self.get_valid_payload()

        response = self.client.post(self.url, payload, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(MissionArtifact.objects.count(), 1)

        artifact = MissionArtifact.objects.get()
        self.assertEqual(artifact.title, "Test Artifact")
        self.assertEqual(artifact.uploaded_by, self.operator)
        self.assertEqual(artifact.mission, self.mission)
        self.assertEqual(artifact.file_type, "image")

    def test_admin_can_upload_artifact(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_dispatcher_can_upload_artifact(self):
        self.client.force_authenticate(self.dispatcher)
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_viewer_cannot_upload_artifact(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MissionArtifact.objects.count(), 0)

    def test_unauthenticated_cannot_upload(self):
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_creates_audit_log(self):
        self.client.force_authenticate(self.operator)
        self.client.post(self.url, self.get_valid_payload(), format="multipart")

        log = MissionAuditLog.objects.get(action="artifact_uploaded")
        self.assertEqual(log.target_model, "MissionArtifact")
        self.assertEqual(log.user, self.operator)
        self.assertEqual(log.changes["mission_id"], self.mission.id)
        self.assertEqual(log.changes["title"], "Test Artifact")

    def test_missing_file_rejected(self):
        self.client.force_authenticate(self.operator)
        payload = {"title": "No File"}
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_empty_file_rejected(self):
        self.client.force_authenticate(self.operator)
        payload = self.get_valid_payload()
        payload["file"] = SimpleUploadedFile("empty.jpg", b"")
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_unsupported_file_extension_rejected(self):
        self.client.force_authenticate(self.operator)
        payload = self.get_valid_payload()
        payload["file"] = SimpleUploadedFile("bad.xyz", b"content")
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    @override_settings(ARTIFACT_MAX_FILE_SIZE_MB=0)
    def test_file_too_large_rejected(self):
        self.client.force_authenticate(self.operator)
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_list_artifacts_for_mission(self):
        MissionArtifactFactory(mission=self.mission, is_image=True)
        MissionArtifactFactory(mission=self.mission, is_video=True)
        MissionArtifactFactory(mission=self.mission, is_data=True)
        MissionArtifactFactory(is_image=True)  # Different mission

        self.client.force_authenticate(self.viewer)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)
        file_types = {item["file_type"] for item in response.data["results"]}
        self.assertEqual(file_types, {"image", "video", "data"})

    def test_unauthenticated_cannot_list(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ArtifactDetailTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.dispatcher = DispatcherUserFactory()
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()

        self.mission = MissionFactory()
        self.artifact = MissionArtifactFactory(
            mission=self.mission, uploaded_by=self.operator, is_image=True
        )
        self.url = reverse(
            "missions:media:artifact-detail",
            kwargs={"mission_pk": self.mission.pk, "artifact_pk": self.artifact.pk},
        )

    def test_viewer_can_retrieve(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.artifact.id)

    def test_unauthenticated_cannot_retrieve(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete(self):
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MissionArtifact.objects.filter(id=self.artifact.id).exists())

    def test_operator_cannot_delete(self):
        self.client.force_authenticate(self.operator)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MissionArtifact.objects.filter(id=self.artifact.id).exists())

    def test_dispatcher_cannot_delete(self):
        self.client.force_authenticate(self.dispatcher)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MissionArtifact.objects.filter(id=self.artifact.id).exists())

    def test_viewer_cannot_delete(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MissionArtifact.objects.filter(id=self.artifact.id).exists())

    def test_delete_creates_audit_log(self):
        self.client.force_authenticate(self.admin)
        self.client.delete(self.url)

        log = MissionAuditLog.objects.get(action="artifact_deleted")
        self.assertEqual(log.target_model, "MissionArtifact")
        self.assertEqual(log.user, self.admin)
        self.assertEqual(log.changes["mission_id"], self.mission.id)
        self.assertEqual(
            log.changes["original_filename"], self.artifact.original_filename
        )

    @patch("django.core.files.storage.default_storage.delete")
    def test_delete_removes_file_from_storage(self, mock_delete):
        self.client.force_authenticate(self.admin)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_delete.assert_called_once()

    def test_delete_wrong_mission_returns_404(self):
        other_mission = MissionFactory()
        bad_url = reverse(
            "missions:media:artifact-detail",
            kwargs={"mission_pk": other_mission.pk, "artifact_pk": self.artifact.pk},
        )

        self.client.force_authenticate(self.admin)
        response = self.client.delete(bad_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
