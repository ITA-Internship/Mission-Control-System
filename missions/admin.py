from django.contrib import admin

from .models import Mission, MissionAuditLog, MissionDrone


class MissionDroneInline(admin.TabularInline):
    model = MissionDrone
    extra = 0
    fields = ("drone", "operator", "condition_after")


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "status",
        "commander",
        "started_at",
        "created_by",
        "created_at",
    )
    list_filter = ("status", "result")
    search_fields = ("title", "location_description")
    readonly_fields = ("created_at", "updated_at")
    inlines = [MissionDroneInline]


@admin.register(MissionDrone)
class MissionDroneAdmin(admin.ModelAdmin):
    list_display = ("id", "mission", "drone", "operator", "created_at")
    list_select_related = ("mission", "drone", "operator")
    list_filter = ("mission__status",)
    raw_id_fields = ("mission", "drone", "operator")


@admin.register(MissionAuditLog)
class MissionAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "action", "target_model", "target_id", "created_at", "user")
    list_filter = ("action", "target_model")
    readonly_fields = (
        "action",
        "target_model",
        "target_id",
        "changes",
        "user",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
