from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from drones.models import Drone


class Status(models.TextChoices):
    PLANNED = "planned", "Planned"
    ACTIVE = "active", "Active"
    COMPLETED = "completed", "Completed"
    ABORTED = "aborted", "Aborted"


MISSION_STATUS_TRANSITIONS = {
    Status.PLANNED: [Status.ACTIVE, Status.ABORTED],
    Status.ACTIVE: [Status.COMPLETED, Status.ABORTED],
    Status.COMPLETED: [],
    Status.ABORTED: [],
}


class Result(models.TextChoices):
    SUCCESS = "success", "Success"
    FAILURE = "failure", "Failure"


class MissionQuerySet(models.QuerySet):
    def with_related(self):
        return self.select_related("commander", "created_by")


class Mission(models.Model):
    title = models.CharField(max_length=255)

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

    notes = models.TextField(blank=True)

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

    drone = models.ForeignKey(
        "drones.Drone", on_delete=models.CASCADE, related_name="mission_participations"
    )

    operator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="operated_mission_drones",
    )

    condition_after = models.CharField(
        max_length=20, choices=Drone.STATUS_CHOICES, default="ACTIVE"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "mission_drones"
        unique_together = ("mission", "drone")

    def __str__(self):
        return f"{self.drone} in {self.mission}"


class MissionAuditLog(models.Model):
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
    )
    action = models.CharField(max_length=255)
    target_model = models.CharField(max_length=100)
    target_id = models.IntegerField()
    changes = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} on {self.target_model} (ID: {self.target_id})"
