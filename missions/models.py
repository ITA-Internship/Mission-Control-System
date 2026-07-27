"""Database models for the missions app.

Defines the Mission aggregate, its drone assignments (``MissionDrone``), the
append-only ``MissionAuditLog`` trail, and the status/result/condition enums
together with the allowed mission status-transition map.
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Prefetch


def get_default_changes():
    """Return a fresh empty dict for the ``MissionAuditLog.changes`` default.

    Used as a callable default so each row gets its own dict rather than
    sharing one mutable instance across rows.
    """
    return {}


class Status(models.TextChoices):
    """Mission lifecycle states.

    Defines the four possible states in the mission workflow:
    - PLANNED: initial state; the mission is scheduled but not yet executing.
    - ACTIVE: the mission is currently in progress.
    - COMPLETED: the mission finished successfully (terminal state).
    - ABORTED: the mission was terminated early (terminal state).

    Valid transitions are enforced by MISSION_STATUS_TRANSITIONS and validated
    in MissionStatusUpdateSerializer.validate_status.
    """

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
    """Terminal outcome of a finished mission.

    - SUCCESS: the mission met its objective.
    - FAILURE: the mission did not meet its objective.

    Stored on ``Mission.result``, which stays null until an outcome is recorded.
    """

    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"


class Condition(models.TextChoices):
    """Condition of a drone recorded after a mission.

    - OK: returned undamaged.
    - DAMAGED: returned damaged but recoverable.
    - LOST: lost in the field; recording this triggers a drone write-off.

    Mapped to the resulting drone status by
    ``missions.services.CONDITION_TO_DRONE_STATUS``.
    """

    OK = "ok", "Ok"
    DAMAGED = "damaged", "Damaged"
    LOST = "lost", "Lost"


class MissionQuerySet(models.QuerySet):
    """Queryset for :class:`Mission`, installed as its default manager."""

    def with_related(self):
        """Return the queryset with ``commander`` and ``created_by`` joined.

        Uses ``select_related`` to avoid a per-row query for the related users
        when listing or serialising missions.
        """

        return self.select_related("commander", "created_by", "unit").prefetch_related(
            Prefetch(
                "mission_drones",
                queryset=MissionDrone.objects.select_related("drone", "operator"),
            )
        )


class Mission(models.Model):
    """A planned or executed operation and its permanent operational record.

    Owns a set of :class:`MissionDrone` assignments and moves through the
    :class:`Status` state machine. The record is durable: ``commander`` and
    ``created_by`` are set null rather than cascaded when those users are
    deleted, so mission history survives the accounts involved.
    """

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

    unit = models.ForeignKey(
        "accounts.MilitaryUnit",
        on_delete=models.PROTECT,
        related_name="missions",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = MissionQuerySet.as_manager()

    class Meta:
        db_table = "missions"
        ordering = ["-created_at"]

        indexes = [
            models.Index(fields=["started_at"]),
            models.Index(
                fields=["status", "started_at", "ended_at"],
                name="mission_time_range_idx",
            ),
        ]

    def __str__(self):
        """Return the mission title."""
        return self.title


class MissionDrone(models.Model):
    """A drone, and its operator, assigned to a specific mission.

    Join model between :class:`Mission` and ``drones.Drone`` that also carries
    per-flight data. The drone is protected from deletion while assignments
    exist, and a unique constraint on ``(mission, drone)`` stops a drone taking
    two slots on the same mission.
    """

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
        indexes = [
            models.Index(
                fields=["drone", "mission"],
                name="md_drone_mission_idx",
            ),
            models.Index(
                fields=["operator", "mission"],
                name="md_operator_mission_idx",
            ),
        ]

    def __str__(self):
        """Return a summary of the assignment (mission, drone, operator)."""
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
        """Return a one-line description of the logged action."""
        return (
            f"[{self.action}] {self.target_model} (ID: {self.target_id}) by {self.user}"
        )
