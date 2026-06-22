from django.core.management.base import BaseCommand
import pandas as pd
from medical_catalog.models import Package


class Command(BaseCommand):

    help = "Import Package Notes"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            type=str
        )

    def handle(self, *args, **options):

        df = pd.read_excel(
            options["file_path"],
            sheet_name="DATA"
        )

        updated = 0

        for i in range(len(df) - 1):

            code = str(df.iloc[i].get("الكود", "")).strip()

            if not code or code == "nan":
                continue

            next_row = df.iloc[i + 1]

            if str(next_row.get("الباكدجات", "")).strip() != "ملاحظات الباكدج":
                continue

            note = None

            for col in df.columns:
                value = next_row.get(col)

                if pd.isna(value):
                    continue

                text = str(value).strip()

                # ✅ استبعاد القيم غير المرغوب فيها
                if text in ["", "0", "nan", "NaN", "None"]:
                    continue

                if col != "الباكدجات":
                    note = text
                    break

            if not note:
                continue

            package = Package.objects.filter(code=code).first()

            if not package:
                continue

            package.package_note = note
            package.save(update_fields=["package_note"])

            updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"✅ Updated Packages: {updated}")
        )