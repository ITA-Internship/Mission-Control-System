"""App configuration for the missions app."""

from django.apps import AppConfig


class MissionsConfig(AppConfig):
    """Default configuration for the missions app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "missions"
