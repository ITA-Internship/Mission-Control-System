from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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


class ComponentType(models.TextChoices):
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


class ComponentReplacement(models.Model):
    drone = models.ForeignKey(
        "drones.Drone",
        on_delete=models.PROTECT,
        related_name="component_replacements",
    )
    component_type = models.CharField(
        max_length=30,
        choices=ComponentType.choices,
        db_index=True,
    )
    component_name = models.CharField(max_length=255, blank=True)
    old_serial_number = models.CharField(max_length=100, blank=True)
    new_serial_number = models.CharField(max_length=100)
    reason = models.TextField()
    replaced_at = models.DateTimeField()
    replaced_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="component_replacements_performed",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "component_replacements"
        ordering = ("-replaced_at", "-id")
        indexes = [
            models.Index(
                fields=["drone", "-replaced_at"],
                name="repl_drone_replaced_idx",
            ),
            models.Index(
                fields=["component_type", "-replaced_at"],
                name="repl_component_replaced_idx",
            ),
            models.Index(
                fields=["replaced_by", "-replaced_at"],
                name="repl_user_replaced_idx",
            ),
        ]

    def clean(self):
        errors = {}

        if self.replaced_at and self.replaced_at > timezone.now():
            errors["replaced_at"] = "replaced_at cannot be in the future."

        if (
            self.component_type == ComponentType.OTHER
            and not self.component_name.strip()
        ):
            errors["component_name"] = "Component name is required for OTHER."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        component = (
            self.component_name
            if self.component_type == ComponentType.OTHER and self.component_name
            else self.get_component_type_display()
        )
        return f"{component} replacement on {self.drone}"
