import datetime

import factory

from roles.models import ADMIN_CODE, VIEWER_CODE


class AdminRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "roles.Role"
        django_get_or_create = ("code",)

    code = ADMIN_CODE
    name = "Admin"


class AdminUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"admin_user_{n}@example.com")
    password = factory.Sequence(lambda n: f"password_{n}")
    role = factory.SubFactory(AdminRoleFactory)


class ViewerRoleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "roles.Role"
        django_get_or_create = ("code",)

    code = VIEWER_CODE
    name = "Viewer"


class ViewerUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.User"

    username = factory.Sequence(lambda n: f"viewer_user_{n}")
    email = factory.Sequence(lambda n: f"viewer_user_{n}@example.com")
    password = factory.Sequence(lambda n: f"password_{n}")
    role = factory.SubFactory(ViewerRoleFactory)


class MilitaryUnitFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "accounts.MilitaryUnit"

    name = factory.Sequence(lambda n: f"military_unit_{n}")
    code = factory.Sequence(lambda n: f"UNIT_{n}")


class DroneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "drones.Drone"

    serial_number = factory.Sequence(lambda n: f"SERIAL_{n}")
    inventory_number = factory.Sequence(lambda n: f"INV_{n}")
    name = factory.Sequence(lambda n: f"Drone {n}")
    drone_model = "FPV Test Model"
    status = "ACTIVE"
    military_unit = factory.SubFactory(MilitaryUnitFactory)
    acquired_at = datetime.date(2026, 5, 9)
    notes = ""


class DroneSpecFactory(factory.django.DjangoModelFactory):
    class Meta:
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
    max_speed_kmh = "120.00"
    max_range_km = "10.00"
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
