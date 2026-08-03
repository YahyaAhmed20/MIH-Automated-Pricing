from django.core.management.base import BaseCommand

from imports.services.package_validation_service import (
    PackageValidationService,
)


class Command(BaseCommand):
    help = "Validate package database"

    def handle(self, *args, **options):

        result = PackageValidationService.summary()

        self.stdout.write("")

        if result["duplicate_groups"] == 0:

            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Package database is healthy."
                )
            )

        else:

            self.stdout.write(
                self.style.WARNING(
                    f"⚠ Found {result['duplicate_groups']} duplicate groups."
                )
            )