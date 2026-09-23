"""
``python manage.py detect_duplicates [--clear]``

Run the five deduplication rules against the lead database and populate
``DuplicateGroup``. Safe to re-run; existing pairs are not duplicated.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.data_quality.services import detect_duplicates


class Command(BaseCommand):
    help = "Detect potential duplicate leads."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing duplicate groups before scanning.",
        )

    def handle(self, *args, **options) -> None:
        result = detect_duplicates(clear_existing=options["clear"])
        total = result.pop("new_groups")
        self.stdout.write(self.style.SUCCESS(f"Detected {total} new duplicate groups."))
        for reason, count in result.items():
            if count:
                self.stdout.write(f"  {reason:24} {count}")
