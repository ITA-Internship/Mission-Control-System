from accounts.models import MilitaryUnit, User
from drones.models import (
    Drone,
    DroneModel,
    DroneSpec,
    DroneStatusHistory,
    WriteOffRecord,
)
from missions.models import Mission
from seed_data.data.drones_data import (
    DRONE_MODELS,
    DRONES,
    STATUS_HISTORY,
    WRITE_OFFS,
    DroneSeed,
)


class DroneSeeder:
    def __init__(self) -> None:
        self.units = self._load_units()
        self.users = self._load_users()
        self.missions = self._load_missions()
        self.drones: dict[str, Drone] = {}
        self.drone_models: dict[str, DroneModel] = {}

    def seed(self) -> dict[str, int]:
        created_count = 0
        updated_count = 0

        self._seed_drone_models()

        for drone_seed in DRONES:
            _, created = self._upsert_drone(drone_seed)
            if created:
                created_count += 1
            else:
                updated_count += 1

        self._seed_status_history()
        self._seed_writeoffs()

        return {
            "drones_created": created_count,
            "drones_updated": updated_count,
            "status_history_records": len(STATUS_HISTORY),
            "writeoff_records": len(WRITE_OFFS),
        }

    def _load_units(self) -> dict[str, MilitaryUnit]:
        unit_codes = {drone_seed.unit_code for drone_seed in DRONES}
        units = {
            unit.code: unit for unit in MilitaryUnit.objects.filter(code__in=unit_codes)
        }
        missing_codes = unit_codes - units.keys()

        if missing_codes:
            missing_codes_display = ", ".join(sorted(missing_codes))
            raise MilitaryUnit.DoesNotExist(
                f"Missing required military units: {missing_codes_display}"
            )

        return units

    def _load_users(self) -> dict[str, User]:
        usernames = {
            seed.changed_by_username
            for seed in STATUS_HISTORY
            if seed.changed_by_username is not None
        } | {
            seed.authorized_by_username
            for seed in WRITE_OFFS
            if seed.authorized_by_username is not None
        }
        return {
            user.username: user for user in User.objects.filter(username__in=usernames)
        }

    def _load_missions(self) -> dict[str, Mission]:
        mission_titles = {
            seed.related_mission_title
            for seed in STATUS_HISTORY
            if seed.related_mission_title is not None
        } | {
            seed.related_mission_title
            for seed in WRITE_OFFS
            if seed.related_mission_title is not None
        }
        return {
            mission.title: mission
            for mission in Mission.objects.filter(title__in=mission_titles)
        }

    def _upsert_drone(self, drone_seed: DroneSeed) -> tuple[Drone, bool]:
        unit = self.units[drone_seed.unit_code]
        drone_model_instance = self.drone_models.get(drone_seed.drone_model_name)

        drone, created = Drone.objects.update_or_create(
            serial_number=drone_seed.serial_number,
            defaults={
                "inventory_number": drone_seed.inventory_number,
                "name": drone_seed.name,
                "drone_model": drone_model_instance,
                "classification": drone_model_instance.get_allowed_classifications()[0],
                "status": drone_seed.status,
                "military_unit": unit,
                "acquired_at": drone_seed.acquired_at,
                "notes": drone_seed.notes,
            },
        )

        DroneSpec.objects.update_or_create(
            drone=drone,
            defaults={
                "frame_type": drone_seed.spec.frame_type,
                "motor_model": drone_seed.spec.motor_model,
                "battery_type": drone_seed.spec.battery_type,
                "battery_capacity_mah": drone_seed.spec.battery_capacity_mah,
                "camera_model": drone_seed.spec.camera_model,
                "vtx_model": drone_seed.spec.vtx_model,
                "flight_controller": drone_seed.spec.flight_controller,
                "firmware_version": drone_seed.spec.firmware_version,
                "max_speed_kmh": drone_seed.spec.max_speed_kmh,
                "max_range_km": drone_seed.spec.max_range_km,
                "max_flight_time_min": drone_seed.spec.max_flight_time_min,
                "frequency_mhz": drone_seed.spec.frequency_mhz,
                "payload_capacity_g": drone_seed.spec.payload_capacity_g,
            },
        )

        self.drones[drone.serial_number] = drone
        return drone, created

    def _seed_status_history(self) -> None:
        for history_seed in STATUS_HISTORY:
            drone = self.drones[history_seed.drone_serial]
            changed_by = self.users.get(history_seed.changed_by_username)
            related_mission = self.missions.get(history_seed.related_mission_title)

            DroneStatusHistory.objects.update_or_create(
                drone=drone,
                from_status=history_seed.from_status,
                to_status=history_seed.to_status,
                reason=history_seed.reason,
                defaults={
                    "changed_by": changed_by,
                    "related_mission": related_mission,
                    "related_repair_order_id": None,
                    "related_writeoff": None,
                },
            )

    def _seed_writeoffs(self) -> None:
        for writeoff_seed in WRITE_OFFS:
            drone = self.drones[writeoff_seed.drone_serial]
            authorized_by = self.users.get(writeoff_seed.authorized_by_username)
            related_mission = self.missions.get(writeoff_seed.related_mission_title)

            writeoff_record, _ = WriteOffRecord.objects.update_or_create(
                drone=drone,
                defaults={
                    "reason": writeoff_seed.reason,
                    "reason_description": writeoff_seed.reason_description,
                    "authorized_by": authorized_by,
                    "related_mission": related_mission,
                    "document_number": writeoff_seed.document_number,
                    "written_off_at": writeoff_seed.written_off_at,
                },
            )

            DroneStatusHistory.objects.filter(
                drone=drone,
                to_status=Drone.STATUS_WRITTEN_OFF,
            ).update(related_writeoff=writeoff_record)

    def _seed_drone_models(self) -> None:
        for drone_model_seed in DRONE_MODELS:
            drone_model, _ = DroneModel.objects.update_or_create(
                name=drone_model_seed.name,
                defaults={
                    "manufacturer": drone_model_seed.manufacturer,
                    "description": drone_model_seed.description,
                    "supported_classifications": (
                        drone_model_seed.supported_classifications
                    ),
                    "is_active": drone_model_seed.is_active,
                },
            )
            self.drone_models[drone_model_seed.name] = drone_model


def seed_drones() -> dict[str, int]:
    return DroneSeeder().seed()
