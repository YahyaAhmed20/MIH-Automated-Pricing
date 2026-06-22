from django.core.management.base import BaseCommand

from imports.utils.excel_reader import ExcelReader

from imports.services.package_price_metadata_import_service import (
    PackagePriceMetadataImportService
)


class Command(BaseCommand):

    help = "Import Package Metadata"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            type=str
        )

    def handle(self, *args, **options):

        dataframe = ExcelReader.read_sheet(
            file_path=options["file_path"],
            sheet_name="package price"
        )

        result = (
            PackagePriceMetadataImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                str(result)
            )
        )