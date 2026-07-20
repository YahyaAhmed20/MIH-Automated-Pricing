# imports/management/commands/import_report_statistics.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.report_statistic_import_service import (
    ReportStatisticImportService,
)


class Command(BaseCommand):

    help = "Import Report Statistics from Sheet 11"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("   Report Statistics Import")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="11",  # ✅ شيت 11
            header=None,      # ✅ مفيش Header
        )

        # ✅ ✅ ✅ تخطي التأكيد تلقائياً (للـ Update All)
        if not options.get("no_confirm", False):
            # لو اتسمى من الـ CLI من غير --no-confirm، اسأل
            total_rows = len(dataframe) - 1
            confirm = input(f"Import {total_rows} records? (y/n): ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("Import cancelled."))
                return
        else:
            # لو اتسمى بـ --no-confirm، تخطى
            total_rows = len(dataframe) - 1
            self.stdout.write(f"✅ Importing {total_rows} records (auto-confirmed)")

        result = ReportStatisticImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("Report Statistics Import Completed")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Processed : {result['processed']}")
        self.stdout.write(f"Created   : {result['created']}")
        self.stdout.write(f"Updated   : {result['updated']}")
        self.stdout.write(f"Skipped   : {result['skipped']}")
        if result["errors"]:
            self.stdout.write(self.style.ERROR(f"Errors    : {result['errors']}"))
        self.stdout.write("=" * 60)