from dataclasses import dataclass

from accounts.models import (
    MilitaryUnit,
    User,
    UserProfile,
    UserRoleAuditLog,
    UserStatusLog,
)
from roles.models import (
    ADMIN_CODE,
    COMMANDER_CODE,
    OPERATOR_CODE,
    TECHNICIAN_CODE,
    VIEWER_CODE,
    Role,
)


TEST_PASSWORD = "Test@1234"


@dataclass(frozen=True)
class UnitSeed:
    code: str
    name: str
    description: str


@dataclass(frozen=True)
class UserSeed:
    username: str
    email: str
    first_name: str
    last_name: str
    role_code: str
    unit_code: str
    rank: str
    contact: str
    is_active: bool
    is_staff: bool = False
    is_superuser: bool = False


UNITS = (
    UnitSeed(
        code="AER-01",
        name="Aerial Recon Unit 01",
        description="Primary reconnaissance and mission planning unit.",
    ),
    UnitSeed(
        code="ATK-02",
        name="Strike Coordination Unit 02",
        description="Operational unit responsible for FPV strike coordination.",
    ),
    UnitSeed(
        code="SUP-03",
        name="Technical Support Unit 03",
        description="Maintenance and technical recovery unit.",
    ),
)


USERS = (
    UserSeed(
        username="root.admin",
        email="root.admin@seed.local",
        first_name="Oleksandr",
        last_name="Koval",
        role_code=ADMIN_CODE,
        unit_code="AER-01",
        rank="Colonel",
        contact="+380500000001",
        is_active=True,
        is_staff=True,
        is_superuser=True,
    ),
    UserSeed(
        username="admin.ops",
        email="admin.ops@seed.local",
        first_name="Iryna",
        last_name="Melnyk",
        role_code=ADMIN_CODE,
        unit_code="AER-01",
        rank="Major",
        contact="+380500000002",
        is_active=True,
        is_staff=True,
    ),
    UserSeed(
        username="commander.north",
        email="commander.north@seed.local",
        first_name="Taras",
        last_name="Havryliuk",
        role_code=COMMANDER_CODE,
        unit_code="ATK-02",
        rank="Captain",
        contact="+380500000003",
        is_active=True,
    ),
    UserSeed(
        username="commander.south",
        email="commander.south@seed.local",
        first_name="Maksym",
        last_name="Bondar",
        role_code=COMMANDER_CODE,
        unit_code="ATK-02",
        rank="Captain",
        contact="+380500000004",
        is_active=True,
    ),
    UserSeed(
        username="operator.alpha",
        email="operator.alpha@seed.local",
        first_name="Andrii",
        last_name="Tkachenko",
        role_code=OPERATOR_CODE,
        unit_code="ATK-02",
        rank="Senior Lieutenant",
        contact="+380500000005",
        is_active=True,
    ),
    UserSeed(
        username="operator.bravo",
        email="operator.bravo@seed.local",
        first_name="Dmytro",
        last_name="Shevchenko",
        role_code=OPERATOR_CODE,
        unit_code="ATK-02",
        rank="Lieutenant",
        contact="+380500000006",
        is_active=True,
    ),
    UserSeed(
        username="operator.charlie",
        email="operator.charlie@seed.local",
        first_name="Roman",
        last_name="Savchenko",
        role_code=OPERATOR_CODE,
        unit_code="AER-01",
        rank="Lieutenant",
        contact="+380500000007",
        is_active=False,
    ),
    UserSeed(
        username="tech.airframe",
        email="tech.airframe@seed.local",
        first_name="Serhii",
        last_name="Klymenko",
        role_code=TECHNICIAN_CODE,
        unit_code="SUP-03",
        rank="Warrant Officer",
        contact="+380500000008",
        is_active=True,
    ),
    UserSeed(
        username="tech.electro",
        email="tech.electro@seed.local",
        first_name="Pavlo",
        last_name="Marchenko",
        role_code=TECHNICIAN_CODE,
        unit_code="SUP-03",
        rank="Warrant Officer",
        contact="+380500000009",
        is_active=True,
    ),
    UserSeed(
        username="viewer.ops",
        email="viewer.ops@seed.local",
        first_name="Olena",
        last_name="Danylchuk",
        role_code=VIEWER_CODE,
        unit_code="AER-01",
        rank="Civilian Specialist",
        contact="+380500000010",
        is_active=True,
    ),
    UserSeed(
        username="viewer.audit",
        email="viewer.audit@seed.local",
        first_name="Nataliia",
        last_name="Petrenko",
        role_code=VIEWER_CODE,
        unit_code="SUP-03",
        rank="Civilian Specialist",
        contact="+380500000011",
        is_active=True,
    ),
)


class UserSeeder:
    def __init__(self) -> None:
        self.roles = self._load_roles()
        self.units: dict[str, MilitaryUnit] = {}

    def seed(self) -> dict[str, int]:
        self._seed_units()

        created_count = 0
        updated_count = 0

        for user_seed in USERS:
            _, created = self._upsert_user(user_seed)
            if created:
                created_count += 1
            else:
                updated_count += 1

        self._seed_status_logs()
        self._seed_role_audit_logs()

        return {
            "units": len(self.units),
            "users_created": created_count,
            "users_updated": updated_count,
        }

    def _load_roles(self) -> dict[str, Role]:
        role_codes = {
            ADMIN_CODE,
            COMMANDER_CODE,
            OPERATOR_CODE,
            TECHNICIAN_CODE,
            VIEWER_CODE,
        }
        roles = {role.code: role for role in Role.objects.filter(code__in=role_codes)}
        missing_codes = role_codes - roles.keys()

        if missing_codes:
            missing_codes_display = ", ".join(sorted(missing_codes))
            raise Role.DoesNotExist(f"Missing required roles: {missing_codes_display}")

        return roles

    def _seed_units(self) -> None:
        for unit_seed in UNITS:
            unit, _ = MilitaryUnit.objects.update_or_create(
                code=unit_seed.code,
                defaults={
                    "name": unit_seed.name,
                    "description": unit_seed.description,
                    "is_active": True,
                },
            )
            self.units[unit.code] = unit

    def _upsert_user(self, user_seed: UserSeed) -> tuple[User, bool]:
        role = self.roles[user_seed.role_code]
        unit = self.units[user_seed.unit_code]

        user, created = User.objects.update_or_create(
            username=user_seed.username,
            defaults={
                "email": user_seed.email,
                "first_name": user_seed.first_name,
                "last_name": user_seed.last_name,
                "role": role,
                "unit": unit,
                "is_active": user_seed.is_active,
                "is_staff": user_seed.is_staff,
                "is_superuser": user_seed.is_superuser,
            },
        )

        user.set_password(TEST_PASSWORD)
        user.save(update_fields=["password"])

        UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "rank": user_seed.rank,
                "contact": user_seed.contact,
                "profile_picture": "",
            },
        )

        return user, created

    def _seed_status_logs(self) -> None:
        root_admin = User.objects.get(username="root.admin")
        inactive_operator = User.objects.get(username="operator.charlie")

        UserStatusLog.objects.update_or_create(
            target_user=inactive_operator,
            changed_by=root_admin,
            new_status=False,
            defaults={
                "old_status": True,
                "reason": "Seeded inactive account for access-control testing.",
            },
        )

    def _seed_role_audit_logs(self) -> None:
        root_admin = User.objects.get(username="root.admin")
        operator = User.objects.get(username="operator.charlie")
        viewer_role = self.roles[VIEWER_CODE]
        operator_role = self.roles[OPERATOR_CODE]

        UserRoleAuditLog.objects.update_or_create(
            target_user=operator,
            changed_by=root_admin,
            previous_role=viewer_role,
            new_role=operator_role,
        )


def seed_users() -> dict[str, int]:
    return UserSeeder().seed()
