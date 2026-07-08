from django.core.management.base import BaseCommand

import pandas as pd

from pricing_requests.services.procedure_fees_import_service import (
    ProcedureFeesImportService,
)

class Command(BaseCommand):

    help = "Import Procedure Fees from Excel Sheet 14"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Procedure Fees Import =========="
        )

        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="14",
        )

        dataframe.columns = (
            dataframe.columns
            .str.strip()
        )

        result = (
            ProcedureFeesImportService.import_data(
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