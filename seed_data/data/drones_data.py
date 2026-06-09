from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from drones.models import Drone


@dataclass(frozen=True)
class DroneSpecSeed:
    frame_type: str
    motor_model: str
    battery_type: str
    battery_capacity_mah: int
    camera_model: str
    vtx_model: str
    flight_controller: str
    firmware_version: str
    max_speed_kmh: Decimal
    max_range_km: Decimal
    max_flight_time_min: Decimal
    frequency_mhz: int
    payload_capacity_g: int | None


@dataclass(frozen=True)
class DroneSeed:
    serial_number: str
    inventory_number: str
    name: str
    drone_model_name: str
    status: str
    unit_code: str
    acquired_at: date
    notes: str
    spec: DroneSpecSeed


@dataclass(frozen=True)
class StatusHistorySeed:
    drone_serial: str
    from_status: str
    to_status: str
    changed_by_username: str | None
    reason: str
    related_mission_title: str | None


@dataclass(frozen=True)
class WriteOffSeed:
    drone_serial: str
    reason: str
    reason_description: str
    authorized_by_username: str | None
    related_mission_title: str | None
    document_number: str
    written_off_at: date


@dataclass(frozen=True)
class DroneModelSeed:
    name: str
    manufacturer: str
    description: str | None
    supported_classifications: list[str]
    is_active: bool = True


DRONE_MODELS = (
    DroneModelSeed(
        name="Shark Recon 7",
        manufacturer="Ukrspecsystems",
        description="Long-range reconnaissance and artillery adjustment UAV.",
        supported_classifications=[
            Drone.CLASSIFICATION_RECONNAISSANCE,
            Drone.CLASSIFICATION_SURVEILLANCE,
        ],
    ),
    DroneModelSeed(
        name="Viper Strike 5",
        manufacturer="SkyDio",
        description="High-speed strike drone for precision attacks.",
        supported_classifications=[Drone.CLASSIFICATION_COMBAT],
        is_active=False,
    ),
    DroneModelSeed(
        name="Banshee Cargo 6",
        manufacturer="Malloy Aeronautics",
        description="Heavy-lift cargo drone for logistics and payload delivery.",
        supported_classifications=[
            Drone.CLASSIFICATION_TRANSPORT,
            Drone.CLASSIFICATION_COMBAT,
        ],
    ),
    DroneModelSeed(
        name="Atlas Relay 8",
        manufacturer="Quantum Systems",
        description="Long-endurance signal relay and perimeter monitoring platform.",
        supported_classifications=[
            Drone.CLASSIFICATION_TRANSPORT,
            Drone.CLASSIFICATION_SURVEILLANCE,
        ],
    ),
    DroneModelSeed(
        name="Kestrel Mini 4",
        manufacturer="Teal Drones",
        description="Compact, silent tactical drone for rapid reconnaissance.",
        supported_classifications=[Drone.CLASSIFICATION_RECONNAISSANCE],
    ),
    DroneModelSeed(
        name="Guardian Hex 6",
        manufacturer="DJI",
        description="Enterprise hexacopter for surveillance and thermal inspection.",
        supported_classifications=[Drone.CLASSIFICATION_SURVEILLANCE],
    ),
    DroneModelSeed(
        name="Raven Attack 5",
        manufacturer="Anduril",
        description="AI-powered loitering munition for target engagement.",
        supported_classifications=[Drone.CLASSIFICATION_COMBAT],
        is_active=False,
    ),
)

DRONES = (
    DroneSeed(
        serial_number="FPV-AER-24001",
        inventory_number="INV-AER-001",
        name="Falcon Eye 1",
        drone_model_name="Shark Recon 7",
        status=Drone.STATUS_ACTIVE,
        unit_code="AER-01",
        acquired_at=date(2025, 1, 12),
        notes="Recon platform configured for stable daytime observation sorties.",
        spec=DroneSpecSeed(
            frame_type="7-inch carbon frame",
            motor_model="XING2 2806.5 1300KV",
            battery_type="Li-Ion 6S",
            battery_capacity_mah=4000,
            camera_model="RunCam Phoenix 2",
            vtx_model="Rush Tank Solo",
            flight_controller="Matek H743",
            firmware_version="INAV 7.1",
            max_speed_kmh=Decimal("118.50"),
            max_range_km=Decimal("18.20"),
            max_flight_time_min=Decimal("24.00"),
            frequency_mhz=5800,
            payload_capacity_g=250,
        ),
    ),
    DroneSeed(
        serial_number="FPV-AER-24002",
        inventory_number="INV-AER-002",
        name="Falcon Eye 2",
        drone_model_name="Shark Recon 7",
        status=Drone.STATUS_ACTIVE,
        unit_code="AER-01",
        acquired_at=date(2025, 2, 18),
        notes="Long-range reserve recon drone kept mission-ready.",
        spec=DroneSpecSeed(
            frame_type="7-inch carbon frame",
            motor_model="BrotherHobby Avenger 2507 1500KV",
            battery_type="Li-Ion 6S",
            battery_capacity_mah=4200,
            camera_model="Caddx Ratel 2",
            vtx_model="Walksnail Avatar VTX",
            flight_controller="SpeedyBee F7 V3",
            firmware_version="Betaflight 4.5.0",
            max_speed_kmh=Decimal("125.00"),
            max_range_km=Decimal("16.40"),
            max_flight_time_min=Decimal("22.50"),
            frequency_mhz=5800,
            payload_capacity_g=220,
        ),
    ),
    DroneSeed(
        serial_number="FPV-ATK-24003",
        inventory_number="INV-ATK-003",
        name="Hammer 1",
        drone_model_name="Viper Strike 5",
        status=Drone.STATUS_ACTIVE,
        unit_code="ATK-02",
        acquired_at=date(2025, 3, 7),
        notes="Primary assault quad used for rapid strike tasking.",
        spec=DroneSpecSeed(
            frame_type="5-inch reinforced frame",
            motor_model="T-Motor F60 Pro V",
            battery_type="LiPo 6S",
            battery_capacity_mah=1800,
            camera_model="DJI O3 Camera",
            vtx_model="DJI O3 Air Unit",
            flight_controller="Holybro Kakute F7",
            firmware_version="Betaflight 4.4.3",
            max_speed_kmh=Decimal("152.00"),
            max_range_km=Decimal("9.80"),
            max_flight_time_min=Decimal("14.00"),
            frequency_mhz=5800,
            payload_capacity_g=650,
        ),
    ),
    DroneSeed(
        serial_number="FPV-ATK-24004",
        inventory_number="INV-ATK-004",
        name="Hammer 2",
        drone_model_name="Viper Strike 5",
        status=Drone.STATUS_MAINTENANCE,
        unit_code="ATK-02",
        acquired_at=date(2025, 3, 25),
        notes="Awaiting motor replacement after vibration issues detected post-sortie.",
        spec=DroneSpecSeed(
            frame_type="5-inch reinforced frame",
            motor_model="T-Motor F60 Pro V",
            battery_type="LiPo 6S",
            battery_capacity_mah=1800,
            camera_model="DJI O3 Camera",
            vtx_model="DJI O3 Air Unit",
            flight_controller="Holybro Kakute F7",
            firmware_version="Betaflight 4.4.3",
            max_speed_kmh=Decimal("149.50"),
            max_range_km=Decimal("9.10"),
            max_flight_time_min=Decimal("13.50"),
            frequency_mhz=5800,
            payload_capacity_g=600,
        ),
    ),
    DroneSeed(
        serial_number="FPV-ATK-24005",
        inventory_number="INV-ATK-005",
        name="Spear 1",
        drone_model_name="Banshee Cargo 6",
        status=Drone.STATUS_DAMAGED,
        unit_code="ATK-02",
        acquired_at=date(2025, 4, 3),
        notes="Recovered after hard landing with arm damage and camera misalignment.",
        spec=DroneSpecSeed(
            frame_type="6-inch hybrid frame",
            motor_model="iFlight XING 2207 1800KV",
            battery_type="LiPo 6S",
            battery_capacity_mah=2200,
            camera_model="RunCam Link Wasp",
            vtx_model="Caddx Vista",
            flight_controller="Skystars F722 HD",
            firmware_version="Betaflight 4.5.0",
            max_speed_kmh=Decimal("138.00"),
            max_range_km=Decimal("11.20"),
            max_flight_time_min=Decimal("16.50"),
            frequency_mhz=5800,
            payload_capacity_g=540,
        ),
    ),
    DroneSeed(
        serial_number="FPV-SUP-24006",
        inventory_number="INV-SUP-006",
        name="Relay 1",
        drone_model_name="Atlas Relay 8",
        status=Drone.STATUS_TRANSFERRED,
        unit_code="SUP-03",
        acquired_at=date(2024, 11, 29),
        notes=(
            "Transferred to adjacent brigade after communications "
            "relay reorganization."
        ),
        spec=DroneSpecSeed(
            frame_type="8-inch endurance frame",
            motor_model="BrotherHobby 3110 900KV",
            battery_type="Li-Ion 6S",
            battery_capacity_mah=5200,
            camera_model="Foxeer Toothless 2",
            vtx_model="Rush Max Solo",
            flight_controller="Matek F765",
            firmware_version="ArduPilot 4.5.1",
            max_speed_kmh=Decimal("102.00"),
            max_range_km=Decimal("24.00"),
            max_flight_time_min=Decimal("31.00"),
            frequency_mhz=1200,
            payload_capacity_g=300,
        ),
    ),
    DroneSeed(
        serial_number="FPV-AER-24007",
        inventory_number="INV-AER-007",
        name="Scout 1",
        drone_model_name="Kestrel Mini 4",
        status=Drone.STATUS_ACTIVE,
        unit_code="AER-01",
        acquired_at=date(2025, 4, 21),
        notes="Compact urban recon platform for short-range rapid launches.",
        spec=DroneSpecSeed(
            frame_type="4-inch compact frame",
            motor_model="T-Motor P1604 3800KV",
            battery_type="LiPo 4S",
            battery_capacity_mah=1500,
            camera_model="Caddx Ant Nano",
            vtx_model="TBS Unify Pro32 Nano",
            flight_controller="SpeedyBee F405 Mini",
            firmware_version="Betaflight 4.4.2",
            max_speed_kmh=Decimal("94.00"),
            max_range_km=Decimal("6.20"),
            max_flight_time_min=Decimal("11.50"),
            frequency_mhz=5800,
            payload_capacity_g=80,
        ),
    ),
    DroneSeed(
        serial_number="FPV-SUP-24008",
        inventory_number="INV-SUP-008",
        name="Sentinel 1",
        drone_model_name="Guardian Hex 6",
        status=Drone.STATUS_DECOMMISSIONED,
        unit_code="SUP-03",
        acquired_at=date(2024, 8, 15),
        notes=(
            "Decommissioned after frame fatigue exceeded safe "
            "maintenance thresholds."
        ),
        spec=DroneSpecSeed(
            frame_type="6-inch hexacopter frame",
            motor_model="Emax Eco II 2306 1700KV",
            battery_type="LiPo 6S",
            battery_capacity_mah=2600,
            camera_model="RunCam Phoenix 2",
            vtx_model="AKK FX3",
            flight_controller="Kakute H7",
            firmware_version="Betaflight 4.3.2",
            max_speed_kmh=Decimal("121.00"),
            max_range_km=Decimal("8.50"),
            max_flight_time_min=Decimal("15.00"),
            frequency_mhz=5800,
            payload_capacity_g=420,
        ),
    ),
    DroneSeed(
        serial_number="FPV-ATK-24009",
        inventory_number="INV-ATK-009",
        name="Lancer 1",
        drone_model_name="Raven Attack 5",
        status=Drone.STATUS_WRITTEN_OFF,
        unit_code="ATK-02",
        acquired_at=date(2024, 12, 10),
        notes="Written off following mission loss in contested zone.",
        spec=DroneSpecSeed(
            frame_type="5-inch carbon frame",
            motor_model="RCinPower GTS V3 2207 1860KV",
            battery_type="LiPo 6S",
            battery_capacity_mah=1600,
            camera_model="DJI O3 Camera",
            vtx_model="DJI O3 Air Unit",
            flight_controller="Mamba F722 MK4",
            firmware_version="Betaflight 4.4.1",
            max_speed_kmh=Decimal("155.00"),
            max_range_km=Decimal("10.40"),
            max_flight_time_min=Decimal("12.80"),
            frequency_mhz=5800,
            payload_capacity_g=700,
        ),
    ),
    DroneSeed(
        serial_number="FPV-SUP-24010",
        inventory_number="INV-SUP-010",
        name="Courier 1",
        drone_model_name="Atlas Relay 8",
        status=Drone.STATUS_LOST,
        unit_code="SUP-03",
        acquired_at=date(2024, 7, 30),
        notes=(
            "Lost during relocation after telemetry dropped and "
            "recovery team could not secure the airframe."
        ),
        spec=DroneSpecSeed(
            frame_type="8-inch endurance frame",
            motor_model="BrotherHobby 3110 900KV",
            battery_type="Li-Ion 6S",
            battery_capacity_mah=5000,
            camera_model="Foxeer Toothless 2",
            vtx_model="Rush Max Solo",
            flight_controller="Matek F765",
            firmware_version="ArduPilot 4.4.0",
            max_speed_kmh=Decimal("99.50"),
            max_range_km=Decimal("22.70"),
            max_flight_time_min=Decimal("29.50"),
            frequency_mhz=1200,
            payload_capacity_g=280,
        ),
    ),
)


STATUS_HISTORY = (
    StatusHistorySeed(
        drone_serial="FPV-ATK-24004",
        from_status=Drone.STATUS_ACTIVE,
        to_status=Drone.STATUS_MAINTENANCE,
        changed_by_username="tech.airframe",
        reason="Scheduled maintenance after abnormal motor vibration.",
        related_mission_title="Southern Tree Line Sweep",
    ),
    StatusHistorySeed(
        drone_serial="FPV-ATK-24005",
        from_status=Drone.STATUS_ACTIVE,
        to_status=Drone.STATUS_DAMAGED,
        changed_by_username="tech.electro",
        reason="Recovered with structural damage after emergency landing.",
        related_mission_title="Rail Crossing Interdiction",
    ),
    StatusHistorySeed(
        drone_serial="FPV-SUP-24006",
        from_status=Drone.STATUS_ACTIVE,
        to_status=Drone.STATUS_TRANSFERRED,
        changed_by_username="admin.ops",
        reason="Transferred to partner unit after asset redistribution.",
        related_mission_title=None,
    ),
    StatusHistorySeed(
        drone_serial="FPV-SUP-24008",
        from_status=Drone.STATUS_MAINTENANCE,
        to_status=Drone.STATUS_DECOMMISSIONED,
        changed_by_username="root.admin",
        reason="Repeated frame fatigue made continued operation unsafe.",
        related_mission_title=None,
    ),
    StatusHistorySeed(
        drone_serial="FPV-ATK-24009",
        from_status=Drone.STATUS_ACTIVE,
        to_status=Drone.STATUS_WRITTEN_OFF,
        changed_by_username="root.admin",
        reason="Mission loss confirmed and write-off approved.",
        related_mission_title="Industrial Yard Strike",
    ),
    StatusHistorySeed(
        drone_serial="FPV-SUP-24010",
        from_status=Drone.STATUS_ACTIVE,
        to_status=Drone.STATUS_LOST,
        changed_by_username="admin.ops",
        reason=(
            "Telemetry link was lost during redeployment flight "
            "and the drone was not recovered."
        ),
        related_mission_title="Riverbank Signal Check",
    ),
)


WRITE_OFFS = (
    WriteOffSeed(
        drone_serial="FPV-ATK-24009",
        reason="Combat loss",
        reason_description=(
            "Drone lost during strike mission with no recoverable components."
        ),
        authorized_by_username="root.admin",
        related_mission_title="Industrial Yard Strike",
        document_number="WO-2026-ATK-009",
        written_off_at=date(2026, 4, 28),
    ),
)
