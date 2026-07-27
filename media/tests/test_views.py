"""Test suite for mission artifact, video metadata and audit log views."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import MilitaryUnit
from drones.models import Drone, DroneModel
from media.factories import MissionArtifactFactory
from media.models import MediaAuditLog, MissionArtifact, VideoMetadata
from media.tasks import extract_video_duration_task
from missions.factories import (
    AdminUserFactory,
    DispatcherUserFactory,
    MissionDroneFactory,
    MissionFactory,
    OperatorUserFactory,
    ViewerUserFactory,
)
from missions.models import Mission, MissionAuditLog

User = get_user_model()


class VideoMetadataAPITests(APITestCase):
    """Test VideoMetadata API endpoints and browser UI views."""

    def setUp(self):
        """Set up a user, missions, drones, military unit
        and video file for testing."""
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

    @patch("media.views.extract_video_duration_task.delay")
    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    @patch("subprocess.run")
    def test_upload_video_metadata_success(self, mock_subproc, mock_perm, mock_delay):
        """Verify successful video metadata creation
        and synchronous execution of duration extraction."""
        mock_delay.side_effect = extract_video_duration_task

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
        self.assertEqual(video_from_db.status, VideoMetadata.Status.READY)

    @patch("media.views.extract_video_duration_task.delay")
    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_starts_in_uploading_status(
        self,
        mock_perm,
        mock_delay,
    ):
        """Verify that video metadata initializes with
        UPLOADING status before async tasks run."""
        data = {
            "mission": self.mission.id,
            "drone": self.drone.id,
            "file": self.video_file,
            "checksum": "sha256_mock_hash_value",
        }

        response = self.client.post(self.list_url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        video_from_db = VideoMetadata.objects.get(id=response.data["id"])
        self.assertEqual(video_from_db.status, VideoMetadata.Status.UPLOADING)
        mock_delay.assert_called_once_with(video_from_db.id)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_requires_mission(self, mock_perm):
        """Verify that video metadata creation fails
        when mission parameter is missing."""
        data = {
            "drone": self.drone.id,
            "file": self.video_file,
        }
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("mission", response.data)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_requires_drone(self, mock_perm):
        """Verify that video metadata creation fails when drone parameter is missing."""
        data = {
            "mission": self.mission.id,
            "file": self.video_file,
        }
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("drone", response.data)

    @patch("media.permissions.MediaUploadPermission.has_permission", return_value=True)
    def test_upload_video_metadata_rejects_unknown_mission(self, mock_perm):
        """Verify that video metadata creation fails
        when provided with a non-existent mission primary key."""
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
        """Verify that video metadata creation fails
        when provided with a non-existent drone primary key."""
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
        """Verify validation rules enforcing that selected drones
        must belong to the target mission."""
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
        """Verify that a GET list endpoint responds with standard paginated response."""
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
        """Verify FilterSet filtering using ?mission=<id> query parameter."""
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
        """Verify FilterSet filtering using the ?drone=<id> query parameter."""
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
        """Verify FilterSet filtering using explicit drone primary key matching."""
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

        response = self.client.get(f"{self.list_url}?drone={self.drone.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["file_name"], "video_1.mp4")

    @patch("media.permissions.MediaViewPermission.has_permission", return_value=True)
    def test_filter_video_metadata_by_mission_id_alias(self, mock_perm):
        """Verify FilterSet lookup when filtering by mission foreign key aliases."""
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

        response = self.client.get(f"{self.list_url}?mission={self.mission.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["file_name"], "video_1.mp4")

    @patch("media.permissions.MediaViewPermission.has_permission", return_value=True)
    def test_video_browser_page_renders_filtered_results(self, mock_perm):
        """Verify HTML browser template rendering and server-side filtering."""
        self.client.force_login(self.user)
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
                name="flight_video_browser.mp4",
                content=b"browser_fake_video_content_bytes",
                content_type="video/mp4",
            ),
            file_name="video_2.mp4",
            file_size=200,
        )

        browser_url = reverse("video_media:video-browser")
        response = self.client.get(f"{browser_url}?mission_id={self.mission.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "Mission Videos")
        self.assertContains(response, "video_1.mp4")
        self.assertNotContains(response, "video_2.mp4")

    @patch("media.permissions.MediaViewPermission.has_permission", return_value=True)
    def test_list_scopes_videos_to_callers_unit(self, mock_perm):
        # Regression for C3: a non-admin caller with a unit must see only their
        # own uploads plus videos captured by a drone in their own unit — never
        # every video system-wide — and the unit-scoped query must resolve (the
        # video's unit is reached via drone__military_unit, not the mission).
        self.user.unit = self.military_unit  # Unit 101; owns self.drone
        self.user.save(update_fields=["unit"])

        other_unit = MilitaryUnit.objects.create(id=2, name="Unit 202", code="U202")
        foreign_drone = Drone.objects.create(
            id=3,
            name="Mavic Gamma",
            serial_number="SN-MAVIC-003",
            inventory_number="INV-DRONE-003",
            drone_model=self.drone_model,
            classification="RECONNAISSANCE",
            status="ACTIVE",
            military_unit=other_unit,
            acquired_at=timezone.localdate(),
        )
        someone_else = OperatorUserFactory()

        # Captured by a drone in the caller's unit, uploaded by someone else:
        # visible via the unit branch, not the uploader branch.
        VideoMetadata.objects.create(
            mission=self.mission,
            drone=self.drone,
            uploader=someone_else,
            file=SimpleUploadedFile("in_unit.mp4", b"a", content_type="video/mp4"),
            file_name="in_unit.mp4",
            file_size=10,
        )
        # Captured by a drone in a foreign unit: must be excluded.
        VideoMetadata.objects.create(
            mission=self.other_mission,
            drone=foreign_drone,
            uploader=someone_else,
            file=SimpleUploadedFile("foreign.mp4", b"b", content_type="video/mp4"),
            file_name="foreign.mp4",
            file_size=20,
        )

        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = {video["file_name"] for video in response.data["results"]}
        self.assertEqual(names, {"in_unit.mp4"})


@override_settings(
    ARTIFACT_ALLOWED_EXTENSIONS={
        "image": [".jpg", ".jpeg", ".png"],
        "video": [".mp4", ".avi", ".mov"],
        "data": [".json", ".csv", ".xml"],
    },
    ARTIFACT_MAX_FILE_SIZE_MB=10,
)
class ArtifactListCreateTests(APITestCase):
    """Test artifact creation and list endpoints."""

    def setUp(self):
        """Set up users with admin, dispatcher, operator and viewer roles,
        and a mission for testing."""
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
        """Returning a valid upload payload with dummy image bytes."""
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
        """Verify that users with Operator role
        can successfully upload a valid artifact."""
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
        """Verify that users with Admin role
        can successfully upload a valid artifact."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_dispatcher_can_upload_artifact(self):
        """Verify that users with Dispatcher role
        can successfully upload a valid artifact."""
        self.client.force_authenticate(self.dispatcher)
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_viewer_cannot_upload_artifact(self):
        """Ensure that users with Viewer role cannot upload a valid artifact."""
        self.client.force_authenticate(self.viewer)
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(MissionArtifact.objects.count(), 0)

    def test_unauthenticated_cannot_upload(self):
        """Ensure that unauthenticated users cannot upload a valid artifact."""
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_creates_audit_log(self):
        """Verify that successful upload automatically generates
        a mission audit log entry."""
        self.client.force_authenticate(self.operator)
        self.client.post(self.url, self.get_valid_payload(), format="multipart")

        log = MissionAuditLog.objects.get(action="artifact_uploaded")
        self.assertEqual(log.target_model, "MissionArtifact")
        self.assertEqual(log.user, self.operator)
        self.assertEqual(log.changes["mission_id"], self.mission.id)
        self.assertEqual(log.changes["title"], "Test Artifact")

    def test_missing_file_rejected(self):
        """Verify that artifact creation fails
        when upload payload lacks the file field."""
        self.client.force_authenticate(self.operator)
        payload = {"title": "No File"}
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_empty_file_rejected(self):
        """Verify rejection of zero-byte file uploads."""
        self.client.force_authenticate(self.operator)
        payload = self.get_valid_payload()
        payload["file"] = SimpleUploadedFile("empty.jpg", b"")
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_unsupported_file_extension_rejected(self):
        """Verify field validation error when uploaded file extension
        that is not explicitly allowed."""
        self.client.force_authenticate(self.operator)
        payload = self.get_valid_payload()
        payload["file"] = SimpleUploadedFile("bad.xyz", b"content")
        response = self.client.post(self.url, payload, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    @override_settings(ARTIFACT_MAX_FILE_SIZE_MB=0)
    def test_file_too_large_rejected(self):
        """Verify max file size limit enforcement via setting override."""
        self.client.force_authenticate(self.operator)
        response = self.client.post(
            self.url, self.get_valid_payload(), format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_list_artifacts_for_mission(self):
        """Verify listing artifacts filters by the target mission_pk."""
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
        """Verify that unauthenticated users cannot list artifacts."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ArtifactDetailTests(APITestCase):
    """Test artifact detail endpoint."""

    def setUp(self):
        """Set up users with admin, dispatcher, operator and viewer roles,
        a mission and an artifact for testing."""
        self.admin = AdminUserFactory()
        self.dispatcher = DispatcherUserFactory()
        self.operator = OperatorUserFactory()
        self.assigned_operator = OperatorUserFactory()
        self.unrelated_operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()

        self.mission = MissionFactory()
        MissionDroneFactory(mission=self.mission, operator=self.assigned_operator)
        self.artifact = MissionArtifactFactory(
            mission=self.mission, uploaded_by=self.operator, is_image=True
        )
        self.url = reverse(
            "missions:media:artifact-detail",
            kwargs={"mission_pk": self.mission.pk, "artifact_pk": self.artifact.pk},
        )
        self.download_url = reverse(
            "missions:media:artifact-download",
            kwargs={"mission_pk": self.mission.pk, "artifact_pk": self.artifact.pk},
        )

    def test_viewer_cannot_retrieve(self):
        """Verify that user with Viewer role
        cannot retrieve detail records for an artifact."""
        self.client.force_authenticate(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_uploaded_by_can_retrieve(self):
        """Verify that user who uploaded the artifact can retrieve its details."""
        self.client.force_authenticate(self.operator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.artifact.id)

    def test_assigned_operator_can_retrieve(self):
        """Verify that an operator assigned to the mission can retrieve an artifact."""
        self.client.force_authenticate(self.assigned_operator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.artifact.id)

    def test_commander_can_retrieve(self):
        """Verify that the mission commander can retrieve an artifact."""
        self.client.force_authenticate(self.mission.commander)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.artifact.id)

    def test_created_by_can_retrieve(self):
        """Verify that the creator of the mission can retrieve the artifact."""
        self.client.force_authenticate(self.mission.created_by)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.artifact.id)

    def test_unrelated_operator_without_unit_cannot_retrieve_artifact(self):
        """Verify that an unassigned operator without a unit
        cannot retrieve artifact details."""
        self.assertIsNone(self.unrelated_operator.unit_id)
        self.client.force_authenticate(self.unrelated_operator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unrelated_operator_without_unit_cannot_download_artifact(self):
        """Verify that an unassigned operator without a unit
        cannot download the artifact file."""
        self.assertIsNone(self.unrelated_operator.unit_id)
        self.client.force_authenticate(self.unrelated_operator)
        response = self.client.get(self.download_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_retrieve(self):
        """Verify that unauthenticated user cannot retrieve
        detail records for an artifact."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete(self):
        """Verify that user with Admin role have permission
        to delete artifact records."""
        self.client.force_authenticate(self.admin)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(MissionArtifact.objects.filter(id=self.artifact.id).exists())

    def test_operator_cannot_delete(self):
        """Verify RBAC rule blocking Operators from deleting artifacts."""
        self.client.force_authenticate(self.operator)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MissionArtifact.objects.filter(id=self.artifact.id).exists())

    def test_dispatcher_cannot_delete(self):
        """Verify RBAC rule blocking Dispatchers from deleting artifacts."""
        self.client.force_authenticate(self.dispatcher)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MissionArtifact.objects.filter(id=self.artifact.id).exists())

    def test_viewer_cannot_delete(self):
        """Verify RBAC rule blocking Viewers from deleting artifacts."""
        self.client.force_authenticate(self.viewer)
        response = self.client.delete(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(MissionArtifact.objects.filter(id=self.artifact.id).exists())

    def test_delete_creates_audit_log(self):
        """Verify that deletion generates a mission audit log entry."""
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
        """Verify that physical storage cleanup triggers
        on transaction commit after DB row removal."""
        self.client.force_authenticate(self.admin)

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.delete(self.url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        mock_delete.assert_called_once()

    def test_delete_wrong_mission_returns_404(self):
        """Verify 404 Not Found response when targeting an artifact
        with a mismatched mission_pk."""
        other_mission = MissionFactory()
        bad_url = reverse(
            "missions:media:artifact-detail",
            kwargs={"mission_pk": other_mission.pk, "artifact_pk": self.artifact.pk},
        )

        self.client.force_authenticate(self.admin)
        response = self.client.delete(bad_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MediaAuditLoggingTests(APITestCase):
    """Test dual-write audit logging behavior."""

    def setUp(self):
        """Set up users with admin, dispatcher, operator and viewer roles,
        a mission and an artifact for testing."""
        self.admin = AdminUserFactory()
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()
        self.mission = MissionFactory()
        self.artifact = MissionArtifactFactory(
            mission=self.mission, uploaded_by=self.operator, is_image=True
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
        """Return a valid file payload for upload testing."""
        upload_file = SimpleUploadedFile(
            "clip.jpg", b"image bytes", content_type="image/jpeg"
        )
        return {"title": "Mission Clip", "file": upload_file}

    def test_retrieve_logs_view_action_with_user_and_ip(self):
        """Verify retrieving artifact details creates
        a media audit log entry with IP address."""
        self.client.force_authenticate(self.operator)
        response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        log = MediaAuditLog.objects.get(action=MediaAuditLog.Action.VIEW)
        self.assertEqual(log.user, self.operator)
        self.assertEqual(log.artifact, self.artifact)
        self.assertEqual(log.mission_id, self.mission.id)
        self.assertEqual(log.ip_address, "127.0.0.1")

    def test_each_retrieve_creates_a_separate_view_log(self):
        """Verify that multiple read accesses log distinct view records."""
        self.client.force_authenticate(self.operator)
        self.client.get(self.detail_url)
        self.client.get(self.detail_url)

        self.assertEqual(
            MediaAuditLog.objects.filter(action=MediaAuditLog.Action.VIEW).count(), 2
        )

    def test_view_logging_failure_does_not_break_retrieve(self):
        """Verify that failures in audit log creation
        do not fail the API read response."""
        self.client.force_authenticate(self.operator)
        with patch(
            "media.services.MediaAuditLog.objects.create",
            side_effect=RuntimeError("logging down"),
        ):
            response = self.client.get(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_upload_writes_to_both_audit_logs(self):
        """Verify dual-write behavior creating both
        media and mission audit logs on upload."""
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
        """Verify dual-write audit logs occur during deletion
        retaining snapshot data."""
        self.client.force_authenticate(self.admin)

        with self.captureOnCommitCallbacks(execute=True):
            with patch("django.core.files.storage.default_storage.delete"):
                response = self.client.delete(self.detail_url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        media_log = MediaAuditLog.objects.get(action=MediaAuditLog.Action.DELETE)
        self.assertEqual(media_log.user, self.admin)
        self.assertEqual(media_log.mission_id, self.mission.id)
        self.assertIsNone(media_log.artifact)
        self.assertEqual(media_log.changes["artifact_id"], self.artifact.id)

        self.assertTrue(
            MissionAuditLog.objects.filter(action="artifact_deleted").exists()
        )


class MediaAuditLogEndpointTests(APITestCase):
    """Test behaviour of a read-only media audit log endpoint."""

    def setUp(self):
        """Set up users with admin, dispatcher, operator and viewer roles,
        missions, an artifact and audit log entries for testing."""
        self.admin = AdminUserFactory()
        self.dispatcher = DispatcherUserFactory()
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()

        self.mission = MissionFactory()
        self.other_mission = MissionFactory()
        self.artifact = MissionArtifactFactory(mission=self.mission, is_image=True)

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
        """Verify that admin can list the audit logs."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 3)

    def test_operator_cannot_list_logs(self):
        """Ensure that operator cannot list audit logs."""
        self.client.force_authenticate(self.operator)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_viewer_cannot_list_logs(self):
        """Ensure that viewer cannot list audit logs."""
        self.client.force_authenticate(self.viewer)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dispatcher_cannot_list_logs(self):
        """Ensure that dispatcher cannot list audit logs."""
        self.client.force_authenticate(self.dispatcher)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_logs(self):
        """Ensure that unauthenticated users cannot list audit logs."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_filter_by_action(self):
        """Verify filtering audit logs by action type."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"action": MediaAuditLog.Action.UPLOAD})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.upload_log.id)

    def test_filter_by_mission(self):
        """Verify filtering audit logs by target mission."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"mission": self.other_mission.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], self.other_mission_log.id)

    def test_filter_by_user(self):
        """Verify filtering audit logs by responsible actor."""
        self.client.force_authenticate(self.admin)
        response = self.client.get(self.url, {"user": self.operator.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_admin_can_retrieve_log_detail(self):
        """Verify that admin can retrieve a specific
        audit log detail record by primary key."""
        self.client.force_authenticate(self.admin)
        detail_url = reverse("media-audit-log-detail", kwargs={"pk": self.view_log.id})
        response = self.client.get(detail_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.view_log.id)
        self.assertEqual(response.data["action"], MediaAuditLog.Action.VIEW)

    def test_endpoint_is_read_only(self):
        """Ensure that HTTP POST requests are rejected
        with 405 Method Not Allowed to preserve log immutability."""
        self.client.force_authenticate(self.admin)
        response = self.client.post(self.url, {"action": "view"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)


class ProtectedMediaDownloadTests(APITestCase):
    """Test secure media download endpoints."""

    def setUp(self):
        """Set up users with admin and operator roles,
        missions, artifacts for testing."""
        self.admin = AdminUserFactory()
        self.operator = OperatorUserFactory()
        self.mission = MissionFactory()
        self.other_mission = MissionFactory()
        self.artifact = MissionArtifactFactory(
            mission=self.mission, uploaded_by=self.operator, is_image=True
        )
        self.url = reverse(
            "missions:media:artifact-download",
            kwargs={"mission_pk": self.mission.pk, "artifact_pk": self.artifact.pk},
        )

    @override_settings(DEBUG=True)
    def test_download_logs_download_action_with_user_and_ip(self):
        """Verify that downloading an artifact creates
        a media audit log entry with user and IP."""
        self.client.force_authenticate(self.operator)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        log = MediaAuditLog.objects.get(action=MediaAuditLog.Action.DOWNLOAD)
        self.assertEqual(log.user, self.operator)
        self.assertEqual(log.artifact, self.artifact)
        self.assertEqual(log.mission_id, self.mission.id)
        self.assertEqual(log.ip_address, "127.0.0.1")

    @override_settings(DEBUG=True)
    def test_download_logging_failure_does_not_break_download(self):
        """Verify that audit log creation errors do not break
        file download responses."""
        self.client.force_authenticate(self.admin)
        with patch(
            "media.services.MediaAuditLog.objects.create",
            side_effect=RuntimeError("logging down"),
        ):
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_wrong_mission_returns_404(self):
        """Verify 404 Not Found response when requesting
        an artifact with a mismatched mission ID."""
        wrong_mission_url = reverse(
            "missions:media:artifact-download",
            kwargs={
                "mission_pk": self.other_mission.pk,
                "artifact_pk": self.artifact.pk,
            },
        )

        self.client.force_authenticate(self.admin)
        response = self.client.get(wrong_mission_url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MediaPermissionDeniedLoggingTests(APITestCase):
    """Test recording of PERMISSION_DENIED events in media audit log."""

    def setUp(self):
        """Set up users with operator and viewer roles,
        a mission and an artifact for testing."""
        self.operator = OperatorUserFactory()
        self.viewer = ViewerUserFactory()
        self.mission = MissionFactory()
        self.artifact = MissionArtifactFactory(
            mission=self.mission, uploaded_by=self.operator, is_image=True
        )
        self.list_url = reverse(
            "missions:media:artifact-list-create",
            kwargs={"mission_pk": self.mission.pk},
        )
        self.detail_url = reverse(
            "missions:media:artifact-detail",
            kwargs={"mission_pk": self.mission.pk, "artifact_pk": self.artifact.pk},
        )

    def test_denied_upload_logs_permission_denied(self):
        """Verify that an unauthorized upload attempt logs
        a PERMISSION_DENIED audit entry."""
        self.client.force_authenticate(self.viewer)
        upload_file = SimpleUploadedFile(
            "x.jpg", b"image bytes", content_type="image/jpeg"
        )
        response = self.client.post(
            self.list_url, {"title": "x", "file": upload_file}, format="multipart"
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        log = MediaAuditLog.objects.get(action=MediaAuditLog.Action.PERMISSION_DENIED)
        self.assertEqual(log.user, self.viewer)
        self.assertEqual(log.changes["reason"], "missing_required_permission")
        self.assertEqual(log.changes["method"], "POST")

    def test_denied_delete_logs_permission_denied(self):
        """Verify that an unauthorized delete attempt logs
        a PERMISSION_DENIED audit entry."""
        self.client.force_authenticate(self.viewer)
        response = self.client.delete(self.detail_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        log = MediaAuditLog.objects.get(action=MediaAuditLog.Action.PERMISSION_DENIED)
        self.assertEqual(log.user, self.viewer)
        self.assertIsNone(log.artifact)
        self.assertEqual(log.changes["reason"], "missing_required_permission")
        self.assertEqual(log.changes["method"], "DELETE")

    def test_permission_denied_logging_failure_does_not_break_response(self):
        """Verify that failures in recording access denial
        do not alter HTTP 403 status."""
        self.client.force_authenticate(self.viewer)
        upload_file = SimpleUploadedFile(
            "x.jpg", b"image bytes", content_type="image/jpeg"
        )
        with patch(
            "media.services.MediaAuditLog.objects.create",
            side_effect=RuntimeError("logging down"),
        ):
            response = self.client.post(
                self.list_url, {"title": "x", "file": upload_file}, format="multipart"
            )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
