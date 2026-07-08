from django.db import transaction
import pandas as pd

from pricing_requests.models import ProcedureFee

from imports.utils.import_helpers import ImportHelpers


class ProcedureFeesImportService:

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
        current_discount = None

        for _, row in dataframe.iterrows():

            entity_name = ImportHelpers.normalize_text(
                row.get("الجهه")
            )

            financial_category = ImportHelpers.normalize_text(
                row.get("الفئه الماليه")
            )

            price_list = ImportHelpers.normalize_text(
                row.get("قائمة الاسعار")
            )

            category = ImportHelpers.normalize_text(
                row.get("التصنيف")
            )

            surgeon_raw = row.get("اتعاب")
            anesthesia_raw = row.get("اتعاب.1")
            assistant_raw = row.get("اتعاب.2")
            total_raw = row.get("اجمالي الاتعاب")
            discount_raw = row.get("معدل الخصم")

            surgeon_fee = ImportHelpers.clean_decimal(surgeon_raw)
            anesthesia_fee = ImportHelpers.clean_decimal(anesthesia_raw)
            assistant_fee = ImportHelpers.clean_decimal(assistant_raw)
            total_fee = ImportHelpers.clean_decimal(total_raw)

            # ✅ معدل الخصم كنص
            if pd.notna(discount_raw):
                discount_rate = str(discount_raw).strip()
            else:
                discount_rate = ""

            # ✅ ✅ ✅ إذا كان الصف يحتوي على معلومات جهة جديدة
            if entity_name:
                current_entity = entity_name
                current_financial = financial_category
                current_price_list = price_list
                current_discount = discount_rate  # ✅ نحفظ الخصم من الصف الرئيسي
                result["skipped"] += 1
                continue

            # ✅ إذا كان الصف يحتوي على تصنيف وأتعاب
            if category and current_entity:
                result["processed"] += 1

                # ✅ ✅ ✅ نستخدم current_discount (من الصف الرئيسي)
                obj, created = ProcedureFee.objects.update_or_create(
                    entity_name=current_entity,
                    financial_category=current_financial,
                    category=category,
                    defaults={
                        "price_list": current_price_list,
                        "surgeon_fee": surgeon_fee or 0,
                        "anesthesia_fee": anesthesia_fee or 0,
                        "assistant_fee": assistant_fee or 0,
                        "total_fee": total_fee or 0,
                        "discount_rate": current_discount,  # ✅ من الصف الرئيسي
                    }
                )

                if created:
                    result["created"] += 1
                else:
                    result["updated"] += 1

            else:
                if not category and not entity_name:
                    result["skipped"] += 1

        return result