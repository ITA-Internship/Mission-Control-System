from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from missions.factories import (
    AdminUserFactory,
    DispatcherUserFactory,
    MissionFactory,
    OperatorUserFactory,
    ViewerUserFactory,
)
from missions.models import MissionAuditLog

from .factories import MissionArtifactFactory
from .models import MediaAuditLog, MissionArtifact
from .services import delete_artifact, upload_artifact


class MissionArtifactModelTests(TestCase):
    def test_str_representation(self):
        mission = MissionFactory()
        artifact = MissionArtifactFactory(
            title="Drone Footage", is_video=True, mission=mission
        )
        self.assertEqual(
            str(artifact), f"Drone Footage (video) — Mission #{mission.id}"
        )

    def test_auto_fields_on_save(self):
        file_content = b"test content"
        upload_file = SimpleUploadedFile(
            "test_auto.jpg", file_content, content_type="image/jpeg"
        )

        artifact = MissionArtifactFactory.build(
            file=upload_file,
            file_type="",
            file_size=None,
            original_filename="",
            mission=MissionFactory(),
            uploaded_by=OperatorUserFactory(),
        )

        artifact.save()

        self.assertEqual(artifact.file_size, len(file_content))
        self.assertEqual(artifact.file_type, "image")
        self.assertEqual(artifact.original_filename, "test_auto.jpg")
        self.assertEqual(artifact.storage_backend, "local")

    def test_clean_validates_blank_title(self):
        artifact = MissionArtifactFactory.build(title="   ", is_image=True)
        with self.assertRaises(ValidationError) as context:
            artifact.clean()
        self.assertIn("title", context.exception.message_dict)

    @override_settings(ARTIFACT_ALLOWED_EXTENSIONS={"video": [".mp4"]})
    def test_unsupported_extension_raises_validation_error(self):
        file_content = b"test data"
        upload_file = SimpleUploadedFile("test.xyz", file_content)
        artifact = MissionArtifactFactory.build(
            file=upload_file,
            mission=MissionFactory(),
            uploaded_by=OperatorUserFactory(),
        )

        with self.assertRaises(ValidationError) as context:
            artifact.full_clean()

        self.assertTrue(
            any(
                "extension" in str(e).lower()
                for e in context.exception.error_dict.get("file", [])
            )
        )

    def test_empty_file_raises_validation_error(self):
        upload_file = SimpleUploadedFile("empty.jpg", b"")
        artifact = MissionArtifactFactory.build(file=upload_file)

        with self.assertRaises(ValidationError):
            artifact.file.field.clean(upload_file, artifact)


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


class MediaAuditLoggingTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()
        self.mission = MissionFactory()
        self.artifact = MissionArtifactFactory(
            mission=self.mission, uploaded_by=self.operator, is_video=True
        )
        self.detail_url = reverse(
            "missions:media:artifact-detail",
            kwargs={"mission_pk": self.mission.pk, "artifact_pk": self.artifact.pk},
        )
        self.list_url = reverse(
            "missions:media:artifact-list-create",
            kwargs={"mission_pk": self.mission.pk},
        )

    def get_valid_payload(self):
        upload_file = SimpleUploadedFile(
            "clip.mp4", b"video bytes", content_type="video/mp4"
        )
        return {"title": "Mission Clip", "file": upload_file}

    def test_retrieve_logs_view_action_with_user_and_ip(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        log = MediaAuditLog.objects.get(action=MediaAuditLog.Action.VIEW)
        self.assertEqual(log.user, self.viewer)
        self.assertEqual(log.artifact, self.artifact)
        self.assertEqual(log.mission_id, self.mission.id)
        self.assertEqual(log.ip_address, "127.0.0.1")

    def test_each_retrieve_creates_a_separate_view_log(self):
        self.client.force_authenticate(self.viewer)
        self.client.get(self.detail_url)
        self.client.get(self.detail_url)

        self.assertEqual(
            MediaAuditLog.objects.filter(action=MediaAuditLog.Action.VIEW).count(), 2
        )

    def test_view_logging_failure_does_not_break_retrieve(self):
        self.client.force_authenticate(self.viewer)
        with patch(
            "media.services.MediaAuditLog.objects.create",
            side_effect=RuntimeError("logging down"),
        ):
            response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_upload_writes_to_both_audit_logs(self):
        self.client.force_authenticate(self.operator)
        response = self.client.post(
            self.list_url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        artifact_id = response.data["id"]

        media_log = MediaAuditLog.objects.get(action=MediaAuditLog.Action.UPLOAD)
        self.assertEqual(media_log.user, self.operator)
        self.assertEqual(media_log.artifact_id, artifact_id)
        self.assertEqual(media_log.mission_id, self.mission.id)
        self.assertEqual(media_log.changes["title"], "Mission Clip")

        self.assertTrue(
            MissionAuditLog.objects.filter(
                action="artifact_uploaded", target_id=artifact_id
            ).exists()
        )

    def test_delete_writes_to_both_audit_logs(self):
        self.client.force_authenticate(self.admin)

        with self.captureOnCommitCallbacks(execute=True):
            with patch("django.core.files.storage.default_storage.delete"):
                response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        media_log = MediaAuditLog.objects.get(action=MediaAuditLog.Action.DELETE)
        self.assertEqual(media_log.user, self.admin)
        self.assertEqual(media_log.mission_id, self.mission.id)
        # Artifact FK is nulled by SET_NULL once the artifact row is deleted,
        # but the reference is preserved in `changes`.
        self.assertIsNone(media_log.artifact)
        self.assertEqual(media_log.changes["artifact_id"], self.artifact.id)

        self.assertTrue(
            MissionAuditLog.objects.filter(action="artifact_deleted").exists()
        )


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
            upload_file = SimpleUploadedFile("clip.mp4", b"video bytes")

            with self.assertRaises(RuntimeError):
                upload_artifact(
                    mission=self.mission,
                    file=upload_file,
                    title="Rollback Clip",
                    uploaded_by=self.operator,
                )

            mock_delete.assert_called_once()

        # The whole atomic block is rolled back: no artifact and no logs.
        self.assertEqual(MissionArtifact.objects.count(), 0)
        self.assertEqual(MissionAuditLog.objects.count(), 0)
        self.assertEqual(MediaAuditLog.objects.count(), 0)


class MediaAuditLogEndpointTests(APITestCase):
    def setUp(self):
        self.admin = AdminUserFactory()
        self.dispatcher = DispatcherUserFactory()
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()

        self.mission = MissionFactory()
        self.other_mission = MissionFactory()
        self.artifact = MissionArtifactFactory(mission=self.mission, is_video=True)

        self.view_log = MediaAuditLog.objects.create(
            user=self.operator,
            artifact=self.artifact,
            mission=self.mission,
            action=MediaAuditLog.Action.VIEW,
            ip_address="127.0.0.1",
        )
        self.upload_log = MediaAuditLog.objects.create(
            user=self.operator,
            artifact=self.artifact,
            mission=self.mission,
            action=MediaAuditLog.Action.UPLOAD,
        )
        self.other_mission_log = MediaAuditLog.objects.create(
            user=self.admin,
            mission=self.other_mission,
            action=MediaAuditLog.Action.VIEW,
        )

        self.url = reverse("media-audit-log-list")

    def test_admin_can_list_logs(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_operator_cannot_list_logs(self):
        self.client.force_authenticate(self.operator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_list_logs(self):
        self.client.force_authenticate(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dispatcher_cannot_list_logs(self):
        self.client.force_authenticate(self.dispatcher)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_logs(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_action(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"action": MediaAuditLog.Action.UPLOAD})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.upload_log.id)

    def test_filter_by_mission(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"mission": self.other_mission.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.other_mission_log.id)

    def test_filter_by_user(self):
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"user": self.operator.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_admin_can_retrieve_log_detail(self):
        self.client.force_authenticate(self.admin)
        detail_url = reverse("media-audit-log-detail", kwargs={"pk": self.view_log.id})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.view_log.id)
        self.assertEqual(response.data["action"], MediaAuditLog.Action.VIEW)

    def test_endpoint_is_read_only(self):
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.url, {"action": "view"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
