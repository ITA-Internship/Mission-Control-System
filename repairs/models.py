from django.conf import settings
from django.db import models


# some examples, since I don't know which ones might actually be needed
class DefectType(models.TextChoices):
    MOTOR = "MOTOR", "Motor"
    BATTERY = "BATTERY", "Battery"
    CAMERA = "CAMERA", "Camera"
    FRAME = "FRAME", "Frame"
    PROPELLER = "PROPELLER", "Propeller"
    FLIGHT_CONTROLLER = "FLIGHT_CONTROLLER", "Flight controller"
    VTX = "VTX", "Video transmitter"
    WIRING = "WIRING", "Wiring"
    FIRMWARE = "FIRMWARE", "Firmware"
    OTHER = "OTHER", "Other"


class Severity(models.TextChoices):
    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class RepairStatus(models.TextChoices):
    REPORTED = "REPORTED", "Reported"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    FIXED = "FIXED", "Fixed"
    VERIFIED = "VERIFIED", "Verified"


class DefectReport(models.Model):
    drone = models.ForeignKey(
        "drones.Drone",
        on_delete=models.PROTECT,
        related_name="defects",
    )
    defect_type = models.CharField(
        max_length=30,
        choices=DefectType.choices,
        db_index=True,
    )
    severity = models.CharField(
        max_length=20,
        choices=Severity.choices,
        db_index=True,
    )
    status = models.CharField(
        max_length=20,
        choices=RepairStatus.choices,
        default=RepairStatus.REPORTED,
        db_index=True,
    )
    description = models.TextField()
    detected_at = models.DateTimeField()
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reported_defects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "defect_reports"
        ordering = ("-detected_at",)
        indexes = [
            models.Index(
                fields=["drone", "-detected_at"],
                name="defect_drone_detected_idx",
            ),
            models.Index(
                fields=["severity"],
                name="defect_severity_idx",
            ),
            models.Index(
                fields=["defect_type"],
                name="defect_type_idx",
            ),
        ]

    def __str__(self) -> str:
        return (
            f"{self.get_severity_display()} "
            f"{self.get_defect_type_display()} on {self.drone}"
        )


class RepairEvent(models.Model):
    defect_report = models.ForeignKey(
        DefectReport,
        on_delete=models.CASCADE,
        related_name="repair_events",
    )
    from_status = models.CharField(max_length=20, choices=RepairStatus.choices)
    to_status = models.CharField(max_length=20, choices=RepairStatus.choices)
    action_taken = models.TextField()
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="repair_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "repair_events"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.defect_report} status changed to {self.to_status}"
