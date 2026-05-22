from django.contrib import admin

from .models import Drone, DroneSpec, DroneStatusHistory, WriteOffRecord


@admin.register(Drone)
class DroneAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "serial_number",
        "inventory_number",
        "name",
        "drone_model",
        "classification",
        "military_unit__name",
        "status",
    )
    search_fields = (
        "serial_number",
        "inventory_number",
        "name",
        "military_unit__name",
        "military_unit__code",
    )
    list_filter = ("status", "created_at", "military_unit")


@admin.register(DroneSpec)
class DroneSpecAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drone",
        "frame_type",
        "motor_model",
        "battery_type",
        "camera_model",
        "vtx_model",
    )
    search_fields = (
        "drone__serial_number",
        "drone__inventory_number",
        "frame_type",
        "motor_model",
        "camera_model",
    )


@admin.register(WriteOffRecord)
class WriteOffRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drone",
        "reason",
        "authorized_by",
        "document_number",
        "written_off_at",
        "created_at",
    )
    search_fields = (
        "drone__serial_number",
        "drone__inventory_number",
        "reason",
        "document_number",
    )
    list_filter = ("written_off_at", "created_at")


@admin.register(DroneStatusHistory)
class DroneStatusHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drone",
        "from_status",
        "to_status",
        "changed_by",
        "created_at",
    )
    search_fields = (
        "drone__serial_number",
        "drone__inventory_number",
        "reason",
    )
    list_filter = ("from_status", "to_status", "created_at")
