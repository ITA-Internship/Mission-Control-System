from types import SimpleNamespace

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from media.factories import MissionArtifactFactory
from media.models import video_upload_path
from missions.factories import MissionFactory, OperatorUserFactory


class VideoUploadPathTests(TestCase):
    def _instance(self):
        return SimpleNamespace(mission_id=7, drone_id=3)

    def test_uses_uuid_and_drops_raw_client_filename(self):
        path = video_upload_path(self._instance(), "flight_clip.mp4")
        self.assertTrue(path.startswith("missions/7/drones/3/"))
        self.assertTrue(path.endswith(".mp4"))
        # The raw client name must not survive into the storage path.
        self.assertNotIn("flight_clip", path)
        # <uuid4 hex>.mp4 == 32 + 4 characters.
        self.assertEqual(len(path.rsplit("/", 1)[1]), 36)

    def test_rejects_path_traversal_filename(self):
        # A traversal payload must not leak ".." or the attacker's basename.
        path = video_upload_path(self._instance(), "../../../../etc/passwd.mp4")
        self.assertNotIn("..", path)
        self.assertNotIn("passwd", path)
        self.assertTrue(path.startswith("missions/7/drones/3/"))

    def test_rejects_unsupported_extension(self):
        with self.assertRaises(ValidationError):
            video_upload_path(self._instance(), "malware.exe")


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
