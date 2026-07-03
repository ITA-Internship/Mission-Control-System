from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def get_default_changes():
    return {}


class Status(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    ABORTED = "aborted", "Aborted"


# Allowed mission status transitions (domain state machine). A mission moves
# PLANNED -> ACTIVE -> COMPLETED, and can be ABORTED from either non-terminal
# state. COMPLETED and ABORTED are terminal: no further transitions are legal.
# Enforced in MissionStatusUpdateSerializer.validate_status.
MISSION_STATUS_TRANSITIONS = {
    Status.PLANNED: [Status.ACTIVE, Status.ABORTED],
    Status.ACTIVE: [Status.COMPLETED, Status.ABORTED],
    Status.COMPLETED: [],
    Status.ABORTED: [],
}


class Result(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"


class Condition(models.TextChoices):
    OK = "ok", "Ok"
    DAMAGED = "damaged", "Damaged"
    LOST = "lost", "Lost"


class MissionQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related("commander", "created_by")


class Mission(models.Model):
    title = models.CharField(max_length=255)

    # SET_NULL: deleting the commander must not delete the mission record.
    # A mission is a permanent operational record that outlives any one user.
    commander = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="commanded_missions",
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PLANNED,
    )

    result = models.CharField(
        max_length=20,
        choices=Result.choices,
        null=True,
        blank=True,
    )

    location_description = models.TextField(null=True, blank=True)
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
    )

    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, max_length=5000)
    incident_notes = models.TextField(blank=True, max_length=5000)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_missions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MissionQuerySet.as_manager()

    class Meta:
        db_table = "missions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self):
        return self.title


class MissionDrone(models.Model):
    mission = models.ForeignKey(
        Mission, on_delete=models.CASCADE, related_name="mission_drones"
    )

    # PROTECT: a drone that has ever flown a mission cannot be hard-deleted,
    # so its operational history stays intact. Retiring a drone goes through
    # the write-off flow (status -> WRITTEN_OFF), never a row delete.
    drone = models.ForeignKey(
        "drones.Drone", on_delete=models.PROTECT, related_name="mission_assignments"
    )

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operated_mission_drones",
    )

    condition_after = models.CharField(
        max_length=20,
        choices=Condition.choices,
        null=True,
        blank=True,
    )

    condition_description = models.TextField(null=True, blank=True)
    flight_started_at = models.DateTimeField(null=True, blank=True)
    flight_ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mission_drones"
        constraints = [
            # A given drone may be assigned to a mission at most once; the same
            # drone cannot hold two slots on one mission.
            models.UniqueConstraint(
                fields=["mission", "drone"], name="unique_mission_drone"
            ),
        ]

    def __str__(self):
        return f"{self.mission.title} - {self.drone} (Operator: {self.operator})"


class MissionAuditLog(models.Model):
    """Append-only trail of mission/assignment changes.

    Rows are written by the service layer (and MissionStatusUpdateView) and are
    never updated or deleted — the Django admin blocks add/change/delete. Each
    entry records who did what to which record, plus a JSON ``changes`` diff.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="mission_audit_logs",
    )
    action = models.CharField(max_length=255)
    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField()
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mission_audit_logs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["action", "target_model"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return (
            f"[{self.action}] {self.target_model} (ID: {self.target_id}) by {self.user}"
        )
