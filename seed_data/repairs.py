from accounts.models import User
from drones.models import Drone
from repairs.models import ComponentReplacement, DefectReport
from seed_data.data.repairs_data import (
    COMPONENT_REPLACEMENTS,
    DEFECT_REPORTS,
    ComponentReplacementSeed,
    DefectReportSeed,
)


class RepairSeeder:
    def __init__(self) -> None:
        self.drones = self._load_drones()
        self.users = self._load_users()

    def seed(self) -> dict[str, int]:
        defect_created = 0
        defect_updated = 0
        replacement_created = 0
        replacement_updated = 0

        for defect_seed in DEFECT_REPORTS:
            _, created = self._upsert_defect_report(defect_seed)
            if created:
                defect_created += 1
            else:
                defect_updated += 1

        for replacement_seed in COMPONENT_REPLACEMENTS:
            _, created = self._upsert_component_replacement(replacement_seed)
            if created:
                replacement_created += 1
            else:
                replacement_updated += 1

        return {
            "defect_reports_created": defect_created,
            "defect_reports_updated": defect_updated,
            "component_replacements_created": replacement_created,
            "component_replacements_updated": replacement_updated,
        }

    def _load_drones(self) -> dict[str, Drone]:
        drone_serials = {
            seed.drone_serial for seed in DEFECT_REPORTS
        } | {seed.drone_serial for seed in COMPONENT_REPLACEMENTS}
        drones = {
            drone.serial_number: drone
            for drone in Drone.objects.filter(serial_number__in=drone_serials)
        }
        missing_serials = drone_serials - drones.keys()

        if missing_serials:
            missing_serials_display = ", ".join(sorted(missing_serials))
            raise Drone.DoesNotExist(
                f"Missing required seeded drones: {missing_serials_display}"
            )

        return drones

    def _load_users(self) -> dict[str, User]:
        usernames = {
            seed.reporter_username
            for seed in DEFECT_REPORTS
            if seed.reporter_username is not None
        } | {
            seed.replaced_by_username
            for seed in COMPONENT_REPLACEMENTS
            if seed.replaced_by_username is not None
        }
        return {
            user.username: user for user in User.objects.filter(username__in=usernames)
        }

    def _upsert_defect_report(
        self,
        defect_seed: DefectReportSeed,
    ) -> tuple[DefectReport, bool]:
        drone = self.drones[defect_seed.drone_serial]
        reporter = self.users.get(defect_seed.reporter_username)

        return DefectReport.objects.update_or_create(
            drone=drone,
            defect_type=defect_seed.defect_type,
            detected_at=defect_seed.detected_at,
            defaults={
                "severity": defect_seed.severity,
                "description": defect_seed.description,
                "reporter": reporter,
            },
        )

    def _upsert_component_replacement(
        self,
        replacement_seed: ComponentReplacementSeed,
    ) -> tuple[ComponentReplacement, bool]:
        drone = self.drones[replacement_seed.drone_serial]
        replaced_by = self.users.get(replacement_seed.replaced_by_username)

        return ComponentReplacement.objects.update_or_create(
            drone=drone,
            component_type=replacement_seed.component_type,
            new_serial_number=replacement_seed.new_serial_number,
            replaced_at=replacement_seed.replaced_at,
            defaults={
                "component_name": replacement_seed.component_name,
                "old_serial_number": replacement_seed.old_serial_number,
                "reason": replacement_seed.reason,
                "replaced_by": replaced_by,
            },
        )


def seed_repairs() -> dict[str, int]:
    return RepairSeeder().seed()
