"""Define factory classes for drone app tests."""

import datetime

import factory

from roles.models import ADMIN_CODE, VIEWER_CODE


class AdminRoleFactory(factory.django.DjangoModelFactory):
    """Build an admin role with drone-management permissions for tests."""
    class Meta:
        """Configure the Role model target for the admin role factory."""
        model = "roles.Role"
        django_get_or_create = ("code",)

    code = ADMIN_CODE
    name = "Admin"


class AdminUserFactory(factory.django.DjangoModelFactory):
    """Build an admin user for drone tests."""
    class Meta:
        """Configure the User model target for the admin user factory."""
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"admin_user_{n}@example.com")
    password = factory.Sequence(lambda n: f"password_{n}")
    role = factory.SubFactory(AdminRoleFactory)


class ViewerRoleFactory(factory.django.DjangoModelFactory):
    """Build a viewer role with read-only drone permissions for tests."""
    class Meta:
        """Configure the Role model target for the viewer role factory."""
        model = "roles.Role"
        django_get_or_create = ("code",)

    code = VIEWER_CODE
    name = "Viewer"


class ViewerUserFactory(factory.django.DjangoModelFactory):
    """Build a viewer user for permission tests."""
    class Meta:
        """Configure the User model target for the viewer user factory."""
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"viewer_user_{n}")
    email = factory.Sequence(lambda n: f"viewer_user_{n}@example.com")
    password = factory.Sequence(lambda n: f"password_{n}")
    role = factory.SubFactory(ViewerRoleFactory)


class MilitaryUnitFactory(factory.django.DjangoModelFactory):
    """Build a military unit for drone assignment tests."""
    class Meta:
        """Configure the MilitaryUnit model target for the factory."""
        model = "accounts.MilitaryUnit"

    name = factory.Sequence(lambda n: f"military_unit_{n}")
    code = factory.Sequence(lambda n: f"UNIT_{n}")


class DroneModelFactory(factory.django.DjangoModelFactory):
    """Build a drone model with supported classifications for tests."""
    class Meta:
        """Configure the DroneModel target for the factory."""
        model = "drones.DroneModel"

    name = factory.Sequence(lambda n: f"Model Name {n}")
    manufacturer = factory.Sequence(lambda n: f"Manufacturer {n}")
    supported_classifications = factory.List(["RECONNAISSANCE", "SURVEILLANCE"])


class DroneFactory(factory.django.DjangoModelFactory):
    """Build a drone tied to a model and military unit for tests."""
    class Meta:
        """Configure the Drone model target for the factory."""
        model = "drones.Drone"

    serial_number = factory.Sequence(lambda n: f"SERIAL_{n}")
    inventory_number = factory.Sequence(lambda n: f"INV_{n}")
    name = factory.Sequence(lambda n: f"Drone {n}")
    drone_model = factory.SubFactory(DroneModelFactory)

    @factory.lazy_attribute
    def classification(self):
        """Use the first classification supported by the generated model."""
        return self.drone_model.supported_classifications[0]

    status = "ACTIVE"
    military_unit = factory.SubFactory(MilitaryUnitFactory)
    acquired_at = datetime.date(2026, 5, 9)
    notes = ""


class DroneSpecFactory(factory.django.DjangoModelFactory):
    """Build a technical specification for a drone test object."""
    class Meta:
        """Configure the DroneSpec model target for the factory."""
        model = "drones.DroneSpec"

    drone = factory.SubFactory(DroneFactory)
    frame_type = "Test Frame"
    motor_model = "Test Motor"
    battery_type = "LiPo"
    battery_capacity_mah = 1500
    battery_model = "Test Battery Model"
    camera_model = "Test Camera"
    camera_specs = {
        "sensor": '1/2.8"',
        "resolution": "1080p",
        "fov": "120",
        "stabilization": "none",
        "night_mode": True,
    }
    vtx_model = "Test VTX"
    flight_controller = "Test Controller"
    firmware_version = "1.0.0"
    is_firmware_outdated = False
    communication_protocol = "ExpressLRS"
    control_channel = "CH1"
    telemetry_channel = "CH2"
    max_speed_kmh = "120.00"
    typical_range_km = "8.50"
    max_range_km = "10.00"
    typical_flight_time_min = "18.00"
    max_flight_time_min = "20.00"
    frequency_mhz = 5800
    payload_capacity_g = 100
    additional_modules = [
        {
            "type": "GPS",
            "model": "Matek M10Q",
            "notes": "External module",
        }
    ]
    technical_documentation_url = "https://example.com/drone-spec.pdf"
    firmware_file_url = "https://example.com/firmware.bin"
