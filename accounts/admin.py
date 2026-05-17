from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import AuditLog, MilitaryUnit, User, UserProfile, UserRoleAuditLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "id",
        "username",
        "email",
        "role",
        "unit",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_superuser", "is_active", "role", "unit")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("id",)
    autocomplete_fields = ("role", "unit", "created_by")
    readonly_fields = ("created_at", "updated_at")

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
    list_display = ("id", "name", "code", "is_active", "created_at", "updated_at")
    search_fields = ("name", "code")
    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("id",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "rank", "contact", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "rank", "contact")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("id",)


@admin.register(UserRoleAuditLog)
class UserRoleAuditLogAdmin(admin.ModelAdmin):
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
        return False

    has_add_permission = _read_only_permission
    has_change_permission = _read_only_permission
    has_delete_permission = _read_only_permission


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
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
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
