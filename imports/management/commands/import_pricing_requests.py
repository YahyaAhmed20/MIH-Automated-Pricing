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

        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt",
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
        )

        total_rows = len(dataframe)

        if options.get("no_confirm", False):

            self.stdout.write(
                f"✅ Importing {total_rows} Pricing Requests (auto-confirmed)"
            )

        else:

            confirm = input(
                f"Import {total_rows} Pricing Requests? (y/n): "
            )

            if confirm.lower() != "y":

                self.stdout.write(
                    self.style.WARNING("Import cancelled.")
                )

                return

        result = PricingRequestImportService.import_data(
            dataframe
        )

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
            f"Users Created    : {result['created_users']}"
        )

        self.stdout.write(
            f"Notes Created    : {result['created_notes']}"
        )

        self.stdout.write("=" * 60)