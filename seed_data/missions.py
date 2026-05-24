from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from django.utils import timezone

from accounts.models import User
from missions.models import Mission, Result, Status


@dataclass(frozen=True)
class MissionSeed:
    title: str
    commander_username: str
    created_by_username: str
    status: str
    result: str | None
    location_description: str
    latitude: Decimal
    longitude: Decimal
    started_days_offset: int | None
    duration_minutes: int | None
    notes: str


MISSIONS = (
    MissionSeed(
        title="Northern Treeline Recon",
        commander_username="commander.north",
        created_by_username="admin.ops",
        status=Status.COMPLETED,
        result=Result.SUCCESS,
        location_description="Forest edge north of the supply route.",
        latitude=Decimal("50.455100"),
        longitude=Decimal("30.523400"),
        started_days_offset=-28,
        duration_minutes=34,
        notes="Operators: operator.alpha, operator.charlie. Drones: Falcon Eye 1. Artifact: recon_north_0426.mp4. Post-mission drone condition: nominal.",
    ),
    MissionSeed(
        title="Riverbank Signal Check",
        commander_username="commander.south",
        created_by_username="admin.ops",
        status=Status.COMPLETED,
        result=Result.SUCCESS,
        location_description="Riverbank relay corridor near fallback crossing.",
        latitude=Decimal("49.993500"),
        longitude=Decimal("36.230400"),
        started_days_offset=-24,
        duration_minutes=26,
        notes="Operators: operator.bravo. Drones: Relay 1. Artifact: relay_signal_report_0430.json. Post-mission drone condition: stable relay output.",
    ),
    MissionSeed(
        title="Industrial Yard Strike",
        commander_username="commander.north",
        created_by_username="root.admin",
        status=Status.COMPLETED,
        result=Result.FAILURE,
        location_description="Industrial storage yard on the eastern perimeter.",
        latitude=Decimal("48.922600"),
        longitude=Decimal("24.711100"),
        started_days_offset=-21,
        duration_minutes=18,
        notes="Operators: operator.alpha. Drones: Lancer 1. Artifact: strike_loss_report_0503.pdf. Outcome: target engagement attempted, drone lost, asset later written off.",
    ),
    MissionSeed(
        title="Southern Tree Line Sweep",
        commander_username="commander.south",
        created_by_username="admin.ops",
        status=Status.COMPLETED,
        result=Result.SUCCESS,
        location_description="Southern tree line covering approach to reserve trench.",
        latitude=Decimal("47.838800"),
        longitude=Decimal("35.139600"),
        started_days_offset=-17,
        duration_minutes=29,
        notes="Operators: operator.bravo, operator.charlie. Drones: Hammer 2, Scout 1. Artifact: sweep_south_0508.mp4. Post-mission maintenance note: motor vibration flagged on Hammer 2.",
    ),
    MissionSeed(
        title="Rail Crossing Interdiction",
        commander_username="commander.north",
        created_by_username="root.admin",
        status=Status.COMPLETED,
        result=Result.FAILURE,
        location_description="Rail crossing west of logistics junction.",
        latitude=Decimal("48.464700"),
        longitude=Decimal("35.046200"),
        started_days_offset=-13,
        duration_minutes=22,
        notes="Operators: operator.alpha, operator.bravo. Drones: Spear 1. Artifact: interdiction_0512.log. Outcome: forced landing after battery lead damage; airframe recovered damaged.",
    ),
    MissionSeed(
        title="Urban Block Observation",
        commander_username="commander.south",
        created_by_username="admin.ops",
        status=Status.COMPLETED,
        result=Result.SUCCESS,
        location_description="Dense urban block near municipal checkpoint.",
        latitude=Decimal("46.482500"),
        longitude=Decimal("30.723300"),
        started_days_offset=-10,
        duration_minutes=16,
        notes="Operators: operator.charlie. Drones: Scout 1. Artifact: urban_block_0515.mp4. Post-mission drone condition: propellers replaced after debris contact.",
    ),
    MissionSeed(
        title="Forward Relay Setup",
        commander_username="commander.north",
        created_by_username="root.admin",
        status=Status.ACTIVE,
        result=None,
        location_description="Forward relay point behind primary observation ridge.",
        latitude=Decimal("49.444400"),
        longitude=Decimal("32.059800"),
        started_days_offset=0,
        duration_minutes=None,
        notes="Operators: operator.bravo. Planned drone support: Falcon Eye 2 and Hammer 1. Mission currently active; artifact pending.",
    ),
    MissionSeed(
        title="Dawn Recon Window",
        commander_username="commander.south",
        created_by_username="admin.ops",
        status=Status.PLANNED,
        result=None,
        location_description="Open field corridor east of reserve logistics line.",
        latitude=Decimal("50.907700"),
        longitude=Decimal("34.798100"),
        started_days_offset=2,
        duration_minutes=25,
        notes="Planned operators: operator.alpha, operator.bravo. Planned drones: Falcon Eye 1. Objective: verify route accessibility before sunrise convoy movement.",
    ),
    MissionSeed(
        title="Bridge Approach Survey",
        commander_username="commander.north",
        created_by_username="root.admin",
        status=Status.PLANNED,
        result=None,
        location_description="Bridge approach sector covering both embankments.",
        latitude=Decimal("49.588300"),
        longitude=Decimal("34.551400"),
        started_days_offset=4,
        duration_minutes=20,
        notes="Planned operators: operator.charlie. Planned drones: Hammer 1 and Scout 1. Objective: map defensive obstacles and thermal signatures.",
    ),
    MissionSeed(
        title="Fallback Route Mapping",
        commander_username="commander.south",
        created_by_username="admin.ops",
        status=Status.PLANNED,
        result=None,
        location_description="Secondary fallback route south-west of artillery support line.",
        latitude=Decimal("48.619700"),
        longitude=Decimal("22.287900"),
        started_days_offset=6,
        duration_minutes=32,
        notes="Planned operators: operator.alpha. Planned drones: Falcon Eye 2. Objective: capture updated terrain references and route obstacles.",
    ),
)


class MissionSeeder:
    def __init__(self) -> None:
        self.users = self._load_users()

    def seed(self) -> dict[str, int]:
        created_count = 0
        updated_count = 0

        for mission_seed in MISSIONS:
            _, created = self._upsert_mission(mission_seed)
            if created:
                created_count += 1
            else:
                updated_count += 1

        return {
            "missions_created": created_count,
            "missions_updated": updated_count,
        }

    def _load_users(self) -> dict[str, User]:
        usernames = {
            mission_seed.commander_username for mission_seed in MISSIONS
        } | {
            mission_seed.created_by_username for mission_seed in MISSIONS
        }
        users = {user.username: user for user in User.objects.filter(username__in=usernames)}
        missing_usernames = usernames - users.keys()

        if missing_usernames:
            missing_users_display = ", ".join(sorted(missing_usernames))
            raise User.DoesNotExist(f"Missing required users: {missing_users_display}")

        return users

    def _upsert_mission(self, mission_seed: MissionSeed) -> tuple[Mission, bool]:
        started_at, ended_at = self._build_schedule(mission_seed)
        commander = self.users[mission_seed.commander_username]
        created_by = self.users[mission_seed.created_by_username]

        mission, created = Mission.objects.update_or_create(
            title=mission_seed.title,
            defaults={
                "commander": commander,
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
