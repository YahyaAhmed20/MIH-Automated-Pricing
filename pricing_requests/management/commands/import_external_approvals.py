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

        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("   External Approvals Import")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="12",  # ✅ شيت 12
            header=None,      # ✅ مفيش Header
        )

        total_rows = len(dataframe) - 1  # ناقص الصف الأول (العناوين)

        # ✅ ✅ ✅ تأكيد الاستيراد (مع دعم --no-confirm)
        if options.get("no_confirm", False):
            # ✅ تخطي التأكيد تلقائياً (من الـ Update All)
            self.stdout.write(f"✅ Importing {total_rows} External Approvals records (auto-confirmed)")
        else:
            # ✅ طلب تأكيد من المستخدم (عند التشغيل اليدوي)
            confirm = input(f"Import {total_rows} records? (y/n): ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("Import cancelled."))
                return

        result = ExternalApprovalImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("External Approvals Import Completed")
        self.stdout.write("=" * 60)
        self.stdout.write(f"Processed : {result['processed']}")
        self.stdout.write(f"Created   : {result['created']}")
        self.stdout.write(f"Updated   : {result['updated']}")
        self.stdout.write(f"Skipped   : {result['skipped']}")
        if result["errors"]:
            self.stdout.write(self.style.ERROR(f"Errors    : {result['errors']}"))
        self.stdout.write("=" * 60)