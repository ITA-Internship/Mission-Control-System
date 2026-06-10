from django.contrib import admin

from .models import DefectReport


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
