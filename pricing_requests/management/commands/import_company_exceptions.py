# imports/management/commands/import_company_exceptions.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.company_exception_import_service import (
    CompanyExceptionImportService,
)


class Command(BaseCommand):

    help = "Import Company Exceptions from Sheet 9"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Company Exceptions Import ==========")

        # ✅ استخدم header=None (حسب الـ Pattern)
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="9",  # ✅ شيت 9
            header=None,     # ✅ مفيش Header
        )

        result = CompanyExceptionImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("===========================================")
        self.stdout.write(f"Processed : {result['processed']}")
        self.stdout.write(f"Profiles  : {result['profiles']}")
        self.stdout.write(f"Items     : {result['items']}")
        self.stdout.write(f"Updated   : {result['updated']}")
        self.stdout.write(f"Skipped   : {result['skipped']}")
        self.stdout.write("===========================================")