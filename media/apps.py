"""Application configuration for the media app."""

import logging

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)


class MediaConfig(AppConfig):
    """Default configuration for the media app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "media"
    verbose_name = "Mission Media Artifacts"

    def ready(self):
        """Perform application initialization tasks when Django starts."""
        import media.signals  # noqa: F401

        self._verify_storage_configuration()

    def _verify_storage_configuration(self):
        """Validate that the storage provider matches
        the active file storage backend."""
        configured_provider = getattr(settings, "STORAGE_PROVIDER", "local")

        actual_backend = getattr(settings, "DEFAULT_FILE_STORAGE", "")

        expected_backends = {
            "local": "django.core.files.storage.FileSystemStorage",
            "s3": "storages.backends.s3boto3.S3Boto3Storage",
            "minio": "storages.backends.s3boto3.S3Boto3Storage",
            "gcs": "storages.backends.gcloud.GoogleCloudStorage",
            "azure": "storages.backends.azure_storage.AzureStorage",
        }

        expected_backend = expected_backends.get(configured_provider)

        if expected_backend and actual_backend != expected_backend:
            error_msg = (
                f"STORAGE MISCONFIGURATION: "
                f"STORAGE_PROVIDER is '{configured_provider}', "
                f"which expects backend '{expected_backend}', but DEFAULT_FILE_STORAGE "
                f"is actually set to '{actual_backend}'. This breaks self-verification."
            )
            logger.critical(error_msg)
            raise ImproperlyConfigured(error_msg)
