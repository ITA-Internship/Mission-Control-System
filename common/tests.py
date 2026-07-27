"""Tests for shared application security behavior."""

import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.middleware.csrf import get_token
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import path
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIClient, APIRequestFactory
from rest_framework.views import APIView


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

    def test_session_cookie_secure_matches_environment(self):
        """Ensure the session cookie policy matches the startup environment."""
        debug_from_environment = os.getenv("DEBUG", "False") == "True"

        self.assertEqual(
            settings.SESSION_COOKIE_SECURE,
            not debug_from_environment,
        )

    def test_csrf_cookie_secure_matches_environment(self):
        """Ensure the CSRF cookie policy matches the startup environment."""
        debug_from_environment = os.getenv("DEBUG", "False") == "True"

        self.assertEqual(
            settings.CSRF_COOKIE_SECURE,
            not debug_from_environment,
        )


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
