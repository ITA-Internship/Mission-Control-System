"""Test suite for media content-validation helpers and startup checks."""

from django.apps import apps
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from media.validators import missing_signatures


class MissingSignaturesTests(SimpleTestCase):
    """Test the extension/signature sync helper."""

    def test_returns_empty_when_all_have_signatures(self):
        """Verify mapped extensions report nothing missing."""
        self.assertEqual(missing_signatures([".jpg", ".png", "mp4"]), set())

    def test_flags_extension_without_signature(self):
        """Verify an extension absent from the map is reported."""
        self.assertEqual(missing_signatures([".pdf", ".jpg"]), {".pdf"})

    def test_normalises_case_and_leading_dot(self):
        """Verify undotted and upper-case extensions normalise before lookup."""
        self.assertEqual(missing_signatures(["JPG", "PNG"]), set())


class ContentSignatureStartupCheckTests(SimpleTestCase):
    """Test that the media app fails loudly on an unmapped extension."""

    def _run_check(self):
        """Invoke the media app's content-signature startup check."""
        apps.get_app_config("media")._verify_content_signatures()

    @override_settings(
        ARTIFACT_ALLOWED_EXTENSIONS={"image": [".jpg", ".png"], "data": [".csv"]}
    )
    def test_passes_when_every_extension_is_mapped(self):
        """Verify a fully-mapped allow-list passes the check."""
        self._run_check()  # must not raise

    @override_settings(
        ARTIFACT_ALLOWED_EXTENSIONS={"image": [".jpg"], "document": [".pdf"]}
    )
    def test_raises_when_extension_has_no_signature(self):
        """Verify an unmapped configured extension raises at startup."""
        with self.assertRaises(ImproperlyConfigured) as ctx:
            self._run_check()
        self.assertIn(".pdf", str(ctx.exception))
