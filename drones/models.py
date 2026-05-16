from django.db import models


class Drone(models.Model):

    STATUS_CHOICES = [
        ("ACTIVE", "Active"),
        ("DAMAGED", "Damaged"),
        ("LOST", "Lost"),
        ("MAINTENANCE", "Maintenance"),
        ("IN_MISSION", "In Mission"),
    ]

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
