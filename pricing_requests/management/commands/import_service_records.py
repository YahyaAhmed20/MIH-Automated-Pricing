from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from pricing_requests.services.service_records_import_service import (
    ServiceRecordsImportService,
)


class Command(BaseCommand):

    help = "Import Service Records from Sheet 6"

    def add_arguments(self, parser):
        parser.add_argument(
            "excel_file",
            nargs="?",
            default=None,
            help="Path to APP.xlsx (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Service Records Import =========="
        )

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["excel_file"],
            sheet_name="6",
            header=None,  # ✅ مفيش Header
        )

        result = ServiceRecordsImportService.import_data(dataframe)

        self.stdout.write(
            f"Processed : {result['processed']}"
        )
        self.stdout.write(
            f"Created   : {result['created']}"
        )
        self.stdout.write(
            f"Updated   : {result['updated']}"
        )
        self.stdout.write(
            f"Skipped   : {result['skipped']}"
        )
        self.stdout.write(
            "==========================================="
        )