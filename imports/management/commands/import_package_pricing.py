from django.core.management.base import BaseCommand

from imports.utils.excel_reader import ExcelReader

from imports.services.package_pricing_import_service import (
    PackagePricingImportService,
)


class Command(BaseCommand):

    help = "Import Package Pricing Sheet"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            type=str
        )

    def handle(
        self,
        *args,
        **options
    ):

        file_path = options["file_path"]

        dataframe = ExcelReader.read_sheet(
            file_path=file_path,
            sheet_name="DATA"
        )

        result = (
            PackagePricingImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                str(result)
            )
        )