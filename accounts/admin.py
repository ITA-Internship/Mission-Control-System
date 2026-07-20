"""Configure Django admin interface for Users, Military Unit and Audit Log. """

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    AuditLog,
    MilitaryUnit,
    User,
    UserProfile,
    UserRoleAuditLog,
    UserStatusLog,
)


class UserProfileInline(admin.StackedInline):
    """Provide inline admin interface for UserProfile within the User admin."""

    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile Information"
    fk_name = "user"
    fields = ("rank", "contact", "profile_picture")


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Configure admin search, filter, and display for the custom User model."""

    list_display = (
        "id",
        "username",
        "email",
        "role",
        "unit",
        "is_staff",
        "is_active",
    )
    list_editable = ("is_active",)
    list_filter = ("is_staff", "is_superuser", "is_active", "role", "unit")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("id",)
    autocomplete_fields = ("role", "unit", "created_by")
    readonly_fields = ("created_at", "updated_at")

    inlines = (UserProfileInline,)

    fieldsets = UserAdmin.fieldsets + (
        (
            "Assignments",
            {
                "fields": (
                    "role",
                    "unit",
                    "created_by",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Assignments", {"fields": ("email", "role", "unit", "created_by")}),
    )


@admin.register(MilitaryUnit)
class MilitaryUnitAdmin(admin.ModelAdmin):
    """Configure admin interface for Military Unit management."""

    list_display = ("id", "name", "code", "is_active", "created_at", "updated_at")
    search_fields = ("name", "code")
    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("id",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Configure admin interface for standalone User Profile management."""

    list_display = ("id", "user", "rank", "contact", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "rank", "contact")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("id",)


@admin.register(UserStatusLog)
class UserStatusLogAdmin(admin.ModelAdmin):
    """Configure read-only admin interface for user status change logs."""

    list_display = (
        "target_user",
        "changed_by",
        "old_status",
        "new_status",
        "created_at",
    )
    readonly_fields = (
        "created_at",
        "target_user",
        "changed_by",
        "old_status",
        "new_status",
        "reason",
    )

    def has_add_permission(self, request):
        """Reject manual creation of user status logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Reject manual deletion of user status logs."""
        return False


@admin.register(UserRoleAuditLog)
class UserRoleAuditLogAdmin(admin.ModelAdmin):
    """Configure read-only admin interface for user role audit logs."""

    list_display = (
        "id",
        "target_user",
        "previous_role",
        "new_role",
        "changed_by",
        "changed_at",
    )
    list_filter = ("previous_role", "new_role", "changed_at")
    search_fields = (
        "target_user__username",
        "target_user__email",
        "changed_by__username",
        "changed_by__email",
    )
    readonly_fields = (
        "target_user",
        "previous_role",
        "new_role",
        "changed_by",
        "changed_at",
    )
    ordering = ("-changed_at",)
    date_hierarchy = "changed_at"
    list_select_related = ("target_user", "previous_role", "new_role", "changed_by")

    def _read_only_permission(self, request, obj=None):
        """Reject manual adding, changing, or deleting of role audit logs."""
        return False

    has_add_permission = _read_only_permission
    has_change_permission = _read_only_permission
    has_delete_permission = _read_only_permission


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Configure read-only admin interface for audit log records."""

    list_display = (
        "created_at",
        "actor",
        "action_type",
        "target_user",
        "result",
        "ip_address",
    )
    list_filter = ("action_type", "result", "created_at", "ip_address")
    search_fields = (
        "actor__username",
        "target_user__username",
        "description",
        "ip_address",
    )
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        """Reject manual creation audit logs."""
        return False

    def has_change_permission(self, request, obj=None):
        """Reject manual updates to existing audit logs."""
        return False

    def has_delete_permission(self, request, obj=None):
        """Reject manual deletion of audit logs."""
        return False

    def get_actions(self, request):
        """Reject the default 'delete_selected' action to project log integrity."""
        actions = super().get_actions(request)
        if "delete_selected" in actions:
            del actions["delete_selected"]
        return actions
