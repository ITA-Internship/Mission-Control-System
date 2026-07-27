"""Test suite for MissionArtifact model lifecycle."""

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from media.factories import MissionArtifactFactory
from missions.factories import MissionFactory, OperatorUserFactory


@override_settings(
    ARTIFACT_ALLOWED_EXTENSIONS={
        "image": [".jpg", ".jpeg", ".png"],
        "video": [".mp4", ".avi", ".mov"],
        "data": [".json", ".csv", ".xml"],
    },
    ARTIFACT_MAX_FILE_SIZE_MB=10,
)
class MissionArtifactModelTests(TestCase):
    """Test creation, validation and deletion of media artifacts."""

    def test_str_representation(self):
        """Verify the custom string representation format of
        a MissionArtifact instance."""
        mission = MissionFactory()
        artifact = MissionArtifactFactory(
            title="Drone Footage", is_video=True, mission=mission
        )
        self.assertEqual(
            str(artifact), f"Drone Footage (video) — Mission #{mission.id}"
        )

    def test_auto_fields_on_save(self):
        """Verify automatic population of file metadata on initial save."""
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
        """Ensure model-level validation flags whitespace-only titles."""
        artifact = MissionArtifactFactory.build(title="   ", is_image=True)
        with self.assertRaises(ValidationError) as context:
            artifact.clean()
        self.assertIn("title", context.exception.message_dict)

    @override_settings(ARTIFACT_ALLOWED_EXTENSIONS={"video": [".mp4"]})
    def test_unsupported_extension_raises_validation_error(self):
        """Verify rejection of unlisted file extensions."""
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
        """Verify that 0-byte files fail validation."""
        upload_file = SimpleUploadedFile("empty.jpg", b"")
        artifact = MissionArtifactFactory.build(file=upload_file)

        with self.assertRaises(ValidationError):
            artifact.file.field.clean(upload_file, artifact)
