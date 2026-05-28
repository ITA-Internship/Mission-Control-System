import datetime

import factory

from drones.factories import (
    AdminRoleFactory,
    AdminUserFactory,
    DroneFactory,
    ViewerRoleFactory,
    ViewerUserFactory,
)
from roles.models import COMMANDER_CODE, OPERATOR_CODE

__all__ = [
    "AdminRoleFactory",
    "AdminUserFactory",
    "CommanderRoleFactory",
    "CommanderUserFactory",
    "DroneFactory",
    "MissionFactory",
    "MissionDroneFactory",
    "OperatorRoleFactory",
    "OperatorUserFactory",
    "ViewerRoleFactory",
    "ViewerUserFactory",
]


class OperatorRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "roles.Role"
        django_get_or_create = ("code",)

    code = OPERATOR_CODE
    name = "Operator"


class OperatorUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"operator_user_{n}")
    email = factory.Sequence(lambda n: f"operator_user_{n}@example.com")
    password = factory.Sequence(lambda n: f"password_{n}")
    role = factory.SubFactory(OperatorRoleFactory)


class CommanderRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "roles.Role"
        django_get_or_create = ("code",)

    code = COMMANDER_CODE
    name = "Commander"


class CommanderUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"commander_user_{n}")
    email = factory.Sequence(lambda n: f"commander_user_{n}@example.com")
    password = factory.Sequence(lambda n: f"password_{n}")
    role = factory.SubFactory(CommanderRoleFactory)


class MissionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "missions.Mission"

    title = factory.Sequence(lambda n: f"Mission {n}")
    status = "planned"
    location_description = "Test location"
    started_at = datetime.datetime(2026, 5, 27, 10, 0, tzinfo=datetime.timezone.utc)
    ended_at = datetime.datetime(2026, 5, 27, 12, 0, tzinfo=datetime.timezone.utc)
    commander = factory.SubFactory(CommanderUserFactory)
    created_by = factory.SubFactory(AdminUserFactory)


class MissionDroneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "missions.MissionDrone"

    mission = factory.SubFactory(MissionFactory)
    drone = factory.SubFactory(DroneFactory)
    operator = factory.SubFactory(OperatorUserFactory)
