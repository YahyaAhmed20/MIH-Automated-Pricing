# pricing_requests/management/commands/import_report_statistics.py

from django.core.management.base import BaseCommand
import pandas as pd

from imports.services.report_statistic_import_service import (
    ReportStatisticImportService,
)


class Command(BaseCommand):

    help = "Import Report Statistics from Excel Sheet 11"

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
        self.stdout.write("   📊 Report Statistics Import (Sheet 11)")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        # ✅ قراءة الشيت 11
        try:
            df = pd.read_excel(
                options["excel_file"],
                sheet_name="11",
                header=None,
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ خطأ في قراءة الملف: {e}"))
            return

        print(f"📊 عدد الصفوف: {len(df)}")
        print(f"📊 عدد الأعمدة: {len(df.columns)}")
        print("")

        # ✅ عرض أول 5 صفوف للتأكد (للـ debug)
        print("📋 أول 5 صفوف:")
        print(df.head(5).to_string())
        print("")
        print("=" * 60)

        # ✅ تأكيد الاستيراد (لو مش مستخدم --no-confirm)
        if not options["no_confirm"]:
            confirm = input("⚠️  هل تريد استيراد البيانات؟ (y/n): ")
            if confirm.lower() != "y":
                self.stdout.write(self.style.WARNING("❌ تم إلغاء الاستيراد"))
                return

        print("")
        print("🔄 جاري الاستيراد...")
        print("")

        # ✅ تشغيل الاستيراد
        result = ReportStatisticImportService.import_data(df)

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