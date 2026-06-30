from unittest.mock import PropertyMock, patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from storages.backends.azure_storage import AzureStorage
from storages.backends.gcloud import GoogleCloudStorage
from storages.backends.s3boto3 import S3Boto3Storage

from media.models import MissionArtifact
from media.services import delete_artifact, upload_artifact
from missions.factories import MissionFactory, OperatorUserFactory


class CloudStorageIntegrationTests(TestCase):
    def setUp(self):
        self.mission = MissionFactory()
        self.user = OperatorUserFactory()
        self.file_content = b"fake video content streaming data"
        self.upload_file = SimpleUploadedFile(
            "mission_clip.mp4", self.file_content, content_type="video/mp4"
        )

    @override_settings(
        STORAGE_PROVIDER="s3",
        STORAGES={"default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}},
        ARTIFACT_ALLOWED_EXTENSIONS={"video": [".mp4"]},
    )
    @patch("storages.backends.s3boto3.S3Boto3Storage.__init__", return_value=None)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save")
    @patch("storages.backends.s3boto3.S3Boto3Storage.delete")
    def test_aws_s3_upload_and_delete_flow(self, mock_delete, mock_save, mock_init):
        mock_save.return_value = "artifacts/mission_1/secure_s3_name.mp4"

        artifact = upload_artifact(
            mission=self.mission,
            file=self.upload_file,
            title="S3 Mission Video",
            uploaded_by=self.user,
        )

        self.assertEqual(artifact.storage_backend, "s3")
        mock_save.assert_called_once()

        self.assertTrue(MissionArtifact.objects.filter(id=artifact.id).exists())

        with self.captureOnCommitCallbacks(execute=True):
            delete_artifact(artifact=artifact, action_user=self.user)

        self.assertFalse(MissionArtifact.objects.filter(id=artifact.id).exists())

        mock_delete.assert_called_once()

    @override_settings(
        STORAGE_PROVIDER="minio",
        STORAGES={"default": {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}},
        ARTIFACT_ALLOWED_EXTENSIONS={"video": [".mp4"]},
    )
    @patch("storages.backends.s3boto3.S3Boto3Storage.__init__", return_value=None)
    @patch("storages.backends.s3boto3.S3Boto3Storage.save")
    @patch("storages.backends.s3boto3.S3Boto3Storage.delete")
    def test_minio_upload_and_delete_flow(self, mock_delete, mock_save, mock_init):
        mock_save.return_value = "artifacts/mission_1/secure_minio_name.mp4"

        artifact = upload_artifact(
            mission=self.mission,
            file=self.upload_file,
            title="MinIO Mission Video",
            uploaded_by=self.user,
        )

        self.assertEqual(artifact.storage_backend, "minio")
        mock_save.assert_called_once()

        self.assertTrue(MissionArtifact.objects.filter(id=artifact.id).exists())

        with self.captureOnCommitCallbacks(execute=True):
            delete_artifact(artifact=artifact, action_user=self.user)

        self.assertFalse(MissionArtifact.objects.filter(id=artifact.id).exists())

        mock_delete.assert_called_once()

    @override_settings(
        STORAGE_PROVIDER="azure",
        STORAGES={
            "default": {"BACKEND": "storages.backends.azure_storage.AzureStorage"}
        },
        ARTIFACT_ALLOWED_EXTENSIONS={"video": [".mp4"]},
    )
    @patch("storages.backends.azure_storage.AzureStorage.__init__", return_value=None)
    @patch("storages.backends.azure_storage.AzureStorage.save")
    @patch("storages.backends.azure_storage.AzureStorage.delete")
    def test_azure_blob_upload_and_delete_flow(self, mock_delete, mock_save, mock_init):
        mock_save.return_value = "artifacts/mission_1/secure_azure_name.mp4"

        artifact = upload_artifact(
            mission=self.mission,
            file=self.upload_file,
            title="Azure Mission Video",
            uploaded_by=self.user,
        )

        self.assertEqual(artifact.storage_backend, "azure")
        mock_save.assert_called_once()

        self.assertTrue(MissionArtifact.objects.filter(id=artifact.id).exists())

        with self.captureOnCommitCallbacks(execute=True):
            delete_artifact(artifact=artifact, action_user=self.user)

        self.assertFalse(MissionArtifact.objects.filter(id=artifact.id).exists())

        mock_delete.assert_called_once()

    @override_settings(
        STORAGE_PROVIDER="gcs",
        STORAGES={
            "default": {"BACKEND": "storages.backends.gcloud.GoogleCloudStorage"}
        },
        ARTIFACT_ALLOWED_EXTENSIONS={"video": [".mp4"]},
    )
    @patch("storages.backends.gcloud.GoogleCloudStorage.__init__", return_value=None)
    @patch("storages.backends.gcloud.GoogleCloudStorage.save")
    @patch("storages.backends.gcloud.GoogleCloudStorage.delete")
    def test_gcs_upload_and_delete_flow(self, mock_delete, mock_save, mock_init):
        mock_save.return_value = "artifacts/mission_1/secure_gcs_name.mp4"

        artifact = upload_artifact(
            mission=self.mission,
            file=self.upload_file,
            title="GCS Mission Video",
            uploaded_by=self.user,
        )

        self.assertEqual(artifact.storage_backend, "gcs")
        mock_save.assert_called_once()

        self.assertTrue(MissionArtifact.objects.filter(id=artifact.id).exists())

        with self.captureOnCommitCallbacks(execute=True):
            delete_artifact(artifact=artifact, action_user=self.user)

        self.assertFalse(MissionArtifact.objects.filter(id=artifact.id).exists())

        mock_delete.assert_called_once()


class SecurityConfigurationTests(TestCase):

    @override_settings(
        AWS_ACCESS_KEY_ID="fake-key",
        AWS_SECRET_ACCESS_KEY="fake-secret",
        AWS_DEFAULT_ACL=None,
        AWS_QUERYSTRING_AUTH=True,
        AWS_S3_FILE_OVERWRITE=False,
        AWS_S3_SIGNATURE_VERSION="s3v4",
    )
    @patch(
        "storages.backends.s3boto3.S3Boto3Storage.connection", new_callable=PropertyMock
    )
    def test_s3_storage_security_parameters_are_applied(self, mock_connection):
        storage = S3Boto3Storage()

        self.assertIsNone(storage.default_acl)
        self.assertTrue(storage.querystring_auth)
        self.assertFalse(storage.file_overwrite)

    @override_settings(
        AWS_ACCESS_KEY_ID="fake-key",
        AWS_SECRET_ACCESS_KEY="fake-secret",
        AWS_DEFAULT_ACL=None,
        AWS_QUERYSTRING_AUTH=True,
        AWS_S3_FILE_OVERWRITE=False,
    )
    @patch(
        "storages.backends.s3boto3.S3Boto3Storage.connection", new_callable=PropertyMock
    )
    def test_minio_storage_security_parameters_are_applied(self, mock_connection):
        storage = S3Boto3Storage()

        self.assertIsNone(storage.default_acl)
        self.assertTrue(storage.querystring_auth)
        self.assertFalse(storage.file_overwrite)

    @override_settings(
        AZURE_ACCOUNT_NAME="fake-account",
        AZURE_ACCOUNT_KEY="fake-key",
        AZURE_OVERWRITE_FILES=False,
    )
    @patch(
        "storages.backends.azure_storage.AzureStorage.client", new_callable=PropertyMock
    )
    def test_azure_storage_security_parameters_are_applied(self, mock_client):
        storage = AzureStorage()

        self.assertFalse(storage.overwrite_files)

    @override_settings(
        GS_CREDENTIALS="fake-credentials",
        GS_FILE_OVERWRITE=False,
        GS_QUERYSTRING_AUTH=True,
        GS_DEFAULT_ACL=None,
    )
    @patch(
        "storages.backends.gcloud.GoogleCloudStorage.client", new_callable=PropertyMock
    )
    def test_gcs_storage_security_parameters_are_applied(self, mock_client):
        storage = GoogleCloudStorage()

        self.assertIsNone(storage.default_acl)
        self.assertTrue(storage.querystring_auth)
        self.assertFalse(storage.file_overwrite)
