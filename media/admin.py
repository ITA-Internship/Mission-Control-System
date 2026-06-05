from django.contrib import admin
from django.template.defaultfilters import filesizeformat

from .models import MissionArtifact


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



