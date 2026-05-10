from django.conf import settings
from django.db import models


class Status(models.TextChoices):
    PLANNED = 'planned', 'Planned'
    ACTIVE = 'active', 'Active'
    COMPLETED = 'completed', 'Completed'


class Result(models.TextChoices):
    SUCCESS = 'success', 'Success'
    FAILURE = 'failure', 'Failure'


class Mission(models.Model):
    title = models.CharField(max_length=255)

    commander = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='commanded_missions',
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
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_missions',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'missions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return self.title
