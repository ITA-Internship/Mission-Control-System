from dataclasses import dataclass

from roles.models import (
    ADMIN_CODE,
    COMMANDER_CODE,
    OPERATOR_CODE,
    TECHNICIAN_CODE,
    VIEWER_CODE,
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
