from django.core.management.base import BaseCommand

from imports.services.excel_provider import ExcelProvider
from pricing_requests.services.similar_invoices_import_service import (
    SimilarInvoicesImportService,
)


class Command(BaseCommand):

    help = "Import Similar Invoices from Sheet 10"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)",
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write(
            "========== Similar Invoices Import =========="
        )

        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="10",
            header=0,
            force_reload=True,
        )

        result = SimilarInvoicesImportService.import_data(
            dataframe
        )

        self.stdout.write("")
        self.stdout.write(
            "==========================================="
        )
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
            f"Deleted   : {result.get('deleted', 0)}"
        )
        self.stdout.write(
            f"Skipped   : {result['skipped']}"
        )
        self.stdout.write(
            "==========================================="
        )