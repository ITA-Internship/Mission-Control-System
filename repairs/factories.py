"""Factory Boy definitions for generating repairs app test data.

Provides default mock data for defects, repair orders, and component
replacements to streamline unit testing.
"""

import datetime

import factory

from drones.factories import AdminUserFactory, DroneFactory

from .models import ComponentType, DefectType, RepairOrderStatus, Severity


class DefectReportFactory(factory.django.DjangoModelFactory):
    """Factory for generating DefectReport instances for testing."""

    class Meta:
        model = "repairs.DefectReport"

    drone = factory.SubFactory(DroneFactory)
    defect_type = DefectType.MOTOR
    severity = Severity.HIGH
    description = "Rear-left motor stutters under load and overheats."
    detected_at = datetime.datetime(2026, 6, 3, 14, 30, tzinfo=datetime.timezone.utc)
    reporter = factory.SubFactory(AdminUserFactory)


class RepairOrderFactory(factory.django.DjangoModelFactory):
    """Factory for generating RepairOrder instances for testing."""

    class Meta:
        model = "repairs.RepairOrder"

    drone = factory.SubFactory(DroneFactory)
    description = "Replaced damaged motor after mission impact."
    status = RepairOrderStatus.PENDING
    created_by = factory.SubFactory(AdminUserFactory)


class ComponentReplacementFactory(factory.django.DjangoModelFactory):
    """Factory for generating ComponentReplacement instances for testing."""

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
