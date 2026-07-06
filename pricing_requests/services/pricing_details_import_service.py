from django.db import transaction

from pricing_requests.models import PricingDetail

from imports.utils.import_helpers import ImportHelpers


class PricingDetailsImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        # بما إن مفيش مفتاح فريد
        # هنعتبر الشيت هو المصدر الوحيد للحقيقة
        PricingDetail.objects.all().delete()

        records = []

        result = {
            "processed": 0,
            "created": 0,
            "skipped": 0,
        }

        for _, row in dataframe.iterrows():

            patient_name = ImportHelpers.normalize_text(
                row.get("الاسم")
            )

            if not patient_name:
                result["skipped"] += 1
                continue

            records.append(

                PricingDetail(

                    pricing_date=ImportHelpers.clean_date(
                        row.get("تاريخ التسعير")
                    ),

                    group_name=ImportHelpers.normalize_text(
                        row.get("الجروب")
                    ),

                    patient_name=patient_name,

                    company_name=ImportHelpers.normalize_text(
                        row.get("الشركة")
                    ),

                    doctor_name=ImportHelpers.normalize_text(
                        row.get("اسم الطبيب")
                    ),

                    report_name=ImportHelpers.normalize_text(
                        row.get("التقرير")
                    ),

                    procedure_name=ImportHelpers.normalize_text(
                        row.get("الاجراء")
                    ),

                    specialty_name=ImportHelpers.normalize_text(
                        row.get("التخصص")
                    ),

                    pricing_type=ImportHelpers.normalize_text(
                        row.get("نوع التسعير")
                    ),

                    card_number=ImportHelpers.normalize_text(
                        row.get("رقم الكارنية")
                    ),

                    accountant_name=ImportHelpers.normalize_text(
                        row.get("اسم المحاسب")
                    ),

                    cost_notes=ImportHelpers.normalize_text(
                        row.get("ملاحظات خاصة بالتكلفة")
                    ),

                    cost=ImportHelpers.clean_decimal(
                        row.get("التكلفه")
                    ) or 0,

                    details=ImportHelpers.normalize_text(
                        row.get("التفاصيل")
                    ),

                )

            )

            result["processed"] += 1

        PricingDetail.objects.bulk_create(
            records,
            batch_size=500,
        )

        result["created"] = len(records)

        return result