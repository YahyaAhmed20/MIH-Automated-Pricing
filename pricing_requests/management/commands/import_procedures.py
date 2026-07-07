from django.core.management.base import BaseCommand

import pandas as pd

from pricing_requests.services.procedure_import_service import (
    ProcedureImportService,
)

class Command(BaseCommand):

    help = "Import Procedures from Excel Sheet 13"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Procedures Import =========="
        )

        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="13",
        )

        dataframe.columns = (
            dataframe.columns
            .str.strip()
        )

        result = (
            ProcedureImportService.import_data(
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