from datetime import datetime, timedelta

from django.utils import timezone

from accounts.models import MilitaryUnit, User
from drones.models import Drone
from missions.models import Mission, MissionDrone
from seed_data.data.missions_data import MISSION_DRONES, MISSIONS, MissionSeed


class MissionSeeder:
    def __init__(self) -> None:
        self.users = self._load_users()
        self.units = self._load_units()
        self.drones = self._load_drones()
        self.missions = {}

    def seed(self) -> dict[str, int]:
        created_count = 0
        updated_count = 0

        for mission_seed in MISSIONS:
            mission, created = self._upsert_mission(mission_seed)
            self.missions[mission.title] = mission
            if created:
                created_count += 1
            else:
                updated_count += 1

        md_created = 0
        md_updated = 0
        for md_seed in MISSION_DRONES:
            _, created = self._upsert_mission_drone(md_seed)
            if created:
                md_created += 1
            else:
                md_updated += 1

        return {
            "missions_created": created_count,
            "missions_updated": updated_count,
            "mission_drones_created": md_created,
            "mission_drones_updated": md_updated,
        }

    def _load_users(self) -> dict[str, User]:
        usernames = (
            {mission_seed.commander_username for mission_seed in MISSIONS}
            | {mission_seed.created_by_username for mission_seed in MISSIONS}
            | {md_seed.operator_username for md_seed in MISSION_DRONES}
        )
        users = {
            user.username: user for user in User.objects.filter(username__in=usernames)
        }
        missing_usernames = usernames - users.keys()

        if missing_usernames:
            missing_users_display = ", ".join(sorted(missing_usernames))
            raise User.DoesNotExist(f"Missing required users: {missing_users_display}")

        return users

    def _load_units(self) -> dict[str, MilitaryUnit]:
        unit_codes = {mission_seed.unit_code for mission_seed in MISSIONS}
        units = {
            unit.code: unit for unit in MilitaryUnit.objects.filter(code__in=unit_codes)
        }
        missing_unit_codes = unit_codes - units.keys()

        if missing_unit_codes:
            missing_units_display = ", ".join(sorted(missing_unit_codes))
            raise MilitaryUnit.DoesNotExist(
                f"Missing required mission units: {missing_units_display}"
            )

        return units

    def _load_drones(self) -> dict[str, Drone]:
        serials = {md_seed.drone_serial_number for md_seed in MISSION_DRONES}
        drones = {
            drone.serial_number: drone
            for drone in Drone.objects.filter(serial_number__in=serials)
        }
        missing_serials = serials - drones.keys()

        if missing_serials:
            missing_display = ", ".join(sorted(missing_serials))
            raise Drone.DoesNotExist(
                f"Missing required drones for missions: {missing_display}"
            )

        return drones

    def _upsert_mission(self, mission_seed: MissionSeed) -> tuple[Mission, bool]:
        started_at, ended_at = self._build_schedule(mission_seed)
        commander = self.users[mission_seed.commander_username]
        created_by = self.users[mission_seed.created_by_username]
        unit = self.units[mission_seed.unit_code]

        mission, created = Mission.objects.update_or_create(
            title=mission_seed.title,
            defaults={
                "commander": commander,
                "unit": unit,
                "status": mission_seed.status,
                "result": mission_seed.result,
                "location_description": mission_seed.location_description,
                "latitude": mission_seed.latitude,
                "longitude": mission_seed.longitude,
                "started_at": started_at,
                "ended_at": ended_at,
                "notes": mission_seed.notes,
                "created_by": created_by,
            },
        )

        return mission, created

    def _upsert_mission_drone(self, md_seed) -> tuple[MissionDrone, bool]:
        mission = self.missions[md_seed.mission_title]
        drone = self.drones[md_seed.drone_serial_number]
        operator = self.users[md_seed.operator_username]

        md, created = MissionDrone.objects.update_or_create(
            mission=mission,
            drone=drone,
            defaults={
                "operator": operator,
                "flight_started_at": mission.started_at,
                "flight_ended_at": mission.ended_at,
                "condition_after": md_seed.condition_after,
                "condition_description": md_seed.condition_description,
            },
        )
        return md, created

    def _build_schedule(
        self,
        mission_seed: MissionSeed,
    ) -> tuple[datetime | None, datetime | None]:
        if mission_seed.started_days_offset is None:
            return None, None

        started_at = timezone.now() + timedelta(days=mission_seed.started_days_offset)

        if mission_seed.duration_minutes is None:
            return started_at, None

        ended_at = started_at + timedelta(minutes=mission_seed.duration_minutes)
        return started_at, ended_at


def seed_missions() -> dict[str, int]:
    return MissionSeeder().seed()
