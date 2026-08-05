from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = "common"

    def ready(self):
        # Importing the module registers drf-spectacular extensions.
        from . import schema  # noqa: F401