"""Define User models, military units, and audit logs.

Classes:
    MilitaryUnit: Represents a military unit with name, code, and description.
    User: Represents a user with email, role, and unit information.
    UserProfile: Represents a user's profile
    with rank, contact information, and profile picture.
    UserStatusLog: Represents a log of user status changes.
    UserRoleAuditLog: Represents a log of user role changes.
    AuditLogQuerySet: A custom query set for audit logs.
    AuditLogManager: A custom manager for audit logs.
    AuditLog: Immutable records of different actions that users can perform.
    UserSession: Tracks active user sessions for security and monitoring.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models

from .validators import validate_image_extension, validate_image_size


class MilitaryUnit(models.Model):
    """Represent a military unit catalog entry.

    A military unit model defines a name, code, description,
    and active status of a unit.
    """

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Return a string representation of the military unit."""
        return f"{self.name} ({self.code})"


class User(AbstractUser):
    """Represent a user in the system.

    This model extends Django's AbstractUser
    to include additional fields such as email, role,
    military unit, and creator information.

    Important fields:
        role: Current role of user in the system.
        unit: Military unit the user belongs to.
        created_by: User who created this user record.
    """

    email = models.EmailField(unique=True)
    must_change_password = models.BooleanField(default=False)
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
        """Return a string representation of the user."""
        return self.username


class UserProfile(models.Model):
    """Represent a user profile in the system.

    This model is linked to the User model
    via a one-to-one relationship and includes additional
    fields such as rank, contact information, and profile picture.
    """

    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="profile"
    )
    rank = models.CharField(max_length=100, blank=True)
    contact = models.CharField(max_length=255, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        blank=True,
        null=True,
        validators=[validate_image_size, validate_image_extension],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        """Return a string representation of the user profile."""
        return f"Profile for {self.user_id}"


class UserStatusLog(models.Model):
    """Store logs of user status changes for auditing purposes.

    This model records the changes in user status
    along with the user who made the change,
    the old and new status, the reason for the change, and the timestamp.
    """

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
        """Return a string representation of the user status log entry."""
        action = "activated" if self.new_status else "deactivated"
        date_str = (
            self.created_at.strftime("%Y-%m-%d") if self.created_at else "pending date"
        )
        return f"User {self.target_user} {action} by {self.changed_by} on {date_str}"


class UserRoleAuditLog(models.Model):
    """Store logs of user role changes for auditing purposes.

    This model records the changes in user roles
    along with the user who made the change,
    the previous and new roles, and the timestamp of the change.
    """

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
        """Return a string representation of the user role audit log."""
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


class AuditLogQuerySet(models.QuerySet):
    """A custom QuerySet for the AuditLog model that prevents deletion and updates."""

    def delete(self):
        """Override delete method to prevent deletion of AuditLog entries."""
        raise ValueError("AuditLog entries are immutable and cannot be deleted.")

    def update(self, **kwargs):
        """Override update method to prevent updates to AuditLog entries."""
        raise ValueError("AuditLog entries are immutable and cannot be updated.")


class AuditLogManager(models.Manager):
    """Custom manager for AuditLog
    to enforce read-only database operations using AuditLogQuerySet."""

    def get_queryset(self):
        """Return a restricted query set that prevents record modification."""
        return AuditLogQuerySet(self.model, using=self._db)


class AuditLog(models.Model):
    """Store immutable records of different actions
    that users can perform in the system.

    Important fields:
        actor: The user who performed the action.
        target_user: The user on whom the action was performed.
        action_type: The specific action performed (e.g., login, password change).
        result: The final outcome of the action (Success or Failed).
    """

    class ActionType(models.TextChoices):
        """Configure different action types for Audit Log."""

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
        """Configure SUCCESS/FAILED status for Audit Log."""

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

    objects = AuditLogManager()

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"

    def __str__(self) -> str:
        """Return a string representation of the audit log entry."""
        actor_name = self.actor.username if self.actor else "System/Anonymous"
        return (
            f"[{self.created_at.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{actor_name} - {self.action_type} ({self.result})"
        )

    def save(self, *args, **kwargs):
        """Override save method to prevent updating existing AuditLog entries."""
        if not self._state.adding:
            raise ValueError("AuditLog entries are immutable and cannot be updated.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Override the delete method to prevent deletion of AuditLog entries."""
        raise ValueError("AuditLog entries are immutable and cannot be deleted.")


class UserSession(models.Model):
    """Track active user sessions to manage concurrent logins
    or session-based security auditing."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tracked_sessions",
    )
    session_key = models.CharField(max_length=40, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "session_key"], name="unique_user_session"
            )
        ]
        indexes = [
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        """Return a string representation of the tracked user session."""
        return f"Session {self.session_key[:8]}… for {self.user}"
