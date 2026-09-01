# imports/management/commands/import_report_statistics_sheet15.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.report_statistic_sheet15_import_service import (
    ReportStatisticSheet15ImportService,
)


class Command(BaseCommand):

    help = "Import Report Statistics from Sheet 15"

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
        self.stdout.write("   Report Statistics Sheet 15 Import")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        # ✅ استخدام Header الصف الأول لتحديد الأعمدة بالاسم
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="15",
            header=0,
            force_reload=True,
        )

        # ✅ عدد صفوف البيانات الفعلية بعد استبعاد الـ Header
        total_rows = len(dataframe)

        if not options.get("no_confirm", False):
            confirm = input(f"Import {total_rows} records? (y/n): ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("Import cancelled."))
                return
        else:
            self.stdout.write(f"✅ Importing {total_rows} records (auto-confirmed)")

        result = ReportStatisticSheet15ImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("Sheet 15 Import Completed")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Processed : {result['processed']}")
        self.stdout.write(f"Created   : {result['created']}")
        self.stdout.write(f"Updated   : {result['updated']}")
        self.stdout.write(f"Deleted   : {result['deleted']}")  # ✅ إضافة deleted
        self.stdout.write(f"Skipped   : {result['skipped']}")
        if result["errors"]:
            self.stdout.write(self.style.ERROR(f"Errors    : {result['errors']}"))
        self.stdout.write("=" * 60)