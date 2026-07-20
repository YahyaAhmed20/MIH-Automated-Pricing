# imports/management/commands/import_company_discount_rank.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.company_discount_rank_import_service import (
    CompanyDiscountRankImportService,
)


class Command(BaseCommand):

    help = "Import Company Discount Rank from Sheet 8"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Company Discount Rank Import ==========")

        # ✅ استخدم header=None (حسب الـ Pattern)
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="8",  # ✅ شيت 8
            header=None,     # ✅ مفيش Header
        )

        result = CompanyDiscountRankImportService.import_data(dataframe)

        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created              : {result['created']}")
        self.stdout.write(f"Updated              : {result['updated']}")
        self.stdout.write(f"Skipped              : {result['skipped']}")
        self.stdout.write("===========================================")