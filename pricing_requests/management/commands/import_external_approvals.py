# imports/management/commands/import_external_approvals.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.external_approval_import_service import (
    ExternalApprovalImportService,
)


class Command(BaseCommand):

    help = "Import External Approvals from Sheet 12"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== External Approvals Import ==========")

        # ✅ استخدم header=None مع force_reload=True
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="12",  # ✅ شيت 12
            header=None,      # ✅ مفيش Header
            force_reload=True,
        )

        result = ExternalApprovalImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("===========================================")
        self.stdout.write(f"Processed : {result['processed']}")
        self.stdout.write(f"Created   : {result['created']}")
        self.stdout.write(f"Updated   : {result['updated']}")
        self.stdout.write(f"Deleted   : {result.get('deleted', 0)}")
        self.stdout.write(f"Skipped   : {result['skipped']}")
        self.stdout.write("===========================================")