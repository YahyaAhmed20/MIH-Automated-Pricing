from django.core.management.base import BaseCommand

import pandas as pd

from imports.services.company_contract_import_service import (
    CompanyContractImportService,
)


class Command(BaseCommand):

    help = "Import Company Contracts from Excel Sheet 3"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Company Contracts Import ==========")

        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="3",
        )

        dataframe.columns = (
            dataframe.columns
            .str.strip()
        )

        result = (
            CompanyContractImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            f"Processed                    : {result['processed']}"
        )

        self.stdout.write(
            f"Created Entities             : {result['created_entities']}"
        )

        self.stdout.write(
            f"Existing Entities            : {result['existing_entities']}"
        )

        self.stdout.write(
            f"Created Financial Categories : {result['created_financial_categories']}"
        )

        self.stdout.write(
            f"Existing Financial Categories: {result['existing_financial_categories']}"
        )

        self.stdout.write(
            f"Created Price Lists          : {result['created_price_lists']}"
        )

        self.stdout.write(
            f"Existing Price Lists         : {result['existing_price_lists']}"
        )

        self.stdout.write(
            f"Created Contracts            : {result['created_contracts']}"
        )

        self.stdout.write(
            f"Updated Contracts            : {result['updated_contracts']}"
        )

        self.stdout.write(
            f"Skipped Incomplete Rows      : {result['skipped_incomplete_contracts']}"
        )

        self.stdout.write("==============================================")