from django.core.management.base import BaseCommand
import pandas as pd
from datetime import date, datetime
from contracts.models import ContractPackage
from imports.services.excel_provider import ExcelProvider


class Command(BaseCommand):

    help = "Import Effective Dates"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        df = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="1",
            header=None,
            force_reload=True,
        )

        rows = df.to_dict("records")

        print("⏳ Loading ContractPackages...")
        contract_packages_cache = {}
        for cp in ContractPackage.objects.select_related('package', 'contract__entity').iterator():
            key = (
                cp.package.code if cp.package else None,
                cp.contract.entity.name if cp.contract and cp.contract.entity else None,
            )
            contract_packages_cache[key] = cp
        print(f"   ✅ {len(contract_packages_cache)} ContractPackages loaded")

        updated = 0
        not_found = 0
        invalid_dates = 0
        packages_to_update = []

        print("⏳ Processing rows...")
        total = len(rows)

        for idx, row in enumerate(rows, start=1):

            company_name = str(row.get(0, "")).split("\n")[0].strip()
            code = str(row.get(6, "")).strip()
            effective_date = row.get(7, None)

            if not company_name or company_name == "nan" or not code or code == "nan":
                continue

            # ✅ تحقق من أن التاريخ موجود
            if effective_date is None or pd.isna(effective_date):
                invalid_dates += 1
                continue

            try:
                # ✅ تحويل التاريخ
                if isinstance(effective_date, pd.Timestamp):
                    effective_date = effective_date.date()
                elif isinstance(effective_date, str):
                    effective_date = pd.to_datetime(effective_date, dayfirst=True).date()
                elif isinstance(effective_date, datetime):
                    effective_date = effective_date.date()
                else:
                    invalid_dates += 1
                    continue
            except Exception:
                invalid_dates += 1
                continue

            # ✅ تأكد من أن effective_date هو date وليس NaT
            if not isinstance(effective_date, date):
                invalid_dates += 1
                continue

            # ✅ تأكد من أن effective_date مش NaT (لأن NaT مش date)
            if pd.isna(effective_date):
                invalid_dates += 1
                continue

            key = (code, company_name)
            cp = contract_packages_cache.get(key)

            if not cp:
                not_found += 1
                continue

            cp.effective_from = effective_date
            packages_to_update.append(cp)
            updated += 1

            if len(packages_to_update) >= 500:
                ContractPackage.objects.bulk_update(
                    packages_to_update,
                    fields=["effective_from"],
                    batch_size=500,
                )
                packages_to_update = []
                print(f"   📊 Processed {idx}/{total} rows...")

        if packages_to_update:
            ContractPackage.objects.bulk_update(
                packages_to_update,
                fields=["effective_from"],
                batch_size=500,
            )

        print(f"   ✅ Processed {total} rows")

        self.stdout.write(
            self.style.SUCCESS(
                f"""
Updated: {updated}
Not Found: {not_found}
Invalid Dates: {invalid_dates}
"""
            )
        )