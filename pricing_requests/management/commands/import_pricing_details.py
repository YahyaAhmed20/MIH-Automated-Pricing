from django.core.management.base import BaseCommand

import pandas as pd

from pricing_requests.services.pricing_details_import_service import PricingDetailsImportService



class Command(BaseCommand):

    help = "Import Pricing Details from Excel Sheet 7"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Pricing Details Import =========="
        )

        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="7",
        )

        dataframe.columns = (
            dataframe.columns
            .str.strip()
        )

        result = (
            PricingDetailsImportService.import_data(dataframe)
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
            "==========================================="
        )