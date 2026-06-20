from django.core.management.base import BaseCommand

from imports.utils.excel_reader import ExcelReader

from imports.services.pricing_request_import_service import (
    PricingRequestImportService,
)


class Command(BaseCommand):

    help = "Import Pricing Requests Sheet"

    def add_arguments(
        self,
        parser
    ):

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
            sheet_name="12"
        )

        result = (
            PricingRequestImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                str(result)
            )
        )