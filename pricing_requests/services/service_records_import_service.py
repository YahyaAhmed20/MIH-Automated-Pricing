from django.db import transaction

from pricing_requests.models import ServiceRecord

from imports.utils.import_helpers import ImportHelpers


class ServiceRecordsImportService:

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

            ServiceRecordsImportService.sync_row(
                row,
                result,
            )

        return result

    @staticmethod
    def sync_row(row, result):

        account_number = ImportHelpers.normalize_text(
            row.get("الرقم الحسابى")
        )

        service_code = ImportHelpers.normalize_text(
            row.get("الكود")
        )

        if not account_number or not service_code:
            result["skipped"] += 1
            return

        result["processed"] += 1

        patient_type = ImportHelpers.normalize_text(
            row.get("نوع المريض")
        )

        patient_name = ImportHelpers.normalize_text(
            row.get("اسم المريض")
        )

        admission_date = ImportHelpers.clean_date(
            row.get("تاريخ الدخول")
        )

        discharge_date = ImportHelpers.clean_date(
            row.get("تاريخ الخروج")
        )

        stay_duration = ImportHelpers.normalize_text(
            row.get("مدة الاقامه")
        )

        department_name = ImportHelpers.normalize_text(
            row.get("اسم القسم")
        )

        service_name = ImportHelpers.normalize_text(
            row.get("اسم الخدمة")
        )

        service_date = ImportHelpers.clean_date(
            row.get("التاريخ")
        )

        insurance_company = ImportHelpers.normalize_text(
            row.get("شركة التامين")
        )

        sub_company = ImportHelpers.normalize_text(
            row.get("الشركة الفرعية")
        )

        amount = ImportHelpers.clean_decimal(
            row.get("المبلغ")
        )

        defaults = {
            "patient_type": patient_type,
            "patient_name": patient_name,
            "admission_date": admission_date,
            "discharge_date": discharge_date,
            "stay_duration": stay_duration,
            "department_name": department_name,
            "service_name": service_name,
            "service_date": service_date,
            "insurance_company": insurance_company,
            "sub_company": sub_company,
            "amount": amount or 0,
        }

        _, created = ServiceRecord.objects.update_or_create(
            account_number=account_number,
            service_code=service_code,
            defaults=defaults,
        )

        if created:
            result["created"] += 1
        else:
            result["updated"] += 1