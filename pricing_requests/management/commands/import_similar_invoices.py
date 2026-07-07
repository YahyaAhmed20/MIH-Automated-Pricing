from django.core.management.base import BaseCommand

import pandas as pd

from pricing_requests.services.similar_invoices_import_service import (
    SimilarInvoicesImportService,
)


class Command(BaseCommand):

    help = "Import Similar Invoices from Excel Sheet 10"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Similar Invoices Import =========="
        )

        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="10",
        )

        # تنظيف أسماء الأعمدة
        dataframe.columns = dataframe.columns.str.strip()

        dataframe.rename(
            columns={
                "التخصص\n": "التخصص",
                "اسم العمليه\n": "اسم العمليه",
                "الدور / المبني\n": "الدور / المبني",
                " صافي الفاتوره": "صافي الفاتوره",
                " المدفوعات": "المدفوعات",
            },
            inplace=True,
        )

        result = SimilarInvoicesImportService.import_data(
            dataframe
        )

        self.stdout.write(
            f"Processed : {result['processed']}"
        )

        self.stdout.write(
            f"Created   : {result['created']}"
        )

        self.stdout.write(
            f"Skipped   : {result['skipped']}"
        )

        self.stdout.write(
            "============================================"
        )