from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import MilitaryUnit, User, UserProfile, UserStatusLog


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "email", "role", "is_staff", "is_active")
    list_editable = ("is_active",)
    list_filter = ("is_staff", "is_superuser", "is_active", "role")
    search_fields = ("username", "email", "first_name", "last_name")
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
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Assignments", {"fields": ("email", "role", "unit", "created_by")}),
    )

    readonly_fields = ("created_at", "updated_at")


@admin.register(MilitaryUnit)
class MilitaryUnitAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "code", "is_active", "created_at", "updated_at")
    search_fields = ("name", "code")
    list_filter = ("is_active",)
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "rank", "contact", "created_at", "updated_at")
    search_fields = ("user__username", "user__email", "rank", "contact")
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserStatusLog)
class UserStatusLogAdmin(admin.ModelAdmin):
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
        return False

    def has_delete_permission(self, request, obj=None):
        return False
