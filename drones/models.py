import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Drone(models.Model):

    STATUS_ACTIVE = "ACTIVE"
    STATUS_DAMAGED = "DAMAGED"
    STATUS_LOST = "LOST"
    STATUS_MAINTENANCE = "MAINTENANCE"
    STATUS_DECOMMISSIONED = "DECOMMISSIONED"
    STATUS_SOLD = "SOLD"
    STATUS_TRANSFERRED = "TRANSFERRED"
    STATUS_WRITTEN_OFF = "WRITTEN_OFF"

    STATUS_CHOICES = [
<<<<<<< HEAD
        ("ACTIVE", "Active"),
        ("DAMAGED", "Damaged"),
        ("LOST", "Lost"),
        ("MAINTENANCE", "Maintenance"),
        ("IN_MISSION", "in_mission"),
=======
        (STATUS_ACTIVE, "Active"),
        (STATUS_DAMAGED, "Damaged"),
        (STATUS_LOST, "Lost"),
        (STATUS_MAINTENANCE, "Maintenance"),
        (STATUS_DECOMMISSIONED, "Decommissioned"),
        (STATUS_SOLD, "Sold"),
        (STATUS_TRANSFERRED, "Transferred"),
        (STATUS_WRITTEN_OFF, "Written off"),
>>>>>>> develop
    ]

    INACTIVE_STATUSES = (
        STATUS_DECOMMISSIONED,
        STATUS_SOLD,
        STATUS_TRANSFERRED,
        STATUS_WRITTEN_OFF,
    )

    serial_number = models.CharField(max_length=100, unique=True)
    inventory_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    drone_model = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")
    military_unit = models.ForeignKey(
        "accounts.MilitaryUnit",
        on_delete=models.PROTECT,
        related_name="drones",
    )
    acquired_at = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.name} {self.drone_model} - {self.serial_number}"


class DroneSpec(models.Model):
    drone = models.OneToOneField(Drone, on_delete=models.CASCADE, related_name="spec")
    frame_type = models.CharField(max_length=255)
    motor_model = models.CharField(max_length=255)
    battery_type = models.CharField(max_length=255)
    battery_capacity_mah = models.PositiveIntegerField()
    camera_model = models.CharField(max_length=255)
    vtx_model = models.CharField(max_length=255, blank=True)
    flight_controller = models.CharField(max_length=255)
    firmware_version = models.CharField(max_length=255, blank=True)
    max_speed_kmh = models.DecimalField(max_digits=6, decimal_places=2)
    max_range_km = models.DecimalField(max_digits=6, decimal_places=2)
    max_flight_time_min = models.DecimalField(max_digits=6, decimal_places=2)
    frequency_mhz = models.PositiveIntegerField()
    payload_capacity_g = models.PositiveIntegerField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Specification for {self.drone}"


class WriteOffRecord(models.Model):
    drone = models.OneToOneField(
        Drone, on_delete=models.PROTECT, related_name="writeoff_record"
    )
    reason = models.CharField(max_length=255)
    reason_description = models.TextField(blank=True)
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="authorized_writeoff_records",
    )
    related_mission = models.ForeignKey(
        "missions.Mission",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="writeoff_records",
    )
    document_number = models.CharField(max_length=100, blank=True)
    written_off_at = models.DateField(default=timezone.localdate)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Write-off record for {self.drone}"


class DroneStatusHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    drone = models.ForeignKey(
        Drone, on_delete=models.PROTECT, related_name="status_history"
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="drone_status_changes",
    )
    reason = models.TextField(blank=True)
    related_mission = models.ForeignKey(
        "missions.Mission",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="drone_status_history_records",
    )
    related_repair_order_id = models.PositiveIntegerField(
        null=True, blank=True
    )  # temporary stub
    related_writeoff = models.ForeignKey(
        WriteOffRecord,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="status_history_records",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.drone}: {self.from_status} -> {self.to_status}"
