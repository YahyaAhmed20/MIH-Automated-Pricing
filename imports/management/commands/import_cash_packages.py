# imports/management/commands/import_cash_packages.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.cash_package_import_service import (
    CashPackageImportService,
)


class Command(BaseCommand):

    help = "Import Cash Packages from Sheet 2"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Cash Packages Import ==========")

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="2",  # ✅ شيت 2
            header=None,     # ✅ مفيش Header
        )

        result = CashPackageImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("==========================================")
        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created Packages     : {result['created']}")
        self.stdout.write(f"Updated Packages     : {result['updated']}")
        self.stdout.write(f"Created Specialties  : {result['created_specialties']}")
        self.stdout.write(f"Missing Specialty    : {result['missing_specialty']}")
        self.stdout.write("==========================================")