from django.core.management.base import BaseCommand

import pandas as pd

from imports.services.company_discount_rank_import_service import (
    CompanyDiscountRankImportService,
)


class Command(BaseCommand):

    help = "Import Company Discount Rank from Excel Sheet 8"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Company Discount Rank Import =========="
        )

        # ✅ قراءة الشيت من الصف 3 (index 2)
        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="8",
            header=2,
        )

        # ✅ إعادة تسمية الأعمدة
        dataframe = dataframe.rename(
            columns={
                "Unnamed: 0": "company_name",
                "Unnamed: 1": "financial_category",
                "Unnamed: 2": "price_list",
                "معدل الخصم": "internal_discount",     # ✅ الخصم الداخلي
                "معدل الخصم.1": "external_discount",   # ✅ الخصم الخارجي
                "Unnamed: 6": "attachment",
            }
        )

        # ✅ حذف الصفوف الفارغة
        dataframe = dataframe[
            dataframe["company_name"].notna()
        ]

        # ✅ إعادة تعيين الـ Index
        dataframe = dataframe.reset_index(drop=True)

        

        result = (
            CompanyDiscountRankImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            f"Processed : {result['processed']}"
        )

        self.stdout.write(
            f"Created   : {result['created']}"
        )

        self.stdout.write(
            f"Updated   : {result['updated']}"
        )

        self.stdout.write(
            f"Skipped   : {result['skipped']}"
        )

        self.stdout.write(
            "==========================================="
        )