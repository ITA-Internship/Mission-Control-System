from django.contrib import admin
from .models import Drone, DroneSpec


@admin.register(Drone)
class DroneAdmin(admin.ModelAdmin):
    list_display = ("id", "serial_number", "inventory_number", "name", "drone_model", "status")
    search_fields = ("serial_number", "inventory_number", "name")
    list_filter = ("status", "created_at")


@admin.register(DroneSpec)
class DroneSpecAdmin(admin.ModelAdmin):
    list_display = ("id", "drone", "frame_type", "motor_model", "battery_type", "camera_model", "vtx_model")
    search_fields = ("drone__serial_number", "drone__inventory_number", "frame_type", "motor_model", "camera_model")