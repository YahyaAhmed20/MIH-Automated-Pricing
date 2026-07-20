# imports/management/commands/import_package_catalog.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.package_catalog_import_service import (
    PackageCatalogImportService,
)


class Command(BaseCommand):

    help = "Import Package Catalog from Sheet 1"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Package Catalog Import ==========")

        # ✅ استخدم header=None (حسب الـ Pattern)
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="1",  # ✅ شيت 1
            header=None,     # ✅ مفيش Header
        )

        result = PackageCatalogImportService.import_data(dataframe)

        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created Packages     : {result['created']}")
        self.stdout.write(f"Updated Packages     : {result['updated']}")
        self.stdout.write(f"Created Specialties  : {result['created_specialties']}")
        self.stdout.write(f"Missing Specialty    : {result['missing_specialty']}")
        self.stdout.write("============================================")