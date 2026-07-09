from django.db import transaction
import pandas as pd

from pricing_requests.models import CompanyException

from imports.utils.import_helpers import ImportHelpers


class CompanyExceptionImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

        # ✅ متغيرات لتخزين بيانات الجهة الحالية
        current_entity = None
        current_financial = None
        current_price_list = None
        current_internal_discount = None
        current_internal_details = None
        current_external_discount = None
        current_external_details = None
        current_attachment = None

        for _, row in dataframe.iterrows():

            # ✅ قراءة البيانات
            entity_name = ImportHelpers.normalize_text(
                row.get("الجهه")
            )

            financial_category = ImportHelpers.normalize_text(
                row.get("الفئه الماليه")
            )

            price_list = ImportHelpers.normalize_text(
                row.get("قائمة الاسعار")
            )

            # ✅ قراءة الخصومات الداخلية
            internal_discount_raw = row.get("معدل الخصم")
            internal_details_raw = row.get("التفاصيل")

            # ✅ قراءة الخصومات الخارجية
            external_discount_raw = row.get("معدل الخصم.1")
            external_details_raw = row.get("التفاصيل.1")

            attachment = ImportHelpers.normalize_text(
                row.get("صورة العقد")
            )

            # ✅ تنظيف الخصومات
            if pd.notna(internal_discount_raw):
                try:
                    internal_discount = float(internal_discount_raw) * 100
                except:
                    internal_discount = 0
            else:
                internal_discount = 0

            if pd.notna(external_discount_raw):
                try:
                    external_discount = float(external_discount_raw) * 100
                except:
                    external_discount = 0
            else:
                external_discount = 0

            # ✅ تنظيف التفاصيل
            internal_details = ImportHelpers.normalize_text(internal_details_raw) if pd.notna(internal_details_raw) else ""
            external_details = ImportHelpers.normalize_text(external_details_raw) if pd.notna(external_details_raw) else ""

            # ✅ إذا كان الصف يحتوي على جهة جديدة
            if entity_name:
                current_entity = entity_name
                current_financial = financial_category
                current_price_list = price_list
                current_internal_discount = internal_discount
                current_internal_details = internal_details
                current_external_discount = external_discount
                current_external_details = external_details
                current_attachment = attachment

                result["processed"] += 1

                obj, created = CompanyException.objects.update_or_create(
                    entity_name=current_entity,
                    defaults={
                        "financial_category": current_financial,
                        "price_list": current_price_list,
                        "internal_discount": current_internal_discount,
                        "internal_details": current_internal_details,
                        "external_discount": current_external_discount,
                        "external_details": current_external_details,
                        "attachment": current_attachment,
                    }
                )

                if created:
                    result["created"] += 1
                else:
                    result["updated"] += 1

            # ✅ إذا كان الصف يحتوي على تفاصيل إضافية لنفس الجهة
            elif current_entity:
                # ✅ تحديث التفاصيل إذا كانت موجودة
                if internal_details or external_details:
                    result["processed"] += 1

                    # ✅ تجميع التفاصيل معاً
                    if internal_details:
                        current_internal_details = current_internal_details + "\n" + internal_details if current_internal_details else internal_details

                    if external_details:
                        current_external_details = current_external_details + "\n" + external_details if current_external_details else external_details

                    obj, created = CompanyException.objects.update_or_create(
                        entity_name=current_entity,
                        defaults={
                            "financial_category": current_financial,
                            "price_list": current_price_list,
                            "internal_discount": current_internal_discount,
                            "internal_details": current_internal_details,
                            "external_discount": current_external_discount,
                            "external_details": current_external_details,
                            "attachment": current_attachment,
                        }
                    )

                    if created:
                        result["created"] += 1
                    else:
                        result["updated"] += 1

        return result