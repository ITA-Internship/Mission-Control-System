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
        self._verify_content_signatures()

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

    def _verify_content_signatures(self):
        """Ensure every configured upload extension has a content-type signature.

        ARTIFACT_ALLOWED_EXTENSIONS is environment-configurable, but the libmagic
        signature map in media.validators is code. Without this guard, adding an
        extension via env (e.g. .pdf) would look valid yet make content
        validation reject every such upload at runtime. Fail loudly on startup.
        """
        from media.models import VIDEO_ALLOWED_EXTENSIONS
        from media.validators import missing_signatures

        configured = [
            ext
            for exts in settings.ARTIFACT_ALLOWED_EXTENSIONS.values()
            for ext in exts
        ]
        configured += list(VIDEO_ALLOWED_EXTENSIONS)

        missing = missing_signatures(configured)
        if missing:
            error_msg = (
                f"MEDIA MISCONFIGURATION: upload extensions "
                f"{', '.join(sorted(missing))} have no content-type signature in "
                f"media.validators.EXTENSION_CONTENT_TYPES. Add a signature entry "
                f"for each, or remove it from the allow-list."
            )
            logger.critical(error_msg)
            raise ImproperlyConfigured(error_msg)
