from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from missions.factories import MissionFactory, OperatorUserFactory
from media.factories import MissionArtifactFactory


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