"""
``python manage.py backfill_data_quality``

Re-applies normalization (trim, lowercase, address keys, etc.) across every
Company and Contact so the dedup indexes are consistent after an upgrade or a
direct data load. Safe to run repeatedly.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.data_quality.services import backfill_normalization


class Command(BaseCommand):
    help = "Re-run normalization across companies and contacts."

    def handle(self, *args, **options) -> None:
        counts = backfill_normalization()
        self.stdout.write(
            self.style.SUCCESS(
                "Backfill complete: "
                f"{counts['companies']} companies, "
                f"{counts['contacts']} contacts re-normalized."
            )
        )
