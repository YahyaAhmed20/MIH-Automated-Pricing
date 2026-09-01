from django.core.management.base import BaseCommand

from imports.services.excel_provider import ExcelProvider
from imports.services.pricing_request_import_service import (
    PricingRequestImportService,
)


class Command(BaseCommand):

    help = "Import Pricing Requests from Sheet 12"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)",
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("   Pricing Requests Import")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="12",
            header=0,
            force_reload=True,
        )

        if dataframe.empty:
            self.stdout.write(
                self.style.WARNING("⚠️ Sheet 12 is empty.")
            )
            return

        self.stdout.write(
            f"📊 Importing {len(dataframe)} Pricing Requests..."
        )

        self.stdout.write(
            f"📋 Detected {len(dataframe.columns)} columns"
        )

        # ============================================================
        # Import
        # ============================================================

        result = PricingRequestImportService.import_data(
            dataframe
        )

        # ============================================================
        # Results
        # ============================================================

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("Pricing Requests Import Completed")
        self.stdout.write("=" * 60)

        self.stdout.write(
            f"Patients Created : {result['created_patients']}"
        )

        self.stdout.write(
            f"Requests Created : {result['created_requests']}"
        )

        self.stdout.write(
            f"Requests Updated : {result['updated_requests']}"
        )

        self.stdout.write(
            f"Requests Deleted : {result['deleted_requests']}"
        )

        self.stdout.write(
            f"Users Created    : {result['created_users']}"
        )

        self.stdout.write(
            f"Notes Created    : {result['created_notes']}"
        )

        self.stdout.write("=" * 60)