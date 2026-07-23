"""Tests for shared application security behavior."""

from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.test import APIRequestFactory
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
