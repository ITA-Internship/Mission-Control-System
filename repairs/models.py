"""Database models for the repairs app.

Defines the DefectReport triage tickets, actionable RepairOrders, hardware
ComponentReplacements, and the append-only RepairEvent audit log.
"""

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class DefectType(models.TextChoices):
    """
    Categorization of physical drone components that can experience defects.

    TODO: Finalize the exact list of defect types.
    """

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
    """Levels of criticality for reported defects to prioritize repair queue."""

    LOW = "LOW", "Low"
    MEDIUM = "MEDIUM", "Medium"
    HIGH = "HIGH", "High"
    CRITICAL = "CRITICAL", "Critical"


class RepairStatus(models.TextChoices):
    """
    Lifecycle states of a DefectReport.

    Tracks the triage and validation process from initial report to final verification.
    """

    REPORTED = "REPORTED", "Reported"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    FIXED = "FIXED", "Fixed"
    VERIFIED = "VERIFIED", "Verified"


class RepairOrderStatus(models.TextChoices):
    """
    Lifecycle states of a RepairOrder.

    Defines the workflow states for a technician's active task. Valid transitions
    are enforced by REPAIR_ORDER_TRANSITIONS.
    """

    PENDING = "PENDING", "Pending"
    IN_PROGRESS = "IN_PROGRESS", "In progress"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


# Allowed repair order status transitions (domain state machine).
# Validated during update operations in the service layer.
REPAIR_ORDER_TRANSITIONS = {
    RepairOrderStatus.PENDING: [
        RepairOrderStatus.IN_PROGRESS,
        RepairOrderStatus.CANCELLED,
    ],
    RepairOrderStatus.IN_PROGRESS: [
        RepairOrderStatus.COMPLETED,
        RepairOrderStatus.CANCELLED,
    ],
    RepairOrderStatus.COMPLETED: [],
    RepairOrderStatus.CANCELLED: [],
}


class ComponentType(models.TextChoices):
    """Hardware categories available for physical replacement on a drone."""

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
    """
    A logged issue or damage report for a drone.

    Acts as the initial triage ticket before a formal RepairOrder is created.
    """

    # PROTECT: a drone with a logged defect cannot be hard-deleted,
    # ensuring the maintenance history remains intact.
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

    # SET_NULL: if the reporting user is deleted (e.g., an employee leaves),
    # the defect record itself must survive.
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
        """Return a human-readable summary of the defect report."""
        return (
            f"{self.get_severity_display()} "
            f"{self.get_defect_type_display()} on {self.drone}"
        )


class RepairOrder(models.Model):
    """
    An actionable maintenance task assigned to a technician.

    Can be linked to a DefectReport or created directly for routine maintenance.
    """

    # PROTECT: maintaining the drone's lifetime repair history is critical.
    drone = models.ForeignKey(
        "drones.Drone",
        on_delete=models.PROTECT,
        related_name="repair_orders",
    )

    # SET_NULL: if a defect report is removed, the repair order (and its accounting
    # of technician labor) must remain intact.
    defect_report = models.ForeignKey(
        DefectReport,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="repair_orders",
    )
    status = models.CharField(
        max_length=20,
        choices=RepairOrderStatus.choices,
        default=RepairOrderStatus.PENDING,
        db_index=True,
    )
    description = models.TextField()

    # SET_NULL: keep the order intact even if the assigned technician is deleted.
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_repairs",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    # SET_NULL: keep the order intact even if the creator is deleted.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_repairs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "repair_orders"
        ordering = ("-created_at",)
        indexes = [
            models.Index(
                fields=["drone", "-created_at"],
                name="repair_drone_created_idx",
            ),
            models.Index(
                fields=["status"],
                name="repair_status_idx",
            ),
        ]

    def __str__(self) -> str:
        """Return a string identifying the repair order and its current status."""
        return f"Repair #{self.pk} [{self.get_status_display()}] on {self.drone}"


class RepairEvent(models.Model):
    """
    Audit log for state changes on a DefectReport.

    Used to track the lifecycle and resolution timeline of an issue.
    """

    # PROTECT: audit logs must never lose their parent report.
    defect_report = models.ForeignKey(
        DefectReport,
        on_delete=models.PROTECT,
        related_name="repair_events",
    )
    from_status = models.CharField(max_length=20, choices=RepairStatus.choices)
    to_status = models.CharField(max_length=20, choices=RepairStatus.choices)
    action_taken = models.TextField()

    # SET_NULL: the audit log row must remain even if the technician account is deleted.
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
        """Return a string summarizing the status transition of the report."""
        return f"{self.defect_report} status changed to {self.to_status}"


class ComponentReplacement(models.Model):
    """
    Tracks physical hardware changes on a drone.

    Critical for maintaining accurate inventory and drone configuration history.
    """

    # PROTECT: physical hardware changes must be permanently tied to the drone.
    drone = models.ForeignKey(
        "drones.Drone",
        on_delete=models.PROTECT,
        related_name="component_replacements",
    )

    # SET_NULL: a replacement record should survive even if its parent order is removed.
    repair_order = models.ForeignKey(
        RepairOrder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="component_replacements",
    )
    component_type = models.CharField(
        max_length=30,
        choices=ComponentType.choices,
        db_index=True,
    )
    component_name = models.CharField(max_length=255, blank=True, null=True)
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
        """
        Validate replacement data.

        Ensures the replacement date is not in the future and that a specific
        name is provided when the generic 'OTHER' category is used.
        """
        errors = {}

        if self.replaced_at is not None and self.replaced_at > timezone.now():
            errors["replaced_at"] = "replaced_at cannot be in the future."

        if (
            self.component_type == ComponentType.OTHER
            and not (self.component_name or "").strip()
        ):
            errors["component_name"] = "Component name is required for OTHER."

        if errors:
            raise ValidationError(errors)

    def __str__(self) -> str:
        """Return a string identifying the replaced component and the drone."""
        component = (
            self.component_name
            if self.component_type == ComponentType.OTHER and self.component_name
            else self.get_component_type_display()
        )
        return f"{component} replacement on {self.drone}"
