import datetime

import factory

# Re-export shared factories for convenience in repairs tests.
from drones.factories import (  # noqa: F401
    AdminUserFactory,
    DroneFactory,
    MilitaryUnitFactory,
    ViewerUserFactory,
)

from .models import DefectType, Severity


class DefectReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "repairs.DefectReport"

    drone = factory.SubFactory(DroneFactory)
    defect_type = DefectType.MOTOR
    severity = Severity.HIGH
    description = "Rear-left motor stutters under load and overheats."
    detected_at = datetime.datetime(2026, 6, 3, 14, 30, tzinfo=datetime.timezone.utc)
    reporter = factory.SubFactory(AdminUserFactory)
