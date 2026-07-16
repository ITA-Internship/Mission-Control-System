from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from media.models import MediaAuditLog


class Command(BaseCommand):
    help = (
        "Enforce the media audit-log retention policy by deleting MediaAuditLog "
        "entries older than MEDIA_AUDIT_LOG_RETENTION_DAYS. Intended to run on a "
        "schedule (see purge_media_audit_logs_task)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Report how many entries would be removed without deleting them.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        days = settings.MEDIA_AUDIT_LOG_RETENTION_DAYS

        if days <= 0:
            self.stdout.write(
                "MediaAuditLog retention disabled (days <= 0); nothing to do."
            )
            return

        cutoff = timezone.now() - timedelta(days=days)
        expired = MediaAuditLog.objects.filter(created_at__lt=cutoff)
        count = expired.count()

        if not dry_run and count:
            MediaAuditLog.objects.purge_older_than(cutoff)

        verb = "Would remove" if dry_run else "Removed"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {count} MediaAuditLog entries older than {cutoff.isoformat()}."
            )
        )
