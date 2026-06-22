from django.core.management.base import BaseCommand

import pandas as pd

from medical_catalog.models import (
    Package,
    Specialty,
)


class Command(BaseCommand):

    help = "Import Package Specialties"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            type=str
        )

    def handle(self, *args, **options):

        file_path = options["file_path"]

        df = pd.read_excel(
            file_path,
            sheet_name="packages "
        )

        updated = 0
        not_found = 0
        created_specialties = 0

        for _, row in df.iterrows():

            code = str(
                row.get("Code", "")
            ).strip()

            specialty_name = str(
                row.get("Specialization ", "")
            ).strip()

            if (
                not code
                or code.lower() == "nan"
                or not specialty_name
                or specialty_name.lower() == "nan"
            ):
                continue

            specialty, created = (
                Specialty.objects.get_or_create(
                    name=specialty_name,
                    defaults={
                        "is_active": True
                    }
                )
            )

            if created:
                created_specialties += 1

            package = (
                Package.objects.filter(
                    code=code
                ).first()
            )

            if not package:

                print(
                    f"PACKAGE NOT FOUND: {code}"
                )

                not_found += 1
                continue

            package.specialty = specialty

            package.save(
                update_fields=[
                    "specialty"
                ]
            )

            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"""
Updated Packages: {updated}
Created Specialties: {created_specialties}
Packages Not Found: {not_found}
                """
            )
        )