import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class DroneModel(models.Model):
    name = models.CharField(max_length=255, unique=True)
    manufacturer = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    supported_classifications = models.JSONField(
        default=list, help_text="List of supported classifications"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Drone Model"
        verbose_name_plural = "Drone Models"
        ordering = ["name"]

    def __str__(self):
        return f"{self.manufacturer} {self.name}"

    def get_allowed_classifications(self):
        return self.supported_classifications or []

    def supports_classification(self, classification):
        return classification in self.get_allowed_classifications()

    def clean(self):
        super().clean()

        if not self.supported_classifications:
            raise ValidationError(
                {
                    "supported_classifications": (
                        "A drone model must support at least one classification."
                    )
                }
            )

        valid_keys = {choice[0] for choice in Drone.CLASSIFICATION_CHOICES}
        invalid_items = [
            item for item in self.supported_classifications if item not in valid_keys
        ]

        if invalid_items:
            raise ValidationError(
                {
                    "supported_classifications": (
                        f"Value {invalid_items} are not valid classifications. "
                        f'Valid classifications: {", ".join(valid_keys)}'
                    )
                }
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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
        (STATUS_ACTIVE, "Active"),
        (STATUS_DAMAGED, "Damaged"),
        (STATUS_LOST, "Lost"),
        (STATUS_MAINTENANCE, "Maintenance"),
        (STATUS_DECOMMISSIONED, "Decommissioned"),
        (STATUS_SOLD, "Sold"),
        (STATUS_TRANSFERRED, "Transferred"),
        (STATUS_WRITTEN_OFF, "Written off"),
    ]

    INACTIVE_STATUSES = (
        STATUS_DECOMMISSIONED,
        STATUS_SOLD,
        STATUS_TRANSFERRED,
        STATUS_WRITTEN_OFF,
    )

    CLASSIFICATION_RECONNAISSANCE = "RECONNAISSANCE"
    CLASSIFICATION_COMBAT = "COMBAT"
    CLASSIFICATION_TRANSPORT = "TRANSPORT"
    CLASSIFICATION_SURVEILLANCE = "SURVEILLANCE"

    CLASSIFICATION_CHOICES = [
        (CLASSIFICATION_RECONNAISSANCE, "Reconnaissance"),
        (CLASSIFICATION_COMBAT, "Combat"),
        (CLASSIFICATION_TRANSPORT, "Transport"),
        (CLASSIFICATION_SURVEILLANCE, "Surveillance"),
    ]

    serial_number = models.CharField(max_length=100, unique=True)
    inventory_number = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    drone_model = models.ForeignKey(
        DroneModel,
        on_delete=models.PROTECT,
        related_name="drones",
        help_text="Drone Model",
    )
    classification = models.CharField(max_length=20, choices=CLASSIFICATION_CHOICES)
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

    def clean(self):
        super().clean()

        if self.drone_model and self.classification:
            allowed_classifications = self.drone_model.get_allowed_classifications()

            if self.classification not in allowed_classifications:
                raise ValidationError(
                    {
                        "classification": f'Classification "{self.classification}" '
                        f'is not supported by drone model "{self.drone_model.name}". '
                        f"Allowed: "
                        f'{", ".join([c.title() for c in allowed_classifications])}'
                    }
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class DroneSpec(models.Model):
    drone = models.OneToOneField(Drone, on_delete=models.CASCADE, related_name="spec")
    frame_type = models.CharField(max_length=255)
    motor_model = models.CharField(max_length=255)
    battery_type = models.CharField(max_length=255)
    battery_capacity_mah = models.PositiveIntegerField()
    battery_model = models.CharField(max_length=255, blank=True)
    camera_model = models.CharField(max_length=255)
    camera_specs = models.JSONField(default=dict, blank=True)
    vtx_model = models.CharField(max_length=255, blank=True)
    flight_controller = models.CharField(max_length=255)
    firmware_version = models.CharField(max_length=255, blank=True)
    is_firmware_outdated = models.BooleanField(
        default=False,
        help_text="Indicates if the firmware or "
        "communication parameters are unsupported.",
    )
    communication_protocol = models.CharField(max_length=100, blank=True)
    control_channel = models.CharField(max_length=255, blank=True)
    telemetry_channel = models.CharField(max_length=255, blank=True)
    max_speed_kmh = models.DecimalField(max_digits=6, decimal_places=2)
    typical_range_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_range_km = models.DecimalField(max_digits=6, decimal_places=2)
    typical_flight_time_min = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_flight_time_min = models.DecimalField(max_digits=6, decimal_places=2)
    frequency_mhz = models.PositiveIntegerField()
    payload_capacity_g = models.PositiveIntegerField(blank=True, null=True)
    additional_modules = models.JSONField(default=list, blank=True)
    technical_documentation_url = models.URLField(blank=True)
    firmware_file_url = models.URLField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        errors = {}

        if not isinstance(self.camera_specs, dict):
            errors["camera_specs"] = "camera_specs must be a JSON object."

        if not isinstance(self.additional_modules, list):
            errors["additional_modules"] = "additional_modules must be a JSON array."
        else:
            invalid_modules = [
                index
                for index, module in enumerate(self.additional_modules)
                if not isinstance(module, dict)
            ]

            if invalid_modules:
                errors["additional_modules"] = (
                    "Each additional module must be a JSON object."
                )

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"Specification for {self.drone}"


class DroneSpecChangeLog(models.Model):
    drone_spec = models.ForeignKey(
        DroneSpec,
        on_delete=models.CASCADE,
        related_name="change_history",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="drone_spec_changes",
    )
    changed_fields = models.JSONField(default=list)
    old_values = models.JSONField(default=dict, blank=True)
    new_values = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["-created_at"],
                name="dronespec_log_created_idx",
            ),
            models.Index(
                fields=["drone_spec", "-created_at"],
                name="dronespec_log_spec_created_idx",
            ),
            models.Index(
                fields=["changed_by", "-created_at"],
                name="dronespec_log_user_created_idx",
            ),
        ]

    def clean(self):
        errors = {}

        if not isinstance(self.changed_fields, list):
            errors["changed_fields"] = "changed_fields must be a list."

        if not isinstance(self.old_values, dict):
            errors["old_values"] = "old_values must be a JSON object."

        if not isinstance(self.new_values, dict):
            errors["new_values"] = "new_values must be a JSON object."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        return f"Spec changes for {self.drone_spec.drone}"


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
