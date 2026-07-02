from django.core.management.base import BaseCommand

import pandas as pd

from imports.services.company_discount_import_service import (
    CompanyDiscountImportService,
)


class Command(BaseCommand):

    help = "Import Company Discounts"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Company Discounts Import =========="
        )

        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="4",
        )

        dataframe.columns = (
            dataframe.columns.str.strip()
        )

        result = (
            CompanyDiscountImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            f"Processed            : {result['processed']}"
        )

        self.stdout.write(
            f"Created Profiles     : {result['created_profiles']}"
        )

        self.stdout.write(
            f"Updated Profiles     : {result['updated_profiles']}"
        )

        self.stdout.write(
            f"Created Discounts    : {result['created_discounts']}"
        )

        self.stdout.write(
            "=============================================="
        )