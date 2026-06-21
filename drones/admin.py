from django.contrib import admin

from .models import (
    Drone,
    DroneModel,
    DroneSpec,
    DroneSpecChangeLog,
    DroneStatusHistory,
    WriteOffRecord,
)


@admin.register(Drone)
class DroneAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "serial_number",
        "inventory_number",
        "name",
        "drone_model__name",
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
        "battery_model",
        "camera_model",
        "vtx_model",
        "technical_documentation_url",
        "is_firmware_outdated",
    )
    search_fields = (
        "drone__serial_number",
        "drone__inventory_number",
        "frame_type",
        "motor_model",
        "battery_type",
        "battery_model",
        "camera_model",
        "vtx_model",
        "flight_controller",
        "communication_protocol",
    )
    list_filter = ("battery_type", "frame_type", "is_firmware_outdated", "updated_at")


@admin.register(DroneSpecChangeLog)
class DroneSpecChangeLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drone_spec",
        "changed_by",
        "changed_fields",
        "created_at",
    )
    search_fields = (
        "drone_spec__drone__serial_number",
        "drone_spec__drone__inventory_number",
        "drone_spec__drone__name",
    )
    list_filter = ("created_at",)
    readonly_fields = (
        "drone_spec",
        "changed_by",
        "changed_fields",
        "old_values",
        "new_values",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(WriteOffRecord)
class WriteOffRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "drone",
        "reason",
        "authorized_by",
        "related_mission",
        "document_number",
        "written_off_at",
        "created_at",
    )
    search_fields = (
        "drone__name",
        "drone__serial_number",
        "drone__inventory_number",
        "reason",
        "reason_description",
        "document_number",
        "authorized_by__username",
    )
    list_filter = (
        "reason",
        "written_off_at",
        "created_at",
        "authorized_by",
    )
    readonly_fields = (
        "drone",
        "reason",
        "reason_description",
        "authorized_by",
        "related_mission",
        "document_number",
        "written_off_at",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return super().has_view_permission(
            request, obj
        ) or super().has_change_permission(
            request,
            obj,
        )

    def has_delete_permission(self, request, obj=None):
        return False


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


@admin.register(DroneModel)
class DroneModelAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "manufacturer",
        "supported_classifications",
        "is_active",
        "created_at",
    )
    search_fields = ("name", "manufacturer", "supported_classifications")
    list_filter = ("is_active", "created_at")
