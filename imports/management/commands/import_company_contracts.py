# imports/management/commands/import_company_contracts.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.company_contract_import_service import (
    CompanyContractImportService,
)


class Command(BaseCommand):

    help = "Import Company Contracts from Sheet 3"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Company Contracts Import ==========")

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="3",  # ✅ شيت 3
            header=None,     # ✅ مفيش Header
        )

        result = CompanyContractImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("==============================================")
        self.stdout.write(f"Processed                    : {result['processed']}")
        self.stdout.write(f"Created Entities             : {result['created_entities']}")
        self.stdout.write(f"Existing Entities            : {result['existing_entities']}")
        self.stdout.write(f"Created Financial Categories : {result['created_financial_categories']}")
        self.stdout.write(f"Existing Financial Categories: {result['existing_financial_categories']}")
        self.stdout.write(f"Created Price Lists          : {result['created_price_lists']}")
        self.stdout.write(f"Existing Price Lists         : {result['existing_price_lists']}")
        self.stdout.write(f"Created Contracts            : {result['created_contracts']}")
        self.stdout.write(f"Updated Contracts            : {result['updated_contracts']}")
        self.stdout.write(f"Skipped Incomplete Rows      : {result['skipped_incomplete_contracts']}")
        self.stdout.write("==============================================")