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
        parser.add_argument(
            "--company",
            type=str,
            default=None,
            help="Import one company only",
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Company Discounts Import ==========")

        if options.get("company"):
            self.stdout.write(f"🎯 Filtering for company: {options['company']}")

        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="4",
            header=None,
            force_reload=True,
        )

        result = CompanyDiscountImportService.import_data(
            dataframe,
            company=options.get("company"),
        )

        self.stdout.write("")
        self.stdout.write("==============================================")
        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created Profiles     : {result['created_profiles']}")
        self.stdout.write(f"Updated Profiles     : {result['updated_profiles']}")
        self.stdout.write(f"Created Discounts    : {result['created_discounts']}")
        self.stdout.write(f"Deleted Profiles    : {result.get('deleted_profiles', 0)}")
        self.stdout.write(f"Deleted Discounts   : {result.get('deleted_discounts', 0)}")
        self.stdout.write("==============================================")