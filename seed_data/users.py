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
from seed_data.data.users_data import TEST_PASSWORD, UNITS, USERS, UserSeed


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
