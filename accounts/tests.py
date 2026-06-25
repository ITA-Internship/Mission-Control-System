from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.test import TestCase
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APITestCase

from roles.models import ADMIN_CODE, OPERATOR_CODE, Role

from .models import AuditLog, User, UserRoleAuditLog, UserStatusLog
from .services import update_user_role


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
