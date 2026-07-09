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
        self.stdout.write(
            "========== Company Exceptions Import =========="
        )

        # ✅ قراءة الشيت
        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="9",
            header=2,
        )

        # ✅ عرض الأعمدة للتأكد
        print("📋 أسماء الأعمدة:")
        print(dataframe.columns.tolist())
        print("=" * 50)

        # ✅ إعادة تسمية الأعمدة المهمة فقط
        dataframe = dataframe.rename(
            columns={
                "Unnamed: 0": "الجهه",
                "Unnamed: 1": "الفئه الماليه",
                "Unnamed: 2": "قائمة الاسعار",
                "معدل الخصم": "معدل الخصم_داخلي",
                "التفاصيل ": "التفاصيل_داخلي",
                "معدل الخصم.1": "معدل الخصم_خارجي",
                "التفاصيل وصافي السعر": "التفاصيل_خارجي",
                "Unnamed: 7": "سعر_الخدمة",
                "Unnamed: 29": "المرفقات",
            }
        )

        # ✅ حذف الصفوف الفارغة
        dataframe = dataframe[
            dataframe["الجهه"].notna()
        ]

        # ✅ إعادة تعيين الـ Index
        dataframe = dataframe.reset_index(drop=True)

        print(f"📊 عدد الصفوف: {len(dataframe)}")

        result = (
            CompanyExceptionImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            f"Processed : {result['processed']}"
        )

        self.stdout.write(
            f"Created   : {result['created']}"
        )

        self.stdout.write(
            f"Updated   : {result['updated']}"
        )

        self.stdout.write(
            f"Skipped   : {result['skipped']}"
        )

        self.stdout.write(
            "==========================================="
        )