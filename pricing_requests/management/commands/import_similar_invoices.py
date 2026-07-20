# pricing_requests/management/commands/import_similar_invoices.py

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
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Similar Invoices Import ==========")

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="10",  # ✅ شيت 10
            header=None,      # ✅ مفيش Header
        )

        result = SimilarInvoicesImportService.import_data(dataframe)

        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created              : {result['created']}")
        self.stdout.write(f"Updated              : {result['updated']}")
        self.stdout.write(f"Skipped              : {result['skipped']}")
        self.stdout.write("============================================")