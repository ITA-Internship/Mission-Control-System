from django.contrib.auth.models import AbstractUser
from django.db import models


class MilitaryUnit(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.code})"


class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.ForeignKey(
        "roles.Role",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="users",
    )

    unit = models.ForeignKey(
        MilitaryUnit,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="users",
    )

    created_by = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_users",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.username


class UserProfile(models.Model):
    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="profile"
    )
    rank = models.CharField(max_length=100, blank=True)
    contact = models.CharField(max_length=255, blank=True)
    profile_picture = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Profile for {self.user_id}"


class UserRoleAuditLog(models.Model):
    changed_by = models.ForeignKey(
        "accounts.User",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="role_changes_made",
    )
    target_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="role_change_logs",
    )
    previous_role = models.ForeignKey(
        "roles.Role",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="previous_role_audit_logs",
    )
    new_role = models.ForeignKey(
        "roles.Role",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="new_role_audit_logs",
    )
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-changed_at",)

    def __str__(self) -> str:
        target_username = (
            self.target_user.username if self.target_user else "Unknown user"
        )
        previous_role_name = (
            self.previous_role.name if self.previous_role else "No role"
        )
        new_role_name = self.new_role.name if self.new_role else "No role"
        return (
            f"Role change for {target_username}: "
            f"{previous_role_name} -> {new_role_name}"
        )


class AuditLog(models.Model):
    class ActionType(models.TextChoices):
        LOGIN_SUCCESS = "LOGIN_SUCCESS", "Login Success"
        LOGIN_FAILED = "LOGIN_FAILED", "Login Failed"
        LOGOUT = "LOGOUT", "Logout"
        USER_CREATED = "USER_CREATED", "User Created"
        ROLE_CHANGED = "ROLE_CHANGED", "Role Changed"
        ACCOUNT_ACTIVATED = "ACCOUNT_ACTIVATED", "Account Activated"
        ACCOUNT_DEACTIVATED = "ACCOUNT_DEACTIVATED", "Account Deactivated"
        PROFILE_UPDATED = "PROFILE_UPDATED", "Profile Updated"
        PASSWORD_CHANGED = "PASSWORD_CHANGED", "Password Changed"
        PASSWORD_RESET_REQUESTED = (
            "PASSWORD_RESET_REQUESTED",
            "Password Reset Requested",
        )
        PERMISSION_DENIED = "PERMISSION_DENIED", "Permission Denied"

    class ResultStatus(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"

    actor = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions_performed",
        help_text="User performing the action (can be Null for system actions)",
    )
    target_user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="actions_received",
        help_text="User on whom the action was taken",
    )
    action_type = models.CharField(
        max_length=50, choices=ActionType.choices, db_index=True
    )
    result = models.CharField(
        max_length=20, choices=ResultStatus.choices, db_index=True
    )
    description = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self) -> str:
        actor_name = self.actor.username if self.actor else "System/Anonymous"
        return (
            f"[{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{actor_name} - {self.action_type} ({self.result})"
        )

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("AuditLog entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("AuditLog entries are immutable and cannot be deleted.")
