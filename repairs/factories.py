import datetime

import factory

# Re-export shared factories for convenience in repairs tests.
from drones.factories import (  # noqa: F401
    AdminUserFactory,
    DroneFactory,
    MilitaryUnitFactory,
    ViewerUserFactory,
)

from .models import ComponentType, DefectType, Severity


class DefectReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "repairs.DefectReport"

    drone = factory.SubFactory(DroneFactory)
    defect_type = DefectType.MOTOR
    severity = Severity.HIGH
    description = "Rear-left motor stutters under load and overheats."
    detected_at = datetime.datetime(2026, 6, 3, 14, 30, tzinfo=datetime.timezone.utc)
    reporter = factory.SubFactory(AdminUserFactory)


class ComponentReplacementFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "repairs.ComponentReplacement"

    drone = factory.SubFactory(DroneFactory)
    component_type = ComponentType.MOTOR
    component_name = ""
    old_serial_number = "MOTOR-OLD-001"
    new_serial_number = "MOTOR-NEW-001"
    reason = "Motor replaced after vibration and overheating."
    replaced_at = datetime.datetime(
        2026,
        6,
        10,
        11,
        0,
        tzinfo=datetime.timezone.utc,
    )
    replaced_by = factory.SubFactory(AdminUserFactory)
