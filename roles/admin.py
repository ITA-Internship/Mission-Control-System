from django.contrib import admin
from django.db.models import Count

from .models import Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "users_count", "created_at", "updated_at")
    search_fields = ("code", "name")
    list_filter = ("code",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("id",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.annotate(users_total=Count("users"))

    @admin.display(description="Users")
    def users_count(self, obj):
        return obj.users_total

    def has_delete_permission(self, request, obj=None):
        return False
