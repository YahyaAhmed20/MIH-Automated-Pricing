# pricing_requests/management/commands/import_external_approvals.py

from django.core.management.base import BaseCommand
import pandas as pd

from imports.services.external_approval_import_service import (
    ExternalApprovalImportService,
)


class Command(BaseCommand):

    help = "Import External Approvals from Excel Sheet 12"

    def add_arguments(self, parser):
        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )
        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt"
        )

    def handle(self, *args, **options):
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("   📊 External Approvals Import (Sheet 12)")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        try:
            df = pd.read_excel(
                options["excel_file"],
                sheet_name="12",
                header=None,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ خطأ في قراءة الملف: {e}"))
            return

        print(f"📊 عدد الصفوف: {len(df)}")
        print(f"📊 عدد الأعمدة: {len(df.columns)}")
        print("")

        print("📋 أول 5 صفوف:")
        print(df.head(5).to_string())
        print("")
        print("=" * 60)

        if not options["no_confirm"]:
            confirm = input("⚠️  هل تريد استيراد البيانات؟ (y/n): ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("❌ تم إلغاء الاستيراد"))
                return

        print("")
        print("🔄 جاري الاستيراد...")
        print("")

        result = ExternalApprovalImportService.import_data(df)

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("✅ انتهى الاستيراد!")
        self.stdout.write(f"   📊 تمت المعالجة: {result['processed']}")
        self.stdout.write(f"   ✅ تم الإنشاء: {result['created']}")
        self.stdout.write(f"   🔄 تم التحديث: {result['updated']}")
        self.stdout.write(f"   ⏭️ تم التخطي: {result['skipped']}")
        if result["errors"] > 0:
            self.stdout.write(self.style.ERROR(f"   ❌ الأخطاء: {result['errors']}"))
        self.stdout.write("=" * 60)