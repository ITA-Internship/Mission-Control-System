"""Tests for shared application security behavior and export sanitization."""

import json
import os
import subprocess
import sys
from datetime import datetime
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.middleware.csrf import get_token
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import path
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView

from config.settings import env_bool

from .utils import sanitize_cell, sanitize_row


class CSVSanitizationTests(TestCase):
    def test_sanitize_strings_pass_through(self):
        """Safe strings should not be modified."""
        self.assertEqual(sanitize_cell("Normal Test"), "Normal Test")
        self.assertEqual(sanitize_cell("123 Safe"), "123 Safe")

    def test_dangerous_prefixes(self):
        """Strings starting with =, +, -, @, \t, or \r must be with a quote."""
        dangerous_values = [
            "=SUM(A1:B1)",
            "+1+1",
            "-1+1",
            "@cmd|'/C calc'!A0",
            "\tTabbed content",
            "\rCarriage return",
        ]

        for val in dangerous_values:
            with self.subTest(value=val):
                self.assertEqual(sanitize_cell(val), f"'{val}")

    def test_lstrip_behavior_on_dangerous_prefixes(self):
        """Leading whitespace should not bypass the prefix check (e.g., '  =cmd')."""
        self.assertEqual(sanitize_cell("   =cmd"), "'   =cmd")
        self.assertEqual(sanitize_cell("\n\n+SUM(1,2)"), "'\n\n+SUM(1,2)")

    def test_non_string_passthrough(self):
        """Non-string types (int, float, None, bool, datetime) should pass untouched."""
        self.assertEqual(sanitize_cell(123), 123)
        self.assertEqual(sanitize_cell(-5), -5)
        self.assertEqual(sanitize_cell(-12.34), -12.34)
        self.assertIsNone(sanitize_cell(None))
        self.assertEqual(sanitize_cell(True), True)

        now = datetime.now()
        self.assertEqual(sanitize_cell(now), now)

    def test_negative_numbers_as_strings(self):
        """Tradeoff check: Negative numbers formatted as strings get prepended."""
        self.assertEqual(sanitize_cell("-500"), "'-500")

    def test_sanitize_row(self):
        """Ensure sanitize_row correctly maps sanitize_cell across an iterable."""
        row = [1, "=malicious", "safe", "-100", None]
        expected = [1, "'=malicious", "safe", "'-100", None]
        self.assertEqual(sanitize_row(row), expected)


class ProtectedByDefaultView(APIView):
    """Test-only view relying on the global DRF permission policy."""

    def get(self, request):
        """Return a successful response when access is granted."""
        return Response({"detail": "ok"})


class ExplicitlyPublicView(APIView):
    """Test-only view explicitly available to anonymous users."""

    permission_classes = [AllowAny]

    def get(self, request):
        """Return a successful response without authentication."""
        return Response({"detail": "ok"})


class DefaultPermissionPolicyTests(SimpleTestCase):
    """Verify that API endpoints are protected by default."""

    def setUp(self):
        """Create a request factory for permission policy tests."""
        self.factory = APIRequestFactory()

    def test_api_view_without_permissions_requires_authentication(self):
        """Ensure an anonymous request is denied by the global policy."""
        request = self.factory.get("/test-protected/")
        response = ProtectedByDefaultView.as_view()(request)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_allow_any_explicitly_overrides_global_policy(self):
        """Ensure explicitly public endpoints remain accessible."""
        request = self.factory.get("/test-public/")
        response = ExplicitlyPublicView.as_view()(request)

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data,
            {"detail": "ok"},
        )


class EnvironmentBooleanSettingsTests(SimpleTestCase):
    """Verify strict parsing of boolean environment variables."""

    @patch.dict(os.environ, {"TEST_BOOLEAN_SETTING": "true"})
    def test_env_bool_accepts_true_value(self):
        """Ensure supported true values are parsed correctly."""
        self.assertTrue(env_bool("TEST_BOOLEAN_SETTING"))

    @patch.dict(os.environ, {"TEST_BOOLEAN_SETTING": "False"})
    def test_env_bool_accepts_false_value(self):
        """Ensure supported false values are parsed correctly."""
        self.assertFalse(env_bool("TEST_BOOLEAN_SETTING", default=True))

    @patch.dict(os.environ, {"TEST_BOOLEAN_SETTING": "invalid"})
    def test_env_bool_rejects_invalid_value(self):
        """Ensure configuration errors are not silently ignored."""
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "TEST_BOOLEAN_SETTING must be a boolean value",
        ):
            env_bool("TEST_BOOLEAN_SETTING")

    def test_env_bool_uses_default_for_missing_value(self):
        """Ensure the supplied default is used when the variable is absent."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TEST_MISSING_BOOLEAN_SETTING", None)

            self.assertTrue(
                env_bool(
                    "TEST_MISSING_BOOLEAN_SETTING",
                    default=True,
                )
            )


class SecurityCookieSettingsTests(SimpleTestCase):
    """Verify secure defaults for session and CSRF cookies."""

    def test_session_cookie_is_http_only(self):
        """Ensure JavaScript cannot read the session cookie."""
        self.assertTrue(settings.SESSION_COOKIE_HTTPONLY)

    def test_session_cookie_uses_lax_same_site_policy(self):
        """Ensure session cookies have cross-site request protection."""
        self.assertEqual(
            settings.SESSION_COOKIE_SAMESITE,
            "Lax",
        )

    def test_csrf_cookie_uses_lax_same_site_policy(self):
        """Ensure CSRF cookies have a SameSite policy."""
        self.assertEqual(
            settings.CSRF_COOKIE_SAMESITE,
            "Lax",
        )

    def test_production_transport_security_values_are_secure(self):
        """Ensure production settings load concrete secure values."""
        environment = os.environ.copy()
        environment.update(
            {
                "DJANGO_SETTINGS_MODULE": "config.settings",
                "DJANGO_SECRET_KEY": "test-secret-key",
                "DEBUG": "False",
                "DB_NAME": "test_db",
                "DB_USER": "test_user",
                "DB_PASSWORD": "test_password",
                "DB_HOST": "localhost",
                "DB_PORT": "5432",
                "STORAGE_PROVIDER": "local",
                "USE_LOCAL_CACHE": "true",
                "SESSION_COOKIE_SECURE": "True",
                "CSRF_COOKIE_SECURE": "True",
                "SECURE_SSL_REDIRECT": "True",
                "SECURE_HSTS_SECONDS": "31536000",
                "SECURE_HSTS_INCLUDE_SUBDOMAINS": "True",
                "SECURE_HSTS_PRELOAD": "True",
            }
        )

        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import json; "
                    "from django.conf import settings; "
                    "print(json.dumps({"
                    "'debug': settings.DEBUG, "
                    "'session_cookie_secure': settings.SESSION_COOKIE_SECURE, "
                    "'csrf_cookie_secure': settings.CSRF_COOKIE_SECURE, "
                    "'ssl_redirect': settings.SECURE_SSL_REDIRECT, "
                    "'hsts_seconds': settings.SECURE_HSTS_SECONDS, "
                    "'hsts_include_subdomains': "
                    "settings.SECURE_HSTS_INCLUDE_SUBDOMAINS, "
                    "'hsts_preload': settings.SECURE_HSTS_PRELOAD"
                    "}))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            env=environment,
        )

        production_settings = json.loads(result.stdout)

        self.assertFalse(production_settings["debug"])
        self.assertTrue(production_settings["session_cookie_secure"])
        self.assertTrue(production_settings["csrf_cookie_secure"])
        self.assertTrue(production_settings["ssl_redirect"])
        self.assertEqual(
            production_settings["hsts_seconds"],
            31536000,
        )
        self.assertTrue(
            production_settings["hsts_include_subdomains"],
        )
        self.assertTrue(production_settings["hsts_preload"])


TEST_ENDPOINT = "/test/session-protected/"


class SessionProtectedView(APIView):
    """Test-only API view protected by the global permission policy."""

    def get(self, request):
        """Return a response and ensure a CSRF cookie is created."""
        get_token(request)
        return Response({"detail": "ok"})

    def post(self, request):
        """Return a response for a valid authenticated POST request."""
        return Response({"detail": "ok"})


urlpatterns = [
    path(
        "test/session-protected/",
        SessionProtectedView.as_view(),
        name="test-session-protected",
    ),
]


@override_settings(ROOT_URLCONF=__name__)
class SessionAuthenticationSecurityTests(TestCase):
    """Verify secure session authentication behavior."""

    def setUp(self):
        """Create an active user and a CSRF-aware API client."""
        self.password = "StrongTestPassword123!"
        self.user = get_user_model().objects.create_user(
            username="session_test_user",
            email="session-test@example.com",
            password=self.password,
        )
        self.client = APIClient(enforce_csrf_checks=True)

    def login_user(self):
        """Authenticate the active test user using a real session."""
        logged_in = self.client.login(
            username=self.user.username,
            password=self.password,
        )
        self.assertTrue(logged_in)

    def test_anonymous_user_cannot_access_protected_endpoint(self):
        response = self.client.get(TEST_ENDPOINT)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_authenticated_session_can_access_protected_endpoint(self):
        self.login_user()

        response = self.client.get(TEST_ENDPOINT)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "ok"})

    def test_unsafe_session_request_without_csrf_is_denied(self):
        self.login_user()

        response = self.client.post(
            TEST_ENDPOINT,
            {"value": "test"},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_unsafe_session_request_with_csrf_is_allowed(self):
        self.login_user()

        csrf_response = self.client.get(TEST_ENDPOINT)

        self.assertEqual(
            csrf_response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn(
            settings.CSRF_COOKIE_NAME,
            self.client.cookies,
        )

        csrf_token = self.client.cookies[settings.CSRF_COOKIE_NAME].value

        response = self.client.post(
            TEST_ENDPOINT,
            {"value": "test"},
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"detail": "ok"})

    def test_logout_invalidates_authenticated_access(self):
        self.login_user()

        response = self.client.get(TEST_ENDPOINT)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.logout()

        response = self.client.get(TEST_ENDPOINT)
        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_inactive_user_cannot_create_authenticated_session(self):
        inactive_user = get_user_model().objects.create_user(
            username="inactive_session_user",
            email="inactive-session@example.com",
            password=self.password,
            is_active=False,
        )

        logged_in = self.client.login(
            username=inactive_user.username,
            password=self.password,
        )

        self.assertFalse(logged_in)

        response = self.client.get(TEST_ENDPOINT)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
