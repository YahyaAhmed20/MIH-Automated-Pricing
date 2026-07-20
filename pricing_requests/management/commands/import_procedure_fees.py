# pricing_requests/management/commands/import_procedure_fees.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from pricing_requests.services.procedure_fees_import_service import (
    ProcedureFeesImportService,
)


class Command(BaseCommand):

    help = "Import Procedure Fees from Sheet 14"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Procedure Fees Import ==========")

        # ✅ استخدم header=None (حسب الـ Pattern)
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="14",  # ✅ شيت 14
            header=None,      # ✅ مفيش Header
        )

        result = ProcedureFeesImportService.import_data(dataframe)

        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created              : {result['created']}")
        self.stdout.write(f"Updated              : {result['updated']}")
        self.stdout.write(f"Skipped              : {result['skipped']}")
        self.stdout.write("===========================================")