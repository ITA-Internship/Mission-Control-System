from io import StringIO
from types import SimpleNamespace

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
from rest_framework.test import APIRequestFactory, APITestCase

from unittest.mock import patch

from roles.models import ADMIN_CODE, OPERATOR_CODE, Role
from seed_data.users import seed_users

from .models import AuditLog, User, UserRoleAuditLog, UserStatusLog
from .services import update_user_role
from .throttles import AccountActivationThrottle, PasswordResetRequestThrottle

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
    def setUp(self):
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
    def setUp(self):
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
        self.client.force_authenticate(user=self.admin_user)

        url = reverse("accounts:user-status-update", kwargs={"pk": self.admin_user.pk})
        payload = {"is_active": False, "reason": "Quitting"}

        response = self.client.patch(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("cannot deactivate your own account", response.data["detail"])

        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active)

    def test_unchanged_status_returns_200_with_message(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {"is_active": True}

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "User is already active.")

        self.assertFalse(UserStatusLog.objects.exists())

    def test_invalid_payload_returns_400(self):
        self.client.force_authenticate(user=self.admin_user)
        payload = {"is_active": "not-a-boolean"}

        response = self.client.patch(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ChangePasswordViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="testuser@example.com",
            password="OldPassword123!",
        )
        self.url = reverse("accounts:change-password")

    def test_change_password_success(self):
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
        response = self.client.post(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PasswordResetConfirmViewTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser", email="test@example.com", password="OldPassword123!"
        )
        self.uidb64 = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

        self.url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": self.uidb64, "token": self.token},
        )

    @patch("accounts.views.send_mail")
    def test_password_reset_success(self, mock_send_mail):
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

    def test_password_reset_invalid_token(self):
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
        invalid_url = reverse(
            "accounts:password-reset-confirm",
            kwargs={"uidb64": "invalid-uid", "token": self.token},
        )
        payload = {"new_password": "BrandNewPassword123!"}

        response = self.client.post(invalid_url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("invalid or has expired", response.data["detail"])
class SeedDbSecurityTests(TestCase):
    @override_settings(DEBUG=False)
    def test_seed_db_is_blocked_outside_debug_mode(self):
        with self.assertRaisesMessage(
            CommandError,
            "seed_db is allowed only in local development when DEBUG=True.",
        ):
            call_command("seed_db", module="users")

    def test_seed_users_use_provided_password_and_require_password_change(self):
        seed_password = "TemporarySeedPassword@123"

        stats = seed_users(seed_password=seed_password)
        seeded_user = User.objects.get(username="root.admin")

        self.assertEqual(stats["users_created"], 11)
        self.assertTrue(seeded_user.check_password(seed_password))
        self.assertTrue(seeded_user.must_change_password)

    def test_seed_users_do_not_force_password_change_when_password_is_unchanged(self):
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
        with self.assertRaisesMessage(
            CommandError,
            "Seeding users requires --password or SEED_DEFAULT_PASSWORD.",
        ):
            call_command("seed_db", module="users")

    def test_disable_seeded_users_deactivates_existing_seeded_accounts(self):
        seed_users(seed_password="TemporarySeedPassword@123")
        out = StringIO()

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
    def setUp(self):
        cache.clear()
        self.request_factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="throttle.user",
            email="throttle.user@example.com",
            password="StrongTest@1234",
            is_active=False,
        )

    def test_activation_endpoint_is_throttled(self):
        token = default_token_generator.make_token(self.user)
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
        with self.assertRaisesMessage(
            ImproperlyConfigured,
            "Missing throttle rate for scope 'account_activation'.",
        ):
            AccountActivationThrottle()

    def test_throttle_cache_key_uses_authenticated_user_when_available(self):
        request = self.request_factory.post("/password-reset/")
        request.user = self.user
        request.data = {"email": "shared@example.com"}
        view = SimpleNamespace(kwargs={})

        cache_key = PasswordResetRequestThrottle().get_cache_key(request, view)

        self.assertIn(f"user:{self.user.pk}", cache_key)

    def test_password_reset_throttle_cache_key_is_scoped_by_email(self):
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


@override_settings(REST_FRAMEWORK=THROTTLE_TEST_SETTINGS)
class PasswordChangeSecurityTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="must.change.user",
            email="must.change.user@example.com",
            password="OldStrongPassword@1234",
            is_active=True,
            must_change_password=True,
        )

    def test_change_password_clears_must_change_password_flag(self):
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
