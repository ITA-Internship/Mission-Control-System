from django.core.management.base import BaseCommand

from accounts.models import User
from seed_data.data.users_data import USERS


class Command(BaseCommand):
    help = "Disable known seeded demo users outside local development."

    def handle(self, *args, **options):
        seeded_usernames = [user_seed.username for user_seed in USERS]
        queryset = User.objects.filter(username__in=seeded_usernames)

        updated_count = queryset.update(
            is_active=False,
            is_staff=False,
            is_superuser=False,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Disabled {updated_count} seeded user(s) outside local development."
            )
        )
