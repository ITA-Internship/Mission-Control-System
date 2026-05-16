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


class UserStatusLog(models.Model):
    target_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="status_logs"
    )
    changed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="performed_status_changes",
    )
    old_status = models.BooleanField()
    new_status = models.BooleanField()
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Change for {self.target_user} by {self.changed_by}"


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
