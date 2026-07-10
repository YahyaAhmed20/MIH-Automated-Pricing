# pricing_requests/management/commands/import_company_exceptions.py

from django.core.management.base import BaseCommand
import pandas as pd

from imports.services.company_exception_import_service import (
    CompanyExceptionImportService,
)


class Command(BaseCommand):

    help = "Import Company Exceptions from Excel Sheet 9"

    def add_arguments(self, parser):
        parser.add_argument(
            "excel_file",
            type=str,
            help="Path to APP.xlsx"
        )

    def handle(self, *args, **options):
        self.stdout.write("")
        self.stdout.write("========== Company Exceptions Import ==========")

        # ✅ قراءة الشيت بدون header
        df = pd.read_excel(
            options["excel_file"],
            sheet_name="9",
            header=None,
        )

        print(f"📊 عدد الصفوف: {len(df)}")
        print(f"📊 عدد الأعمدة: {len(df.columns)}")

        # ✅ نبدأ من الصف 3 (أول جهة)
        df_data = df.iloc[3:].copy()
        df_data = df_data.reset_index(drop=True)

        # ✅ حذف الصفوف الفارغة تماماً
        df_data = df_data.dropna(how='all')

        print(f"\n📊 عدد الصفوف بعد التنظيف: {len(df_data)}")

        # ✅ عرض البيانات للتأكد
        print("\n📋 البيانات بعد التنظيف (أول 5 صفوف):")
        print(df_data.head(5).iloc[:, 0:10].to_string())

        # ✅ تشغيل الاستيراد
        result = CompanyExceptionImportService.import_data(df_data)

        self.stdout.write("")
        self.stdout.write("===========================================")
        self.stdout.write(f"✅ Processed : {result['processed']}")
        self.stdout.write(f"✅ Profiles  : {result['profiles']}")
        self.stdout.write(f"✅ Items     : {result['items']}")
        self.stdout.write(f"⏭️ Skipped   : {result['skipped']}")
        self.stdout.write("===========================================")