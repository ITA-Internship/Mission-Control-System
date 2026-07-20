"""Application configuration for user accounts management.

This module sets up the Django app config and ensures that system signals
are registered when the application starts.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Configuration class for the accounts' application."""

    name = "accounts"

    def ready(self):
        """Perform initialization tasks when Django stars.

        Import signal receivers to register them.
        """
        import accounts.signals  # noqa: F401
