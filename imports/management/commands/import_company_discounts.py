# imports/management/commands/import_company_discounts.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.company_discount_import_service import (
    CompanyDiscountImportService,
)


class Command(BaseCommand):

    help = "Import Company Discounts from Sheet 4"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Company Discounts Import ==========")

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="4",  # ✅ شيت 4
            header=None,     # ✅ مفيش Header
        )

        result = CompanyDiscountImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("==============================================")
        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created Profiles     : {result['created_profiles']}")
        self.stdout.write(f"Updated Profiles     : {result['updated_profiles']}")
        self.stdout.write(f"Created Discounts    : {result['created_discounts']}")
        self.stdout.write("==============================================")