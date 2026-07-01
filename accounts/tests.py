from io import StringIO

from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from roles.models import ADMIN_CODE, OPERATOR_CODE, Role
from seed_data.users import seed_users

from .models import AuditLog, User, UserRoleAuditLog
from .services import update_user_role

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
