from django.core.management.base import BaseCommand

from imports.utils.excel_reader import ExcelReader

from imports.services.package_catalog_import_service import (
    PackageCatalogImportService,
)


class Command(BaseCommand):

    help = "Import Package Catalog from Excel Sheet 1"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            type=str,
            help="Path to Excel file"
        )

    def handle(self, *args, **options):

        dataframe = ExcelReader.read_sheet(
            file_path=options["file_path"],
            sheet_name="1"
        )

        result = (
            PackageCatalogImportService.import_data(
                dataframe
            )
        )

        self.stdout.write("")

        self.stdout.write(
            self.style.SUCCESS(
                "========== Package Catalog Import =========="
            )
        )

        self.stdout.write(
            f"Processed            : {result['processed']}"
        )

        self.stdout.write(
            f"Created Packages     : {result['created']}"
        )

        self.stdout.write(
            f"Updated Packages     : {result['updated']}"
        )

        self.stdout.write(
            f"Created Specialties  : {result['created_specialties']}"
        )

        self.stdout.write(
            f"Missing Specialty    : {result['missing_specialty']}"
        )

        self.stdout.write(
            self.style.SUCCESS(
                "============================================"
            )
        )