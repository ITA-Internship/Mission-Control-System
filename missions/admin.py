from django.contrib import admin

from .models import Mission, MissionDrone


class MissionDroneInline(admin.TabularInline):
    model = MissionDrone
    extra = 0
    fields = ("drone", "condition_after")



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
