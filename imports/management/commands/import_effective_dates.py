from django.core.management.base import BaseCommand

import pandas as pd

from contracts.models import ContractPackage


class Command(BaseCommand):

    help = "Import Effective Dates"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            type=str
        )

    def handle(self, *args, **options):

        df = pd.read_excel(
            options["file_path"],
            sheet_name="1"
        )

        updated = 0
        not_found = 0
        duplicates = 0
        invalid_dates = 0

        for _, row in df.iterrows():

            company_name = str(
                row.get("الشركه", "")
            ).split("\n")[0].strip()

            code = str(
                row.get("الكود", "")
            ).strip()

            effective_date = row.get(
                "اعتبارا من"
            )

            if (
                not company_name
                or company_name == "nan"
                or not code
                or code == "nan"
            ):
                continue

            if pd.isna(effective_date):
                invalid_dates += 1
                continue

            try:

                effective_date = pd.to_datetime(
                    effective_date
                ).date()

            except Exception:

                invalid_dates += 1
                continue

            matches = ContractPackage.objects.filter(
                package__code=code,
                contract__entity__name=company_name
            )

            count = matches.count()

            if count == 0:

                not_found += 1
                continue

            if count > 1:

                duplicates += 1
                continue

            cp = matches.first()

            cp.effective_from = effective_date

            cp.save(
                update_fields=[
                    "effective_from"
                ]
            )

            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"""
Updated: {updated}
Not Found: {not_found}
Duplicates: {duplicates}
Invalid Dates: {invalid_dates}
"""
            )
        )