from django.contrib import admin
from django.template.defaultfilters import filesizeformat

from .models import MediaAuditLog, MissionArtifact


@admin.register(MissionArtifact)
class MissionArtifactAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "mission",
        "file_type",
        "formatted_file_size",
        "uploaded_by",
        "uploaded_at",
    )
    list_display_links = ("id", "title")
    list_filter = ("file_type", "storage_backend", "uploaded_at")
    search_fields = ("title", "description", "original_filename")
    list_select_related = ("mission", "uploaded_by")
    readonly_fields = (
        "original_filename",
        "file_size",
        "file_type",
        "storage_backend",
        "uploaded_at",
    )
    raw_id_fields = ("mission", "uploaded_by")
    date_hierarchy = "uploaded_at"
    ordering = ("-uploaded_at",)

    @admin.display(description="File Size", ordering="file_size")
    def formatted_file_size(self, obj):
        return filesizeformat(obj.file_size)


@admin.register(MediaAuditLog)
class MediaAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "action",
        "artifact",
        "mission",
        "user",
        "ip_address",
        "created_at",
    )
    list_display_links = ("id",)
    list_filter = ("action", "created_at")
    search_fields = ("user__username", "ip_address", "changes")
    list_select_related = ("artifact", "mission", "user")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    readonly_fields = [f.name for f in MediaAuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
