"""Django application configuration for the repairs app.

Registers the app with the Django project and defines default settings
such as the primary key field type.
"""

from django.apps import AppConfig


class RepairsConfig(AppConfig):
    """Configuration settings for the repairs application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "repairs"
