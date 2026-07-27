"""Test suite for user accounts, role management, authentication. """

import csv
import io
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient, APIRequestFactory, APITestCase

from drones.factories import AdminUserFactory
from roles.models import ADMIN_CODE, OPERATOR_CODE, Role
from seed_data.users import seed_users

from .models import AuditLog, User, UserRoleAuditLog, UserStatusLog
from .permissions import user_has_permission
from .rbac import PERMISSION_PROFILE_VIEW_ANY
from .services import update_user_role
from .throttles import AccountActivationThrottle, PasswordResetRequestThrottle
from .tokens import account_activation_token_generator

THROTTLE_TEST_SETTINGS = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
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
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
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

    def test_unauthenticated_user_cannot_access(self):
        """Verify that anonymous users are blocked from accessing password change."""
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PasswordResetConfirmViewTests(APITestCase):
    """Test the password reset confirmation API endpoint via token."""

    def setUp(self):
        """Set up a user and generate valid base64 and token parameters."""
        self.user = User.objects.create_user(
            username="resetuser", email="test@example.com", password="OldPassword123!"
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
        self.user = User.objects.create_user(
            username="must.change.user",
            email="must.change.user@example.com",
            password="OldStrongPassword@1234",
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

    def test_anonymous_user_cannot_access_profile_picture(self):
        """Ensure profile pictures require authentication."""
        response = self.client.get(self.url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )


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
