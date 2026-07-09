from django.db import transaction
import pandas as pd

from pricing_requests.models import CompanyDiscountRank

from imports.utils.import_helpers import ImportHelpers


class CompanyDiscountRankImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

        for _, row in dataframe.iterrows():

            # ✅ قراءة البيانات (باستخدام أسماء الأعمدة الجديدة)
            company_name = ImportHelpers.normalize_text(
                row.get("company_name")
            )

            if not company_name:
                result["skipped"] += 1
                continue

            financial_category = ImportHelpers.normalize_text(
                row.get("financial_category")
            )

            price_list = ImportHelpers.normalize_text(
                row.get("price_list")
            )

            # ✅ قراءة الخصومات (بالفعل تم تحويلها في الـ Command)
            internal_raw = row.get("internal_discount")
            external_raw = row.get("external_discount")

            # ✅ تنظيف الخصومات (تحويل 0.65 إلى 65.0)
            if pd.notna(internal_raw):
                try:
                    internal_discount = float(internal_raw) * 100
                except:
                    internal_discount = 0
            else:
                internal_discount = 0

            if pd.notna(external_raw):
                try:
                    external_discount = float(external_raw) * 100
                except:
                    external_discount = 0
            else:
                external_discount = 0

            attachment = ImportHelpers.normalize_text(
                row.get("attachment")
            )

            # ✅ تحديث أو إنشاء
            obj, created = CompanyDiscountRank.objects.update_or_create(
                company_name=company_name,
                defaults={
                    "financial_category": financial_category,
                    "price_list": price_list,
                    "internal_discount": internal_discount,
                    "external_discount": external_discount,
                    "attachment": attachment,
                }
            )

            if created:
                result["created"] += 1
            else:
                result["updated"] += 1

            result["processed"] += 1

        return result