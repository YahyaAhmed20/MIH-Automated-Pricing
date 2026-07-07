from django.db import transaction

from pricing_requests.models import SimilarInvoice

from imports.utils.import_helpers import ImportHelpers


class SimilarInvoicesImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        SimilarInvoice.objects.all().delete()

        records = []

        result = {
            "processed": 0,
            "created": 0,
            "skipped": 0,
        }

        for _, row in dataframe.iterrows():

            operation_name = ImportHelpers.normalize_text(
                row.get("اسم العمليه")
            )

            if not operation_name:
                result["skipped"] += 1
                continue

            # ✅ معالجة مدة الإقامة
            stay_duration_raw = ImportHelpers.clean_decimal(
                row.get("مدة الاقامه")
            )

            stay_duration = (
                str(int(stay_duration_raw))
                if stay_duration_raw is not None
                else ""
            )

            records.append(

                SimilarInvoice(

                    account_number=ImportHelpers.normalize_text(
                        row.get("الرقم الحسابي")
                    ),

                    medical_number=ImportHelpers.normalize_text(
                        row.get("الرقم الطبي")
                    ),

                    patient_name=ImportHelpers.normalize_text(
                        row.get("اسم المريض")
                    ),

                    admission_date=ImportHelpers.clean_date(
                        row.get("تاريخ الدخول")
                    ),

                    discharge_date=ImportHelpers.clean_date(
                        row.get("تاريخ الخروج")
                    ),

                    stay_duration=stay_duration,

                    specialty_name=ImportHelpers.normalize_text(
                        row.get("التخصص")
                    ),

                    doctor_name=ImportHelpers.normalize_text(
                        row.get("اسم الطبيب")
                    ),

                    operation_name=operation_name,

                    entity_name=ImportHelpers.normalize_text(
                        row.get("الجهه")
                    ),

                    sub_company=ImportHelpers.normalize_text(
                        row.get("الشركة الفرعية")
                    ),

                    building=ImportHelpers.normalize_text(
                        row.get("الدور / المبني")
                    ),

                    total_invoice=ImportHelpers.clean_decimal(
                        row.get("اجمالي الفاتوره")
                    ) or 0,

                    discount=ImportHelpers.clean_decimal(
                        row.get("الخصم")
                    ) or 0,

                    net_invoice=ImportHelpers.clean_decimal(
                        row.get("صافي الفاتوره")
                    ) or 0,

                    company_share=ImportHelpers.clean_decimal(
                        row.get("حصة الشركه")
                    ) or 0,

                    patient_share=ImportHelpers.clean_decimal(
                        row.get("حصة المريض")
                    ) or 0,

                    payments=ImportHelpers.clean_decimal(
                        row.get("المدفوعات")
                    ) or 0,

                    invoice_status=ImportHelpers.normalize_text(
                        row.get("حالة الفاتورة")
                    ),

                    invoice_closed_date=ImportHelpers.clean_date(
                        row.get("تاريخ انهاء الفاتوره")
                    ),

                    notes=ImportHelpers.normalize_text(
                        row.get("ملاحظات")
                    ),
                )
            )

            result["processed"] += 1

        SimilarInvoice.objects.bulk_create(
            records,
            batch_size=1000,
        )

        result["created"] = len(records)

        return result