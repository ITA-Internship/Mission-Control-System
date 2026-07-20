"""Seed demo users, missions, drones, and repairs from project seed data."""

import os

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import connection, transaction

from accounts.models import (
    MilitaryUnit,
    User,
    UserProfile,
    UserRoleAuditLog,
    UserStatusLog,
)
from drones.models import Drone, DroneSpec, DroneStatusHistory, WriteOffRecord
from missions.models import Mission
from repairs.models import ComponentReplacement, DefectReport
from seed_data.drones import DRONES, seed_drones
from seed_data.missions import MISSIONS, seed_missions
from seed_data.repairs import seed_repairs
from seed_data.users import UNITS, USERS, seed_users


class Command(BaseCommand):
    """Seed demo data for local development and review environments."""

    help = "Seed database with demo data for users, missions, drones, and repairs."

    def add_arguments(self, parser):
        """Register command options for clearing data and selecting a seed module."""
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Remove existing seed data before seeding.",
        )
        parser.add_argument(
            "--module",
            choices=("users", "missions", "drones", "repairs"),
            help="Seed only one module.",
        )
        parser.add_argument(
            "--password",
            help="Password to assign to seeded demo users.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Run selected seeders and optionally clear existing seed data first."""
        if not settings.DEBUG:
            raise CommandError(
                "seed_db is allowed only in local development when DEBUG=True."
            )

        if options["clear"]:
            self._clear_seed_data()

        module = options.get("module")
        seed_password = None

        if module is None or module == "users":
            seed_password = self._resolve_seed_password(options.get("password"))
            self.stdout.write("Seeding users...")
            user_stats = seed_users(seed_password=seed_password)
            self.stdout.write(self.style.SUCCESS(self._format_stats(user_stats)))
            self.stdout.write(
                self.style.WARNING(
                    "Seeded users were marked with must_change_password=True."
                )
            )

        if module is None or module == "missions":
            self.stdout.write("Seeding missions...")
            mission_stats = seed_missions()
            self.stdout.write(self.style.SUCCESS(self._format_stats(mission_stats)))

        if module is None or module == "drones":
            self.stdout.write("Seeding drones...")
            drone_stats = seed_drones()
            self.stdout.write(self.style.SUCCESS(self._format_stats(drone_stats)))

        if module is None or module == "repairs":
            self.stdout.write("Seeding repairs...")
            repair_stats = seed_repairs()
            self.stdout.write(self.style.SUCCESS(self._format_stats(repair_stats)))

        self.stdout.write(self.style.SUCCESS("Database seeding complete."))

    def _clear_seed_data(self) -> None:
        """Remove known demo records in dependency-safe order before reseeding."""
        self.stdout.write(self.style.WARNING("Clearing existing seed data..."))

        mission_titles = [mission_seed.title for mission_seed in MISSIONS]
        drone_serials = [drone_seed.serial_number for drone_seed in DRONES]
        usernames = [user_seed.username for user_seed in USERS]
        unit_codes = [unit_seed.code for unit_seed in UNITS]

        existing_tables = set(connection.introspection.table_names())

        if DefectReport._meta.db_table in existing_tables:
            DefectReport.objects.filter(drone__serial_number__in=drone_serials).delete()

        if ComponentReplacement._meta.db_table in existing_tables:
            ComponentReplacement.objects.filter(
                drone__serial_number__in=drone_serials
            ).delete()
        Mission.objects.filter(title__in=mission_titles).delete()
        DroneStatusHistory.objects.filter(
            drone__serial_number__in=drone_serials
        ).delete()
        WriteOffRecord.objects.filter(drone__serial_number__in=drone_serials).delete()
        DroneSpec.objects.filter(drone__serial_number__in=drone_serials).delete()
        Drone.objects.filter(serial_number__in=drone_serials).delete()
        UserRoleAuditLog.objects.filter(target_user__username__in=usernames).delete()
        UserStatusLog.objects.filter(target_user__username__in=usernames).delete()
        UserProfile.objects.filter(user__username__in=usernames).delete()
        User.objects.filter(username__in=usernames).delete()
        MilitaryUnit.objects.filter(code__in=unit_codes).delete()

    def _format_stats(self, stats: dict[str, int]) -> str:
        """Format seeding counters for console output."""
        return ", ".join(f"{key}={value}" for key, value in stats.items())

    def _resolve_seed_password(self, password_option: str | None) -> str:
        if password_option:
            return password_option

        if env_password := os.getenv("SEED_DEFAULT_PASSWORD"):
            return env_password

        raise CommandError(
            "Seeding users requires --password or SEED_DEFAULT_PASSWORD. "
            "The password is not generated or printed to avoid leaking credentials."
        )
