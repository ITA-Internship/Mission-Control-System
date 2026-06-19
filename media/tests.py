from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import MilitaryUnit
from drones.models import Drone, DroneModel
from media.models import VideoMetadata
from missions.factories import (
    AdminUserFactory,
    DispatcherUserFactory,
    MissionFactory,
    MissionDroneFactory,
    OperatorUserFactory,
    ViewerUserFactory,
)
from missions.models import Mission, MissionAuditLog

from .factories import MissionArtifactFactory
from .models import MissionArtifact
from .services import delete_artifact, upload_artifact

User = get_user_model()


class VideoMetadataAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="operator_travis",
            email="travis@example.com",
            password="securepassword123",
        )
        self.mission = Mission.objects.create(title="Test Mission Alpha")
        self.other_mission = Mission.objects.create(title="Test Mission Beta")
        self.military_unit = MilitaryUnit.objects.create(id=1, name="Unit 101")
        self.drone_model = DroneModel.objects.create(
            name="Mavic 3 Pro",
            manufacturer="DJI",
            supported_classifications=["RECONNAISSANCE", "SURVEILLANCE"],
        )

        drones_to_create = [
            Drone(
                id=1,
                name="Mavic Alpha",
                serial_number="SN-MAVIC-001",
                inventory_number="INV-DRONE-001",
                drone_model=self.drone_model,
                classification="RECONNAISSANCE",
                status="ACTIVE",
                military_unit=self.military_unit,
                acquired_at=timezone.localdate(),
            ),
            Drone(
                id=2,
                name="Mavic Beta",
                serial_number="SN-MAVIC-002",
                inventory_number="INV-DRONE-002",
                drone_model=self.drone_model,
                classification="SURVEILLANCE",
                status="ACTIVE",
                military_unit=self.military_unit,
                acquired_at=timezone.localdate(),
            ),
        ]
        Drone.objects.bulk_create(drones_to_create)
        self.drone = Drone.objects.get(id=1)
        self.other_drone = Drone.objects.get(id=2)
        MissionDroneFactory(mission=self.mission, drone=self.drone, operator=self.user)
        MissionDroneFactory(
            mission=self.other_mission, drone=self.other_drone, operator=self.user
        )

        self.video_file = SimpleUploadedFile(
            name="flight_video.mp4",
            content=b"fake_video_content_bytes",
            content_type="video/mp4",
        )
        self.list_url = reverse("video_media:video-metadata-list")
        self.client.force_authenticate(user=self.user)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    @patch("subprocess.run")
    def test_upload_video_metadata_success(self, mock_subproc, mock_perm):
        class MockResult:
            stdout = '{"format": {"duration": "42.0"}}'
            stderr = ""

        mock_subproc.return_value = MockResult()

        data = {
            "mission": self.mission.id,
            "drone": self.drone.id,
            "file": self.video_file,
            "checksum": "sha256_mock_hash_value",
            "recorded_at": timezone.now().isoformat(),
        }
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        video_from_db = VideoMetadata.objects.get(id=response.data["id"])
        self.assertEqual(video_from_db.duration_seconds, 42)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_requires_mission(self, mock_perm):
        data = {
            "drone": self.drone.id,
            "file": self.video_file,
        }
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mission", response.data)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_requires_drone(self, mock_perm):
        data = {
            "mission": self.mission.id,
            "file": self.video_file,
        }
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drone", response.data)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_rejects_unknown_mission(self, mock_perm):
        data = {
            "mission": 999999,
            "drone": self.drone.id,
            "file": self.video_file,
        }
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mission", response.data)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_rejects_unknown_drone(self, mock_perm):
        data = {
            "mission": self.mission.id,
            "drone": 999999,
            "file": self.video_file,
        }
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drone", response.data)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_rejects_drone_not_assigned_to_mission(
        self, mock_perm
    ):
        data = {
            "mission": self.mission.id,
            "drone": self.other_drone.id,
            "file": self.video_file,
        }
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["drone"][0],
            "Drone must be assigned to the selected mission.",
        )

    @patch("media.permissions.MediaViewPermission.has_permission", return_value=True)
    def test_get_video_metadata_list_with_pagination(self, mock_perm):
        VideoMetadata.objects.create(
            mission=self.mission,
            drone=self.drone,
            uploader=self.user,
            file=self.video_file,
            file_name="video_1.mp4",
            file_size=100,
        )

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)
        self.assertEqual(len(response.data["results"]), 1)

    @patch("media.permissions.MediaViewPermission.has_permission", return_value=True)
    def test_filter_video_metadata_by_mission(self, mock_perm):
        VideoMetadata.objects.create(
            mission=self.mission,
            drone=self.drone,
            uploader=self.user,
            file=self.video_file,
            file_name="video_1.mp4",
            file_size=100,
        )
        VideoMetadata.objects.create(
            mission=self.other_mission,
            drone=self.other_drone,
            uploader=self.user,
            file=self.video_file,
            file_name="video_2.mp4",
            file_size=200,
        )

        response = self.client.get(f"{self.list_url}?mission={self.mission.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["file_name"], "video_1.mp4")

    @patch("media.permissions.MediaViewPermission.has_permission", return_value=True)
    def test_filter_video_metadata_by_drone_alias(self, mock_perm):
        VideoMetadata.objects.create(
            mission=self.mission,
            drone=self.drone,
            uploader=self.user,
            file=self.video_file,
            file_name="video_1.mp4",
            file_size=100,
        )
        VideoMetadata.objects.create(
            mission=self.other_mission,
            drone=self.other_drone,
            uploader=self.user,
            file=SimpleUploadedFile(
                name="flight_video_4.mp4",
                content=b"fourth_fake_video_content_bytes",
                content_type="video/mp4",
            ),
            file_name="video_2.mp4",
            file_size=200,
        )

        response = self.client.get(f"{self.list_url}?drone={self.drone.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["file_name"], "video_1.mp4")

    @patch("media.permissions.MediaViewPermission.has_permission", return_value=True)
    def test_filter_video_metadata_by_drone_id(self, mock_perm):
        VideoMetadata.objects.create(
            mission=self.mission,
            drone=self.drone,
            uploader=self.user,
            file=self.video_file,
            file_name="video_1.mp4",
            file_size=100,
        )
        VideoMetadata.objects.create(
            mission=self.other_mission,
            drone=self.other_drone,
            uploader=self.user,
            file=SimpleUploadedFile(
                name="flight_video_2.mp4",
                content=b"other_fake_video_content_bytes",
                content_type="video/mp4",
            ),
            file_name="video_2.mp4",
            file_size=200,
        )

        response = self.client.get(f"{self.list_url}?drone_id={self.drone.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["file_name"], "video_1.mp4")

    @patch("media.permissions.MediaViewPermission.has_permission", return_value=True)
    def test_filter_video_metadata_by_mission_id_alias(self, mock_perm):
        VideoMetadata.objects.create(
            mission=self.mission,
            drone=self.drone,
            uploader=self.user,
            file=self.video_file,
            file_name="video_1.mp4",
            file_size=100,
        )
        VideoMetadata.objects.create(
            mission=self.other_mission,
            drone=self.other_drone,
            uploader=self.user,
            file=SimpleUploadedFile(
                name="flight_video_3.mp4",
                content=b"third_fake_video_content_bytes",
                content_type="video/mp4",
            ),
            file_name="video_2.mp4",
            file_size=200,
        )

        response = self.client.get(f"{self.list_url}?mission_id={self.mission.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["file_name"], "video_1.mp4")


@override_settings(
    ARTIFACT_ALLOWED_EXTENSIONS={
        "image": [".jpg", ".jpeg", ".png"],
        "video": [".mp4", ".avi", ".mov"],
        "data": [".json", ".csv", ".xml"],
    },
    ARTIFACT_MAX_FILE_SIZE_MB=10,
)
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


@override_settings(
    ARTIFACT_ALLOWED_EXTENSIONS={
        "image": [".jpg", ".jpeg", ".png"],
        "video": [".mp4", ".avi", ".mov"],
        "data": [".json", ".csv", ".xml"],
    },
    ARTIFACT_MAX_FILE_SIZE_MB=10,
)
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
        MissionArtifactFactory(is_image=True)

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
