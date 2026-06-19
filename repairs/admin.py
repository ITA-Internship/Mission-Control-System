from django.contrib import admin

from .models import ComponentReplacement, DefectReport


@admin.register(DefectReport)
class DefectReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drone",
        "defect_type",
        "severity",
        "reporter",
        "detected_at",
        "created_at",
    )
    list_filter = ("severity", "defect_type", "detected_at")
    search_fields = (
        "drone__serial_number",
        "drone__inventory_number",
        "description",
    )


@admin.register(ComponentReplacement)
class ComponentReplacementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drone",
        "component_type",
        "component_name",
        "old_serial_number",
        "new_serial_number",
        "replaced_by",
        "replaced_at",
        "created_at",
    )
    list_filter = ("component_type", "replaced_at", "created_at", "replaced_by")
    search_fields = (
        "drone__serial_number",
        "drone__inventory_number",
        "component_name",
        "old_serial_number",
        "new_serial_number",
        "reason",
        "replaced_by__username",
    )
    readonly_fields = ("replaced_by", "created_at", "updated_at")
    fields = (
        "drone",
        "component_type",
        "component_name",
        "old_serial_number",
        "new_serial_number",
        "reason",
        "replaced_at",
        "replaced_by",
        "created_at",
        "updated_at",
    )

    def save_model(self, request, obj, form, change):
        if request.user.is_authenticated:
            obj.replaced_by = request.user
        super().save_model(request, obj, form, change)

    def has_delete_permission(self, request, obj=None):
        return False
