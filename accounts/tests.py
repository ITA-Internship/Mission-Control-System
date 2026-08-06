"""Test suite for user accounts, role management, authentication."""

import base64
import csv
import io
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.conf import settings
from django.contrib.auth import BACKEND_SESSION_KEY, HASH_SESSION_KEY, SESSION_KEY
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.sessions.models import Session
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import RequestFactory, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from common.authentication import RequiredPasswordChangeBasicAuthentication
from drones.factories import (
    AdminUserFactory,
    DroneFactory,
    MilitaryUnitFactory,
    ViewerUserFactory,
)
from roles.models import ADMIN_CODE, OPERATOR_CODE, Role
from seed_data.users import seed_users

from .models import (
    AuditLog,
    MilitaryUnit,
    User,
    UserRoleAuditLog,
    UserSession,
    UserStatusLog,
)
from .permissions import user_has_permission
from .rbac import (
    PERMISSION_PROFILE_RESET_PASSWORD_OWN,
    PERMISSION_PROFILE_UPDATE_OWN,
    PERMISSION_PROFILE_VIEW_ANY,
    PERMISSION_PROFILE_VIEW_OWN,
)
from .serializers import delete_storage_file_safely
from .services import create_audit_log, update_user_role
from .throttles import (
    AccountActivationThrottle,
    LoginThrottle,
    PasswordResetRequestThrottle,
)
from .tokens import account_activation_token_generator
from .views import UserMeView

THROTTLE_TEST_SETTINGS = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "login": "5/min",
        "account_activation": "1/minute",
        "password_reset_request": "1/minute",
        "password_reset_confirm": "1/minute",
        "audit_export": "10/hour",
    },
}


class UpdateUserRoleTests(TestCase):
    """Test the service-level logic for updating user roles."""

    def setUp(self):
        """Set up standard roles, a root admin, and a target operator for testing."""
        self.admin_role = Role.objects.get(code=ADMIN_CODE)
        self.operator_role = Role.objects.get(code=OPERATOR_CODE)

        self.root_admin = User.objects.create_user(
            username="root.admin",
            email="root.admin@example.com",
            password="Test@1234",
            role=self.admin_role,
            is_active=True,
            is_superuser=True,
            is_staff=True,
        )
        self.target_user = User.objects.create_user(
            username="operator.alpha",
            email="operator.alpha@example.com",
            password="Test@1234",
            role=self.operator_role,
            is_active=True,
        )

    def test_admin_can_update_another_users_role(self):
        """Verify that an admin can change user's role and generate logs."""
        updated_user = update_user_role(
            target_user=self.target_user,
            new_role_id=self.admin_role.id,
            changed_by=self.root_admin,
        )

        updated_user.refresh_from_db()

        self.assertEqual(updated_user.role, self.admin_role)
        self.assertTrue(
            UserRoleAuditLog.objects.filter(
                target_user=self.target_user,
                changed_by=self.root_admin,
                previous_role=self.operator_role,
                new_role=self.admin_role,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.root_admin,
                target_user=self.target_user,
                action_type=AuditLog.ActionType.ROLE_CHANGED,
                result=AuditLog.ResultStatus.SUCCESS,
            ).exists()
        )


class CreateAuditLogIPResolutionTests(TestCase):
    """Test that create_audit_log persists the resolved client IP, not raw headers."""

    def setUp(self):
        """Initialize a request factory and a minimal actor for audit entries."""
        self.factory = RequestFactory()
        self.actor = User.objects.create_user(
            username="audit.actor",
            email="audit.actor@example.com",
            password="StrongPassword123!",
            is_active=True,
        )

    @override_settings(TRUSTED_PROXY_COUNT=0)
    def test_audit_log_ignores_spoofed_header_with_no_trusted_proxy(self):
        """Verify a forged X-Forwarded-For cannot end up in an AuditLog entry."""
        request = self.factory.get(
            "/",
            REMOTE_ADDR="203.0.113.9",
            HTTP_X_FORWARDED_FOR="6.6.6.6",
        )

        log = create_audit_log(
            actor=self.actor,
            action_type=AuditLog.ActionType.USER_CREATED,
            result=AuditLog.ResultStatus.SUCCESS,
            request=request,
        )

        self.assertEqual(log.ip_address, "203.0.113.9")
        self.assertNotEqual(log.ip_address, "6.6.6.6")

    @override_settings(TRUSTED_PROXY_COUNT=2)
    def test_audit_log_records_real_client_ip_behind_trusted_proxies(self):
        """Verify the real client IP is recorded when proxies are trusted."""
        request = self.factory.get(
            "/",
            REMOTE_ADDR="10.0.0.2",
            HTTP_X_FORWARDED_FOR="1.2.3.4, 10.0.0.1, 10.0.0.2",
        )

        log = create_audit_log(
            actor=self.actor,
            action_type=AuditLog.ActionType.USER_CREATED,
            result=AuditLog.ResultStatus.SUCCESS,
            request=request,
        )

        self.assertEqual(log.ip_address, "10.0.0.1")


class UserStatusUpdateViewTests(APITestCase):
    """Test the API endpoints for activating and deactivating user accounts."""

    def setUp(self):
        """Initialize an admin user and a target user for status modification."""
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="password123",
            is_active=True,
        )

        admin_role, _ = Role.objects.get_or_create(
            code="ADMIN", defaults={"name": "Administrator"}
        )

        self.admin_user.role = admin_role
        self.admin_user.save()

        self.target_user = User.objects.create_user(
            username="target_user",
            email="target@example.com",
            password="password123",
            is_active=True,
        )

        self.url = reverse(
            "accounts:user-status-update", kwargs={"pk": self.target_user.pk}
        )

    def test_admin_can_deactivate_user(self):
        """Verify that an admin can deactivate a user and a status log is created."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"is_active": False, "reason": "Violation of terms"}

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_active"], False)

        self.target_user.refresh_from_db()
        self.assertFalse(self.target_user.is_active)

        self.assertTrue(
            UserStatusLog.objects.filter(
                target_user=self.target_user,
                changed_by=self.admin_user,
                old_status=True,
                new_status=False,
                reason="Violation of terms",
            ).exists()
        )

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.admin_user,
                action_type=AuditLog.ActionType.ACCOUNT_DEACTIVATED,
                result=AuditLog.ResultStatus.SUCCESS,
                target_user=self.target_user,
            ).exists()
        )

    def test_admin_cannot_deactivate_self(self):
        """Ensure that users are restricted from deactivating their own accounts."""
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("accounts:user-status-update", kwargs={"pk": self.admin_user.pk})
        payload = {"is_active": False, "reason": "Quitting"}

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot deactivate your own account", response.data["detail"])

        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_unchanged_status_returns_200_with_message(self):
        """Verify submitting the same status returns a message without logging."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"is_active": True}

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "User is already active.")

        self.assertFalse(UserStatusLog.objects.exists())

    def test_invalid_payload_returns_400(self):
        """Ensure that the endpoint rejects non-boolean values for the status field."""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"is_active": "not-a-boolean"}

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordViewTests(APITestCase):
    """Test the authenticated password change API endpoint."""

    def setUp(self):
        """Initialize a standard user for password change operations."""
        self.operator_role = Role.objects.get(code=OPERATOR_CODE)
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="OldPassword123!",
            role=self.operator_role,
        )
        self.user_without_role = User.objects.create_user(
            username="testuser.no.role",
            email="testuser.no.role@example.com",
            password="OldPassword123!",
        )
        self.url = reverse("accounts:change-password")

    def test_change_password_success(self):
        """Verify that a user can change their password given correct old password."""
        self.client.force_authenticate(user=self.user)
        payload = {
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "Password has been successfully changed."
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewPassword123!"))

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.user,
                action_type=AuditLog.ActionType.PASSWORD_CHANGED,
                result=AuditLog.ResultStatus.SUCCESS,
                target_user=self.user,
            ).exists()
        )

    def test_change_password_invalidates_other_sessions(self):
        """Verify password change clears other sessions and rotates the current one."""
        hijacked_session = Session.objects.create(
            session_key="hijacked_key_123",
            session_data=SessionStore().encode({"test_session": "hijacked"}),
            expire_date=timezone.now() + timedelta(days=1),
        )
        UserSession.objects.create(
            user=self.user, session_key=hijacked_session.session_key
        )

        self.client.force_authenticate(user=self.user)
        current_session = self.client.session
        current_session["_auth_user_id"] = str(self.user.pk)
        current_session.save()
        current_session_key = current_session.session_key
        UserSession.objects.create(user=self.user, session_key=current_session_key)

        active_sessions = Session.objects.filter(
            session_key__in=["hijacked_key_123", current_session_key]
        )
        tracked_sessions = UserSession.objects.filter(user=self.user)

        self.assertEqual(active_sessions.count(), 2)
        self.assertEqual(tracked_sessions.count(), 2)

        payload = {
            "old_password": "OldPassword123!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(
            Session.objects.filter(session_key="hijacked_key_123").exists()
        )
        self.assertFalse(
            UserSession.objects.filter(session_key="hijacked_key_123").exists()
        )

        self.assertEqual(UserSession.objects.filter(user=self.user).count(), 1)
        rotated_session_key = self.client.cookies[settings.SESSION_COOKIE_NAME].value
        self.assertNotEqual(rotated_session_key, current_session_key)
        self.assertFalse(
            Session.objects.filter(session_key=current_session_key).exists()
        )
        self.assertFalse(
            UserSession.objects.filter(session_key=current_session_key).exists()
        )
        self.assertTrue(
            Session.objects.filter(session_key=rotated_session_key).exists()
        )
        self.assertTrue(
            UserSession.objects.filter(session_key=rotated_session_key).exists()
        )
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.pk))

    def test_change_password_only_invalidates_target_users_sessions(self):
        """Ensure targeted cleanup leaves another user's session untouched."""
        other_user = User.objects.create_user(
            username="other.session.user",
            email="other.session.user@example.com",
            password="OtherPassword123!",
            role=self.operator_role,
        )
        own_session = Session.objects.create(
            session_key="own_tracked_session",
            session_data=SessionStore().encode({"test_session": "own"}),
            expire_date=timezone.now() + timedelta(days=1),
        )
        other_session = Session.objects.create(
            session_key="other_tracked_session",
            session_data=SessionStore().encode({"test_session": "other"}),
            expire_date=timezone.now() + timedelta(days=1),
        )
        UserSession.objects.create(
            user=self.user,
            session_key=own_session.session_key,
        )
        UserSession.objects.create(
            user=other_user,
            session_key=other_session.session_key,
        )

        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertFalse(
            Session.objects.filter(session_key=own_session.session_key).exists()
        )
        self.assertTrue(
            Session.objects.filter(session_key=other_session.session_key).exists()
        )
        self.assertTrue(
            UserSession.objects.filter(
                user=other_user,
                session_key=other_session.session_key,
            ).exists()
        )

    def test_password_hash_rejects_an_untracked_legacy_session(self):
        """Ensure untracked sessions cannot authenticate after password change."""
        legacy_session = SessionStore()
        legacy_session[SESSION_KEY] = str(self.user.pk)
        legacy_session[BACKEND_SESSION_KEY] = (
            "django.contrib.auth.backends.ModelBackend"
        )
        legacy_session[HASH_SESSION_KEY] = self.user.get_session_auth_hash()
        legacy_session.save()
        legacy_session_key = legacy_session.session_key

        self.assertFalse(
            UserSession.objects.filter(session_key=legacy_session_key).exists()
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertTrue(Session.objects.filter(session_key=legacy_session_key).exists())

        legacy_client = APIClient()
        legacy_client.cookies[settings.SESSION_COOKIE_NAME] = legacy_session_key
        profile_response = legacy_client.get(reverse("accounts:user-me"))

        self.assertEqual(profile_response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertFalse(
            Session.objects.filter(session_key=legacy_session_key).exists()
        )

    def test_change_password_rejects_current_password_as_new_password(self):
        """Ensure forced password changes require a genuinely new password."""
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {
                "old_password": "OldPassword123!",
                "new_password": "OldPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["new_password"][0],
            "New password must be different from the current password.",
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.must_change_password)
        self.assertTrue(self.user.check_password("OldPassword123!"))

    def test_change_password_failure_invalid_data(self):
        """Ensure password change fails and logs failed audit for a wrong password."""
        self.client.force_authenticate(user=self.user)
        payload = {
            "old_password": "WrongPassword!",
            "new_password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("OldPassword123!"))

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.user,
                action_type=AuditLog.ActionType.PASSWORD_CHANGED,
                result=AuditLog.ResultStatus.FAILED,
                target_user=self.user,
            ).exists()
        )

    def test_authenticated_user_without_role_cannot_change_password(self):
        """Ensure password change requires the explicit RBAC permission."""
        self.client.force_authenticate(user=self.user_without_role)

        response = self.client.post(
            self.url,
            {
                "old_password": "OldPassword123!",
                "new_password": "NewPassword123!",
                "confirm_password": "NewPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_access(self):
        """Verify that anonymous users are blocked from accessing password change."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class UserMeRBACTests(APITestCase):
    """Test RBAC enforcement for self-service profile endpoints."""

    def setUp(self):
        self.operator_role = Role.objects.get(code=OPERATOR_CODE)
        self.unit = MilitaryUnit.objects.create(
            code="UNIT-TST",
            name="Test Unit",
            description="Unit used by self-profile tests.",
        )
        self.user = User.objects.create_user(
            username="profile.owner",
            email="profile.owner@example.com",
            password="StrongPassword123!",
            role=self.operator_role,
            unit=self.unit,
            is_active=True,
        )
        self.user_without_role = User.objects.create_user(
            username="profile.no.role",
            email="profile.no.role@example.com",
            password="StrongPassword123!",
            is_active=True,
        )
        self.url = reverse("accounts:user-me")

    def test_operator_role_has_self_service_profile_permissions(self):
        """Ensure the operator role includes self-service profile permissions."""
        self.assertTrue(user_has_permission(self.user, PERMISSION_PROFILE_VIEW_OWN))
        self.assertTrue(user_has_permission(self.user, PERMISSION_PROFILE_UPDATE_OWN))
        self.assertTrue(
            user_has_permission(self.user, PERMISSION_PROFILE_RESET_PASSWORD_OWN)
        )

    def test_authenticated_user_without_role_cannot_view_own_profile(self):
        """Ensure self-profile read requires the explicit RBAC permission."""
        self.client.force_authenticate(self.user_without_role)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_authenticated_user_without_role_cannot_update_own_profile(self):
        """Ensure self-profile update requires the explicit RBAC permission."""
        self.client.force_authenticate(self.user_without_role)

        response = self.client.patch(
            self.url,
            {"first_name": "Blocked"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_with_profile_permissions_can_view_own_profile(self):
        """Ensure role-based self-profile access still works for valid users."""
        self.client.force_authenticate(self.user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["role_name"], self.user.role.name)
        self.assertEqual(response.data["unit_name"], self.user.unit.name)
        self.assertIn("created_by_username", response.data)
        self.assertNotIn("is_staff", response.data)
        self.assertNotIn("is_superuser", response.data)

    def test_user_with_profile_permissions_can_update_own_profile(self):
        """Ensure role-based self-profile updates still work for valid users."""
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            self.url,
            {"first_name": "Updated"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")

    def test_required_password_change_blocks_profile_updates(self):
        """Reject direct unsafe API calls until the password is changed."""
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])
        self.assertTrue(
            self.client.login(
                username=self.user.username,
                password="StrongPassword123!",
            )
        )

        response = self.client.patch(
            self.url,
            {"first_name": "Blocked"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.json()["code"], "password_change_required")
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.first_name, "Blocked")

    @patch.object(
        UserMeView,
        "authentication_classes",
        [RequiredPasswordChangeBasicAuthentication],
    )
    def test_required_password_change_blocks_basic_authentication(self):
        """Apply the mandatory password policy after DRF Basic authentication."""
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])
        credentials = base64.b64encode(
            f"{self.user.username}:StrongPassword123!".encode()
        ).decode()

        response = self.client.patch(
            self.url,
            {"first_name": "Blocked"},
            format="json",
            HTTP_AUTHORIZATION=f"Basic {credentials}",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["code"], "password_change_required")
        self.user.refresh_from_db()
        self.assertNotEqual(self.user.first_name, "Blocked")

    def test_required_password_change_allows_me_read_and_unlocks_api(self):
        """Allow state discovery and restore API access after password change."""
        self.user.must_change_password = True
        self.user.save(update_fields=["must_change_password"])
        self.assertTrue(
            self.client.login(
                username=self.user.username,
                password="StrongPassword123!",
            )
        )

        me_response = self.client.get(self.url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertTrue(me_response.data["must_change_password"])

        password_response = self.client.post(
            reverse("accounts:change-password"),
            {
                "old_password": "StrongPassword123!",
                "new_password": "NewStrongPassword456!",
            },
            format="json",
        )
        self.assertEqual(password_response.status_code, status.HTTP_200_OK)

        update_response = self.client.patch(
            self.url,
            {"first_name": "Unlocked"},
            format="json",
        )
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        self.assertEqual(self.user.first_name, "Unlocked")

    def test_user_cannot_clear_required_profile_names(self):
        """Reject whitespace-only first and last names at the API boundary."""
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            self.url,
            {
                "first_name": "   ",
                "last_name": "   ",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["first_name"][0], "First name is required.")
        self.assertEqual(response.data["last_name"][0], "Last name is required.")

    def test_user_cannot_exceed_profile_field_lengths(self):
        """Reject values that exceed the backing profile model limits."""
        self.client.force_authenticate(self.user)

        response = self.client.patch(
            self.url,
            {
                "rank": "R" * 101,
                "contact": "C" * 256,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("rank", response.data)
        self.assertIn("contact", response.data)

    @patch("accounts.serializers.logger.exception")
    def test_profile_picture_cleanup_failure_is_logged(self, mock_log_exception):
        """Keep a committed profile update successful when old-file cleanup fails."""
        storage = SimpleNamespace(delete=Mock(side_effect=OSError("storage offline")))

        delete_storage_file_safely(storage, "profile_pictures/old.png")

        storage.delete.assert_called_once_with("profile_pictures/old.png")
        mock_log_exception.assert_called_once()

    def test_user_with_profile_permissions_can_update_own_profile_with_multipart(self):
        """Ensure self-profile updates accept multipart form data for avatars."""
        self.client.force_authenticate(self.user)
        image_buffer = io.BytesIO()
        Image.new("RGB", (1, 1), color="white").save(image_buffer, format="PNG")
        upload = SimpleUploadedFile(
            "avatar.png",
            image_buffer.getvalue(),
            content_type="image/png",
        )

        response = self.client.patch(
            self.url,
            {
                "first_name": "Updated",
                "profile_picture": upload,
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, "Updated")
        self.assertTrue(bool(self.user.profile.profile_picture))
        self.assertEqual(
            response.data["profile_picture"],
            reverse(
                "accounts:user-profile-picture",
                kwargs={"user_id": self.user.pk},
            ),
        )

        with self.settings(DEBUG=False):
            picture_response = self.client.get(response.data["profile_picture"])
        self.assertEqual(picture_response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            picture_response.headers["Cache-Control"],
            "private, no-store",
        )

        remove_response = self.client.patch(
            self.url,
            {"profile_picture": None},
            format="json",
        )

        self.assertEqual(
            remove_response.status_code,
            status.HTTP_200_OK,
            remove_response.data,
        )
        self.user.refresh_from_db()
        self.assertFalse(bool(self.user.profile.profile_picture))
        self.assertIsNone(remove_response.data["profile_picture"])


class LoginViewTests(APITestCase):
    """Test the session login endpoint used by the frontend sign-in form."""

    def setUp(self):
        """Create an active user and the endpoint URLs used by the tests."""
        cache.clear()
        self.password = "Test@1234"
        self.operator_role = Role.objects.get(code=OPERATOR_CODE)
        self.user = User.objects.create_user(
            username="root.admin",
            email="root.admin@example.com",
            password=self.password,
            role=self.operator_role,
            is_active=True,
        )
        self.client = APIClient(enforce_csrf_checks=True)
        self.url = reverse("accounts:login")
        self.logout_url = reverse("accounts:logout")
        self.me_url = reverse("accounts:user-me")

    def _prime_csrf_cookie(self):
        """Request the CSRF cookie required by the session login endpoint."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertIn("csrftoken", self.client.cookies)
        return self.client.cookies["csrftoken"].value

    def test_login_get_issues_csrf_cookie(self):
        """Verify the login bootstrap request returns a CSRF cookie."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["detail"], "CSRF cookie set.")
        self.assertIn("csrftoken", self.client.cookies)

    def test_login_requires_csrf_token(self):
        """Verify unsafe login requests are rejected without a CSRF token."""
        response = self.client.post(
            self.url,
            {
                "identifier": self.user.email,
                "password": self.password,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_login_with_email_creates_session(self):
        """Verify email-based login starts a session and returns user data."""
        csrf_token = self._prime_csrf_cookie()

        response = self.client.post(
            self.url,
            {
                "identifier": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["id"], self.user.id)
        self.assertEqual(response.data["email"], self.user.email)
        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(self.user.pk),
        )
        self.assertIn("csrftoken", response.cookies)

        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK, me_response.data)
        self.assertEqual(me_response.data["email"], self.user.email)

    def test_login_rotates_existing_anonymous_session_key(self):
        """Verify session login rotates the session key to avoid fixation."""
        csrf_token = self._prime_csrf_cookie()
        session = self.client.session
        session["bootstrap"] = "anonymous"
        session.save()
        anonymous_session_key = session.session_key

        response = self.client.post(
            self.url,
            {
                "identifier": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertNotEqual(self.client.session.session_key, anonymous_session_key)

    def test_login_with_username_creates_session(self):
        """Verify username-based login is also accepted for compatibility."""
        csrf_token = self._prime_csrf_cookie()

        response = self.client.post(
            self.url,
            {
                "identifier": self.user.username,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(
            self.client.session.get("_auth_user_id"),
            str(self.user.pk),
        )

    def test_login_matches_username_case_insensitively(self):
        """Verify mixed-case usernames still resolve to the same account."""
        csrf_token = self._prime_csrf_cookie()

        response = self.client.post(
            self.url,
            {
                "identifier": "ROOT.ADMIN",
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["username"], self.user.username)

    def test_login_matches_email_case_insensitively(self):
        """Verify mixed-case emails still resolve to the same account."""
        csrf_token = self._prime_csrf_cookie()

        response = self.client.post(
            self.url,
            {
                "identifier": "ROOT.ADMIN@EXAMPLE.COM",
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK, response.data)
        self.assertEqual(response.data["email"], self.user.email)

    def test_login_rejects_invalid_credentials(self):
        """Verify the endpoint does not authenticate wrong credentials."""
        csrf_token = self._prime_csrf_cookie()

        response = self.client.post(
            self.url,
            {
                "identifier": self.user.email,
                "password": "WrongPassword!",
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid credentials.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_rejects_whitespace_only_identifier(self):
        """Verify identifiers containing only whitespace are rejected explicitly."""
        csrf_token = self._prime_csrf_cookie()

        response = self.client.post(
            self.url,
            {
                "identifier": "   ",
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Identifier is required.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_rejects_inactive_user_with_generic_error(self):
        """Verify inactive accounts are rejected with the generic auth message."""
        inactive_user = User.objects.create_user(
            username="inactive.user",
            email="inactive.user@example.com",
            password=self.password,
            role=self.operator_role,
            is_active=False,
        )
        csrf_token = self._prime_csrf_cookie()

        response = self.client.post(
            self.url,
            {
                "identifier": inactive_user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["detail"], "Invalid credentials.")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_logout_requires_csrf_and_ends_current_session(self):
        """Verify logout is CSRF protected and removes session tracking."""
        csrf_token = self._prime_csrf_cookie()
        login_response = self.client.post(
            self.url,
            {
                "identifier": self.user.email,
                "password": self.password,
            },
            format="json",
            HTTP_X_CSRFTOKEN=csrf_token,
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        session_key = self.client.session.session_key
        self.assertTrue(
            UserSession.objects.filter(
                user=self.user,
                session_key=session_key,
            ).exists()
        )

        missing_csrf_response = self.client.post(self.logout_url, {}, format="json")
        self.assertEqual(
            missing_csrf_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

        logout_response = self.client.post(
            self.logout_url,
            {},
            format="json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

        self.assertEqual(logout_response.status_code, status.HTTP_200_OK)
        self.assertFalse(Session.objects.filter(session_key=session_key).exists())
        self.assertFalse(UserSession.objects.filter(session_key=session_key).exists())
        self.assertNotIn(SESSION_KEY, self.client.session)


class PasswordResetConfirmViewTests(APITestCase):
    """Test the password reset confirmation API endpoint via token."""

    def setUp(self):
        """Set up a user and generate valid base64 and token parameters."""
        self.operator_role = Role.objects.get(code=OPERATOR_CODE)
        self.user = User.objects.create_user(
            username="resetuser",
            email="test@example.com",
            password="OldPassword123!",
            role=self.operator_role,
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

        self.url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": self.uidb64, "token": self.token},
        )

    @patch("accounts.tasks.send_mail")
    def test_password_reset_success(self, mock_send_mail):
        """Verify successful password reset with valid token and email notification."""
        payload = {
            "new_password": "BrandNewPassword123!",
            "confirm_password": "BrandNewPassword123!",
        }

        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["detail"], "Password has been reset successfully."
        )

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("BrandNewPassword123!"))

        self.assertTrue(
            AuditLog.objects.filter(
                actor=self.user,
                action_type=AuditLog.ActionType.PASSWORD_CHANGED,
                result=AuditLog.ResultStatus.SUCCESS,
                target_user=self.user,
            ).exists()
        )

        mock_send_mail.assert_called_once()
        args, kwargs = mock_send_mail.call_args
        self.assertEqual(kwargs["recipient_list"], [self.user.email])

    def test_password_reset_deletes_all_user_sessions(self):
        """Verify password reset removes all tracked Session and UserSession rows."""
        session_keys = ["reset_session_a", "reset_session_b"]
        for session_key in session_keys:
            Session.objects.create(
                session_key=session_key,
                session_data=SessionStore().encode({"test_session": session_key}),
                expire_date=timezone.now() + timedelta(days=1),
            )
            UserSession.objects.create(user=self.user, session_key=session_key)

        self.assertEqual(UserSession.objects.filter(user=self.user).count(), 2)
        self.assertEqual(
            Session.objects.filter(session_key__in=session_keys).count(), 2
        )

        response = self.client.post(
            self.url,
            {"new_password": "BrandNewPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserSession.objects.filter(user=self.user).count(), 0)
        self.assertEqual(
            Session.objects.filter(session_key__in=session_keys).count(), 0
        )

    def test_password_reset_uses_user_aware_password_validation(self):
        """Reject reset passwords that are too similar to account attributes."""
        response = self.client.post(
            self.url,
            {"new_password": "resetuser123!A"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("too similar", response.data["new_password"][0].lower())

    def test_password_reset_rejects_current_password(self):
        """Do not let a reset token preserve the user's compromised password."""
        response = self.client.post(
            self.url,
            {"new_password": "OldPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["new_password"][0],
            "New password must be different from the current password.",
        )

    @patch("accounts.tasks.send_mail")
    def test_password_reset_invalidates_existing_session(self, mock_send_mail):
        """Ensure password reset terminates the user's existing sessions."""
        session_client = APIClient()

        logged_in = session_client.login(
            username=self.user.username,
            password="OldPassword123!",
        )
        self.assertTrue(logged_in)

        protected_url = reverse("accounts:user-me")

        response_before_reset = session_client.get(protected_url)
        self.assertEqual(
            response_before_reset.status_code,
            status.HTTP_200_OK,
            response_before_reset.data,
        )

        # Login updates last_login, which invalidates the token created in setUp().
        # Refresh the user and generate a new valid token after login.
        self.user.refresh_from_db()

        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)

        reset_url = reverse(
            "accounts:password-reset-confirm",
            kwargs={
                "uidb64": uidb64,
                "token": token,
            },
        )

        reset_response = self.client.post(
            reset_url,
            {
                "new_password": "BrandNewPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            reset_response.status_code,
            status.HTTP_200_OK,
            reset_response.data,
        )

        response_after_reset = session_client.get(protected_url)

        self.assertEqual(
            response_after_reset.status_code,
            status.HTTP_403_FORBIDDEN,
            response_after_reset.data,
        )

        mock_send_mail.assert_called_once()

    def test_password_reset_invalid_token(self):
        """Ensure that an invalid or expired token rejects the password reset."""
        invalid_url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": self.uidb64, "token": "invalid-token"},
        )
        payload = {"new_password": "BrandNewPassword123!"}

        response = self.client.post(invalid_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid or has expired", response.data["detail"])

        self.assertTrue(
            AuditLog.objects.filter(
                action_type=AuditLog.ActionType.PASSWORD_CHANGED,
                result=AuditLog.ResultStatus.FAILED,
                target_user=self.user,
            ).exists()
        )

    def test_invalid_reset_token_cannot_probe_the_current_password(self):
        """Do not expose password-match validation for an invalid reset token."""
        invalid_url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": self.uidb64, "token": "invalid-token"},
        )

        response = self.client.post(
            invalid_url,
            {"new_password": "OldPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"],
            "The reset link is invalid or has expired.",
        )
        self.assertNotIn("new_password", response.data)

    def test_invalid_reset_token_takes_precedence_over_password_validation(self):
        """Return a stable invalid-link response before validating the password."""
        invalid_url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": self.uidb64, "token": "invalid-token"},
        )

        response = self.client.post(
            invalid_url,
            {"new_password": "weak"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data,
            {"detail": "The reset link is invalid or has expired."},
        )

    def test_password_reset_invalid_uidb64(self):
        """Ensure that an invalid base64 encoded user ID rejects the request."""
        invalid_url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": "invalid-uid", "token": self.token},
        )
        payload = {"new_password": "BrandNewPassword123!"}

        response = self.client.post(invalid_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid or has expired", response.data["detail"])


class SeedDbSecurityTests(TestCase):
    """Test security constraints and operational behaviors of the database seeding."""

    @override_settings(DEBUG=False)
    def test_seed_db_is_blocked_outside_debug_mode(self):
        """Ensure that seeding scripts are prohibited from running in production."""
        with self.assertRaisesMessage(
            CommandError,
            "seed_db is allowed only in local development when DEBUG=True.",
        ):
            call_command("seed_db", module="users")

    def test_seed_users_use_provided_password_and_require_password_change(self):
        """Verify that seeded users receive the exact password."""
        seed_password = "TemporarySeedPassword@123"

        stats = seed_users(seed_password=seed_password)
        seeded_user = User.objects.get(username="root.admin")

        self.assertEqual(stats["users_created"], 11)
        self.assertTrue(seeded_user.check_password(seed_password))
        self.assertTrue(seeded_user.must_change_password)

    def test_seed_users_do_not_force_password_change_when_password_is_unchanged(self):
        """Ensure force-change flag is not reapplied if password was already updated."""
        seed_password = "TemporarySeedPassword@123"
        seed_users(seed_password=seed_password)
        seeded_user = User.objects.get(username="root.admin")
        seeded_user.must_change_password = False
        seeded_user.save(update_fields=["must_change_password"])

        seed_users(seed_password=seed_password)

        seeded_user.refresh_from_db()
        self.assertFalse(seeded_user.must_change_password)

    @override_settings(DEBUG=True)
    def test_seed_db_requires_password_when_seeding_users(self):
        """Verify halting and raising an error if no default password is provided."""
        with self.assertRaisesMessage(
            CommandError,
            "Seeding users requires --password or SEED_DEFAULT_PASSWORD.",
        ):
            call_command("seed_db", module="users")

    def test_disable_seeded_users_deactivates_existing_seeded_accounts(self):
        """Ensure that the disable command revokes access for all seeded users."""
        seed_users(seed_password="TemporarySeedPassword@123")
        out = io.StringIO()

        call_command("disable_seeded_users", stdout=out)

        seeded_user = User.objects.get(username="root.admin")
        operator_user = User.objects.get(username="operator.alpha")

        self.assertFalse(seeded_user.is_active)
        self.assertFalse(seeded_user.is_staff)
        self.assertFalse(seeded_user.is_superuser)
        self.assertFalse(operator_user.is_active)
        self.assertIn("Disabled 11 seeded user(s)", out.getvalue())


@override_settings(
    REST_FRAMEWORK=THROTTLE_TEST_SETTINGS,
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class PublicAuthThrottleTests(APITestCase):
    """Test rate-limiting (throttling) behavior on public authentication endpoints."""

    def setUp(self):
        """Clear cache to reset limits and initialize a test user."""
        cache.clear()
        self.request_factory = APIRequestFactory()
        # Pending activation: no usable password yet (mirrors real account
        # creation), so the activation endpoint accepts the first request.
        self.user = User.objects.create_user(
            username="throttle.user",
            email="throttle.user@example.com",
            password=None,
        )

    def test_activation_endpoint_is_throttled(self):
        """Verify that repeated account activation requests return a 429."""
        token = account_activation_token_generator.make_token(self.user)
        url = reverse(
            "accounts:account-activate",
            kwargs={"user_id": self.user.pk, "token": token},
        )

        first_response = self.client.post(
            url,
            {"password": "NewStrongPassword@1234"},
            format="json",
        )
        second_response = self.client.post(
            url,
            {"password": "AnotherStrongPassword@1234"},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    @override_settings(
        REST_FRAMEWORK={
            "DEFAULT_THROTTLE_RATES": {
                "password_reset_request": "1/minute",
                "password_reset_confirm": "1/minute",
            },
        }
    )
    def test_missing_throttle_scope_raises_configuration_error(self):
        """Ensure an error is raised if a throttle rate is undefined in settings."""
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "Missing throttle rate for scope 'account_activation'.",
        ):
            AccountActivationThrottle()

    def test_throttle_cache_key_uses_authenticated_user_when_available(self):
        """Verify that the throttle scopes by user ID for authenticated requests."""
        request = self.request_factory.post("/password-reset/")
        request.user = self.user
        request.data = {"email": "shared@example.com"}
        view = SimpleNamespace(kwargs={})

        cache_key = PasswordResetRequestThrottle().get_cache_key(request, view)

        self.assertIn(f"user:{self.user.pk}", cache_key)

    def test_password_reset_throttle_cache_key_is_scoped_by_email(self):
        """Verify anonymous password reset requests are throttled per email address."""
        view = SimpleNamespace(kwargs={})
        first_request = self.request_factory.post("/password-reset/")
        first_request.data = {"email": "first@example.com"}
        second_request = self.request_factory.post("/password-reset/")
        second_request.data = {"email": "second@example.com"}

        first_key = PasswordResetRequestThrottle().get_cache_key(first_request, view)
        second_key = PasswordResetRequestThrottle().get_cache_key(second_request, view)

        self.assertNotEqual(first_key, second_key)
        self.assertNotIn("first@example.com", first_key)

    def test_login_throttle_cache_key_is_scoped_by_normalized_identifier(self):
        """Verify login throttling hashes the normalized identifier value."""
        view = SimpleNamespace(kwargs={})
        request = self.request_factory.post("/login/")
        request.data = {"identifier": "  ROOT.ADMIN@EXAMPLE.COM "}

        cache_key = LoginThrottle().get_cache_key(request, view)

        self.assertIn("identifier:", cache_key)
        self.assertNotIn("ROOT.ADMIN@EXAMPLE.COM", cache_key)

    def test_login_throttle_ignores_non_mapping_request_data(self):
        """Verify login throttling falls back safely when request.data is unexpected."""
        view = SimpleNamespace(kwargs={})
        request = self.request_factory.post("/login/")
        request.data = "invalid-payload"

        cache_key = LoginThrottle().get_cache_key(request, view)

        self.assertNotIn("identifier:", cache_key)

    def test_password_reset_throttle_ignores_non_mapping_request_data(self):
        """Verify password reset throttling safely handles non-mapping payloads."""
        view = SimpleNamespace(kwargs={})
        request = self.request_factory.post("/password-reset/")
        request.data = "invalid-payload"

        cache_key = PasswordResetRequestThrottle().get_cache_key(request, view)

        self.assertNotIn("email:", cache_key)

    def test_password_reset_request_endpoint_is_throttled(self):
        """Verify that repeated password reset generation requests are rate-limited."""
        url = reverse("accounts:password-reset-request")

        first_response = self.client.post(
            url,
            {"email": self.user.email},
            format="json",
        )
        second_response = self.client.post(
            url,
            {"email": self.user.email},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


@override_settings(
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class AccountActivationSecurityTests(APITestCase):
    """Test that account activation enforces token scope and account state.

    Activation and password-reset both build on Django's token machinery, so
    these tests guard against the two flows' tokens being interchangeable and
    against the endpoint being used to bypass administrative deactivation.
    """

    def setUp(self):
        """Reset throttle state and create a user pending activation."""
        cache.clear()
        self.user = User.objects.create(
            username="pending.user",
            email="pending.user@example.com",
        )
        self.user.set_unusable_password()
        self.user.save()

    def _activation_url(self, token):
        """Build the activation URL for the test user and given token."""
        return reverse(
            "accounts:account-activate",
            kwargs={"user_id": self.user.pk, "token": token},
        )

    def test_valid_activation_token_activates_account(self):
        """Verify a genuine activation token sets a usable password and activates."""
        # Precondition: the account is pending (no usable password yet).
        self.assertFalse(self.user.has_usable_password())

        token = account_activation_token_generator.make_token(self.user)

        response = self.client.post(
            self._activation_url(token),
            {"password": "NewStrongPassword@1234"},
            format="json",
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.user.is_active)
        self.assertTrue(self.user.has_usable_password())
        self.assertTrue(self.user.check_password("NewStrongPassword@1234"))
        self.assertFalse(self.user.must_change_password)

    def test_missing_password_field_is_rejected(self):
        """Verify activation without a password returns a field error."""
        token = account_activation_token_generator.make_token(self.user)

        response = self.client.post(
            self._activation_url(token),
            {},
            format="json",
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIsInstance(response.data["password"], list)
        self.assertFalse(self.user.has_usable_password())

    def test_password_reset_token_cannot_activate_account(self):
        """Verify a password-reset token is rejected by the activation endpoint."""
        reset_token = default_token_generator.make_token(self.user)

        response = self.client.post(
            self._activation_url(reset_token),
            {"password": "NewStrongPassword@1234"},
            format="json",
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(self.user.has_usable_password())

    def test_deactivated_user_cannot_reactivate_via_reset_token(self):
        """Verify a deactivated user cannot reactivate through the activation endpoint.

        An administratively deactivated account already holds a usable password,
        so it can only obtain a password-reset token. That token must not pass
        activation and must not flip ``is_active`` back to True.
        """
        deactivated = User.objects.create_user(
            username="deactivated.user",
            email="deactivated.user@example.com",
            password="ExistingStrongPassword@1234",
            is_active=False,
        )

        reset_token = default_token_generator.make_token(deactivated)
        url = reverse(
            "accounts:account-activate",
            kwargs={"user_id": deactivated.pk, "token": reset_token},
        )

        response = self.client.post(
            url,
            {"password": "AttackerStrongPassword@1234"},
            format="json",
        )

        deactivated.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(deactivated.is_active)
        self.assertTrue(deactivated.check_password("ExistingStrongPassword@1234"))

    def test_weak_password_is_rejected(self):
        """Verify activation enforces the password-strength policy."""
        token = account_activation_token_generator.make_token(self.user)

        response = self.client.post(
            self._activation_url(token),
            {"password": "1"},
            format="json",
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIsInstance(response.data["password"], list)
        self.assertTrue(response.data["password"])
        self.assertFalse(self.user.has_usable_password())

    def test_already_activated_account_cannot_be_reactivated(self):
        """Verify an active account with a usable password cannot re-activate."""
        active_user = User.objects.create_user(
            username="active.user",
            email="active.user@example.com",
            password="ExistingStrongPassword@1234",
            is_active=True,
        )

        token = account_activation_token_generator.make_token(active_user)
        url = reverse(
            "accounts:account-activate",
            kwargs={"user_id": active_user.pk, "token": token},
        )

        response = self.client.post(
            url,
            {"password": "NewStrongPassword@1234"},
            format="json",
        )

        active_user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["detail"], "This account has already been activated."
        )
        self.assertTrue(active_user.is_active)
        self.assertTrue(active_user.check_password("ExistingStrongPassword@1234"))


@override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
class PasswordChangeSecurityTests(APITestCase):
    """Test application behavior regarding forced password changes."""

    def setUp(self):
        """Initialize a user specifically flagged for a mandatory password change."""
        self.operator_role = Role.objects.get(code=OPERATOR_CODE)
        self.user = User.objects.create_user(
            username="must.change.user",
            email="must.change.user@example.com",
            password="OldStrongPassword@1234",
            role=self.operator_role,
            is_active=True,
            must_change_password=True,
        )

    def test_change_password_clears_must_change_password_flag(self):
        """Verify changing a password removes the 'must_change_password' requirement."""
        self.client.force_authenticate(self.user)

        response = self.client.post(
            reverse("accounts:change-password"),
            {
                "old_password": "OldStrongPassword@1234",
                "new_password": "NewStrongPassword@1234",
            },
            format="json",
        )

        self.user.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(self.user.must_change_password)

    def test_password_reset_confirm_endpoint_is_throttled(self):
        """Verify final password reset stage is rate-limited to prevent bruteforcing."""
        self.user.is_active = True
        self.user.save(update_fields=["is_active"])

        uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": uidb64, "token": token},
        )

        first_response = self.client.post(
            url,
            {"new_password": "ResetStrongPassword@1234"},
            format="json",
        )
        second_response = self.client.post(
            url,
            {"new_password": "AnotherResetStrongPassword@1234"},
            format="json",
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertEqual(second_response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)


class AuditLogExportTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin_user = AdminUserFactory()
        self.client.force_authenticate(self.admin_user)

    def test_audit_log_csv_export_is_sanitized(self):
        """Integration test asserting exported CSV are protected against injection."""

        malicious_description = "=cmd|'/C calc'!A0"
        AuditLog.objects.create(
            actor=self.admin_user,
            action_type=AuditLog.ActionType.USER_CREATED,
            result=AuditLog.ResultStatus.SUCCESS,
            description=malicious_description,
            ip_address="127.0.0.1",
        )
        url = reverse("accounts:audit-log-export")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        content = b"".join(response.streaming_content).decode("utf-8")
        reader = csv.reader(io.StringIO(content))
        rows = list(reader)
        data_row = rows[1]

        self.assertEqual(data_row[-1], f"'{malicious_description}")


# The audit viewset uses DRF's stock ScopedRateThrottle, which reads its rates
# from the THROTTLE_RATES dict captured at import time — so `override_settings`
# can't reach it (unlike the project's custom throttles). Patch that live dict
# instead to exercise the split scopes at controlled, tight rates.
_STOCK_THROTTLE_RATES = "rest_framework.throttling.SimpleRateThrottle.THROTTLE_RATES"


class AuditLogThrottleScopeTests(APITestCase):
    """Verify audit-log viewing and export use independent throttle buckets."""

    def setUp(self):
        """Authenticate an admin and reset any carried-over throttle counters."""
        cache.clear()
        self.admin_user = AdminUserFactory()
        self.client.force_authenticate(self.admin_user)

    def tearDown(self):
        """Clear throttle state so later tests start from a clean bucket."""
        cache.clear()

    @patch.dict(
        _STOCK_THROTTLE_RATES,
        {"audit_view": "5/min", "audit_export": "1/min"},
    )
    def test_view_and_export_throttle_independently(self):
        """List and export must not share a throttle bucket.

        Regression guard: the viewset once applied a single `audit_export` scope
        to every action, so routine dashboard reads could 429 real CSV exports
        (and vice versa). Viewing now has its own, separate `audit_view` scope.
        """
        list_url = reverse("accounts:audit-log-list")
        export_url = reverse("accounts:audit-log-export")

        # Export budget is tight (1/min): first succeeds, second is throttled.
        self.assertEqual(self.client.get(export_url).status_code, 200)
        self.assertEqual(
            self.client.get(export_url).status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )

        # The exhausted export budget must NOT block viewing — separate scope.
        for _ in range(5):
            self.assertEqual(self.client.get(list_url).status_code, 200)

        # ...and the 6th view crosses the *view* budget (5/min), proving reads
        # throttle on audit_view rather than the export bucket.
        self.assertEqual(
            self.client.get(list_url).status_code,
            status.HTTP_429_TOO_MANY_REQUESTS,
        )


class ProtectedProfilePictureRBACTests(APITestCase):
    """Test centralized RBAC access to protected profile pictures."""

    def setUp(self):
        """Create Admin, Operator, and target users."""
        self.admin_role, _ = Role.objects.get_or_create(
            code=ADMIN_CODE,
            defaults={"name": "Administrator"},
        )
        self.operator_role, _ = Role.objects.get_or_create(
            code=OPERATOR_CODE,
            defaults={"name": "Operator"},
        )

        self.admin_user = User.objects.create_user(
            username="profile.admin",
            email="profile.admin@example.com",
            password="StrongPassword123!",
            role=self.admin_role,
            is_active=True,
        )

        self.staff_operator = User.objects.create_user(
            username="profile.staff.operator",
            email="profile.staff.operator@example.com",
            password="StrongPassword123!",
            role=self.operator_role,
            is_active=True,
            is_staff=True,
        )

        self.target_user = User.objects.create_user(
            username="profile.target",
            email="profile.target@example.com",
            password="StrongPassword123!",
            role=self.operator_role,
            is_active=True,
        )
        self.user_without_role = User.objects.create_user(
            username="profile.no.role.picture",
            email="profile.no.role.picture@example.com",
            password="StrongPassword123!",
            is_active=True,
        )

        self.url = reverse(
            "accounts:user-profile-picture",
            kwargs={"user_id": self.target_user.pk},
        )

    def test_admin_has_view_any_profile_permission(self):
        """Ensure the Admin role receives profile.view_any."""
        self.assertTrue(
            user_has_permission(
                self.admin_user,
                PERMISSION_PROFILE_VIEW_ANY,
            )
        )

    def test_non_admin_staff_has_no_view_any_profile_permission(self):
        """Ensure Django staff status does not bypass application RBAC."""
        self.assertFalse(
            user_has_permission(
                self.staff_operator,
                PERMISSION_PROFILE_VIEW_ANY,
            )
        )

    def test_admin_can_access_another_users_profile_picture_endpoint(self):
        """Ensure Admin passes authorization for another user's picture."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            response.data["detail"],
            "User does not have a profile picture.",
        )

    def test_staff_non_admin_cannot_access_another_users_picture(self):
        """Ensure is_staff does not grant access outside RBAC."""
        self.client.force_authenticate(user=self.staff_operator)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_user_can_access_own_profile_picture_endpoint(self):
        """Ensure users retain access to their own profile picture."""
        self.client.force_authenticate(user=self.target_user)

        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
        self.assertEqual(
            response.data["detail"],
            "User does not have a profile picture.",
        )

    def test_authenticated_user_without_role_cannot_access_own_profile_picture(self):
        """Ensure self-profile picture access requires explicit RBAC permission."""
        own_url = reverse(
            "accounts:user-profile-picture",
            kwargs={"user_id": self.user_without_role.pk},
        )
        self.client.force_authenticate(user=self.user_without_role)

        response = self.client.get(own_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_anonymous_user_cannot_access_profile_picture(self):
        """Ensure profile pictures require authentication."""
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


class UserListViewTests(APITestCase):
    """Test the paginated user list endpoint."""

    def setUp(self):
        """Set up the URL, an admin viewer, and users to list and filter."""
        self.url = reverse("accounts:user-create")
        self.admin_role = Role.objects.get(code=ADMIN_CODE)
        self.operator_role = Role.objects.get(code=OPERATOR_CODE)
        self.unit = MilitaryUnitFactory(name="Alpha Company", code="ALPHA")

        self.admin_user = AdminUserFactory()
        self.viewer_user = ViewerUserFactory()

        self.operator = User.objects.create_user(
            username="petro.melnyk",
            email="petro.melnyk@example.com",
            password="StrongPassword123!",
            first_name="Petro",
            last_name="Melnyk",
            role=self.operator_role,
            unit=self.unit,
            is_active=True,
            created_by=self.admin_user,
        )
        self.inactive_user = User.objects.create_user(
            username="inactive.ivan",
            email="inactive.ivan@example.com",
            password="StrongPassword123!",
            first_name="Ivan",
            last_name="Shevchenko",
            role=self.operator_role,
            is_active=False,
        )

    def test_admin_can_list_users_with_expected_row_fields(self):
        """Admins receive a paginated list where each row carries the row data."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("results", response.data)

        row = next(
            item
            for item in response.data["results"]
            if item["username"] == "petro.melnyk"
        )
        self.assertEqual(row["role"], self.operator_role.id)
        self.assertEqual(row["role_code"], OPERATOR_CODE)
        self.assertEqual(row["unit"], self.unit.id)
        self.assertEqual(row["unit_name"], "Alpha Company")
        self.assertTrue(row["is_active"])
        self.assertEqual(row["created_by_username"], self.admin_user.username)
        self.assertIn("last_login", row)

    def test_search_matches_name_and_email(self):
        """The search query filters users by name and email fragments."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"search": "petro.melnyk@example.com"})

        usernames = [row["username"] for row in response.data["results"]]
        self.assertEqual(usernames, ["petro.melnyk"])

    def test_filter_by_role(self):
        """The role filter narrows results to users with the given role id."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"role": self.operator_role.id})

        returned_roles = {row["role"] for row in response.data["results"]}
        self.assertEqual(returned_roles, {self.operator_role.id})

    def test_filter_by_unit_and_active_status(self):
        """The unit and is_active filters can be combined."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(
            self.url, {"unit": self.unit.id, "is_active": "true"}
        )

        usernames = [row["username"] for row in response.data["results"]]
        self.assertEqual(usernames, ["petro.melnyk"])

    def test_filter_inactive_users(self):
        """Filtering by is_active=false returns only deactivated users."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.url, {"is_active": "false"})

        usernames = [row["username"] for row in response.data["results"]]
        self.assertIn("inactive.ivan", usernames)
        self.assertNotIn("petro.melnyk", usernames)

    def test_user_without_view_permission_is_forbidden(self):
        """Users without the users view permission cannot list users."""
        self.client.force_authenticate(user=self.viewer_user)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class MilitaryUnitViewTests(APITestCase):
    """Test the military unit list, create, and update endpoints."""

    def setUp(self):
        """Set up URLs, an admin manager, and a viewer without unit permissions."""
        self.list_url = reverse("accounts:military-unit-list")
        self.admin_user = AdminUserFactory()
        self.viewer_user = ViewerUserFactory()
        self.unit = MilitaryUnitFactory(name="Bravo Company", code="BRAVO")

    def _detail_url(self, unit):
        """Return the detail URL for the supplied unit."""
        return reverse("accounts:military-unit-detail", kwargs={"pk": unit.pk})

    def test_admin_can_list_units_with_counts(self):
        """The list response includes drone_count and user_count per unit."""
        DroneFactory(military_unit=self.unit)
        DroneFactory(military_unit=self.unit)
        ViewerUserFactory(unit=self.unit)
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        row = next(item for item in response.data["results"] if item["code"] == "BRAVO")
        self.assertEqual(row["drone_count"], 2)
        self.assertEqual(row["user_count"], 1)

    def test_search_by_code(self):
        """Units can be searched by code."""
        MilitaryUnitFactory(name="Charlie Company", code="CHARLIE")
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.get(self.list_url, {"search": "BRAVO"})

        codes = [row["code"] for row in response.data["results"]]
        self.assertEqual(codes, ["BRAVO"])

    def test_admin_can_create_unit(self):
        """Admins can create a military unit."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            self.list_url,
            {
                "name": "Delta Company",
                "code": "DELTA",
                "description": "Reserve formation.",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MilitaryUnit.objects.filter(code="DELTA").exists())
        self.assertEqual(response.data["drone_count"], 0)
        self.assertEqual(response.data["user_count"], 0)

    def test_create_rejects_duplicate_code_case_insensitively(self):
        """Creating a unit with an existing code (any case) is rejected."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(
            self.list_url,
            {"name": "Bravo Clone", "code": "bravo"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("code", response.data)

    def test_viewer_cannot_create_unit(self):
        """Users without the units manage permission cannot create units."""
        self.client.force_authenticate(user=self.viewer_user)

        response = self.client.post(
            self.list_url,
            {"name": "Echo Company", "code": "ECHO"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_patch_is_active(self):
        """Admins can deactivate a unit via PATCH."""
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.patch(
            self._detail_url(self.unit),
            {"is_active": False},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_active"])
        self.unit.refresh_from_db()
        self.assertFalse(self.unit.is_active)

    def test_viewer_cannot_patch_unit(self):
        """Users without the units manage permission cannot update units."""
        self.client.force_authenticate(user=self.viewer_user)

        response = self.client.patch(
            self._detail_url(self.unit),
            {"is_active": False},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class AuditLogRBACTests(APITestCase):
    """Test RBAC restrictions for audit log endpoints."""

    def test_user_without_audit_permissions_gets_forbidden(self):
        """Ensure users without an RBAC role cannot view audit logs."""
        user = User.objects.create_user(
            username="no.audit.role",
            email="no.audit.role@example.com",
            password="StrongPassword123!",
            is_active=True,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(
            reverse("accounts:audit-log-list"),
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
