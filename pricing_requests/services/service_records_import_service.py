# pricing_requests/services/service_records_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from pricing_requests.models import ServiceRecord
from imports.utils.import_helpers import ImportHelpers


class ServiceRecordsImportService:

    COLUMN_MAPPING = {
        "account_number": "الرقم الحسابى",
        "patient_type": "نوع المريض",
        "patient_name": "اسم المريض",
        "admission_date": "تاريخ الدخول",
        "discharge_date": "تاريخ الخروج",
        "stay_duration": "مدة الاقامة",
        "department_name": "اسم القسم",
        "service_name": "اسم الخدمة",
        "service_code": "الكود",
        "service_date": "التاريخ",
        "insurance_company": None,
        "sub_company": "الشركه الفرعيه",
        "amount": "المبلغ",
        "total_invoice": "صافي الفاتورة",
    }

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ DataFrame already contains the real Sheet headers
        # ============================================================
        if len(dataframe) == 0:
            return result

        dataframe = dataframe.copy()
        dataframe.columns = ImportHelpers.make_unique_headers(dataframe.columns)
        dataframe = dataframe.reset_index(drop=True)

        header_map = ImportHelpers.build_header_map(dataframe)

        # ============================================================
        # ✅ التحقق من الأعمدة المطلوبة (مع استبعاد الـ None)
        # ============================================================
        required_columns = [
            column
            for column in ServiceRecordsImportService.COLUMN_MAPPING.values()
            if column
        ]

        ImportHelpers.validate_required_columns(
            dataframe,
            required_columns,
        )

        print("✅ Sheet 6 headers mapped successfully")
        print("   Headers:", list(header_map.keys()))

        # ============================================================
        # ✅ Cache للـ Service Records
        # ============================================================
        records_cache = {}
        for r in ServiceRecord.objects.all():
            key = (
                ImportHelpers.normalize_text(r.account_number),
                ImportHelpers.normalize_text(r.service_code),
                r.service_date,
            )
            records_cache[key] = r

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        records_to_create = []
        records_to_update = []
        sheet_records = set()

        # ============================================================
        # ✅ Loop - استخدام أسماء الأعمدة
        # ============================================================

        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ قراءة البيانات باستخدام أسماء الأعمدة
            account_number = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "account_number",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            service_code = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "service_code",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            if not account_number or not service_code:
                result["skipped"] += 1
                continue

            result["processed"] += 1
            processed = result["processed"]

            patient_type = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "patient_type",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            patient_name = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "patient_name",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            admission_date = ImportHelpers.clean_date_mdy(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "admission_date",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                    default=None,
                )
            )

            discharge_date = ImportHelpers.clean_date_mdy(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "discharge_date",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                    default=None,
                )
            )

            stay_duration = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "stay_duration",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            department_name = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "department_name",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            service_name = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "service_name",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            service_date = ImportHelpers.clean_date_mdy(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "service_date",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                    default=None,
                )
            )

            insurance_company = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "insurance_company",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            sub_company = ImportHelpers.normalize_text(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "sub_company",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                )
            )

            amount = ImportHelpers.clean_decimal(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "amount",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                    default=None,
                )
            )
            if amount is None:
                amount = Decimal('0.00')

            total_invoice = ImportHelpers.clean_decimal(
                ImportHelpers.get_mapped_value(
                    row,
                    header_map,
                    "total_invoice",
                    ServiceRecordsImportService.COLUMN_MAPPING,
                    default=None,
                )
            )
            if total_invoice is None:
                total_invoice = Decimal('0.00')

            # ✅ البحث في Cache
            key = (
                account_number,
                service_code,
                service_date,
            )
            sheet_records.add(key)
            
            record = records_cache.get(key)

            if record:
                # ✅ تحديث البيانات
                changed = False
                
                if record.patient_type != patient_type:
                    record.patient_type = patient_type
                    changed = True
                    
                if record.patient_name != patient_name:
                    record.patient_name = patient_name
                    changed = True
                    
                if record.admission_date != admission_date:
                    record.admission_date = admission_date
                    changed = True
                    
                if record.discharge_date != discharge_date:
                    record.discharge_date = discharge_date
                    changed = True
                    
                if record.stay_duration != stay_duration:
                    record.stay_duration = stay_duration
                    changed = True
                    
                if record.department_name != department_name:
                    record.department_name = department_name
                    changed = True
                    
                if record.service_name != service_name:
                    record.service_name = service_name
                    changed = True
                    
                if record.service_date != service_date:
                    record.service_date = service_date
                    changed = True
                    
                if record.insurance_company != insurance_company:
                    record.insurance_company = insurance_company
                    changed = True
                    
                if record.sub_company != sub_company:
                    record.sub_company = sub_company
                    changed = True
                    
                if record.amount != amount:
                    record.amount = amount
                    changed = True

                if record.total_invoice != total_invoice:
                    record.total_invoice = total_invoice
                    changed = True

                if changed:
                    records_to_update.append(record)
                    result["updated"] += 1

            else:
                # ✅ إنشاء جديد
                record = ServiceRecord(
                    account_number=account_number,
                    service_code=service_code,
                    patient_type=patient_type,
                    patient_name=patient_name,
                    admission_date=admission_date,
                    discharge_date=discharge_date,
                    stay_duration=stay_duration,
                    department_name=department_name,
                    service_name=service_name,
                    service_date=service_date,
                    insurance_company=insurance_company,
                    sub_company=sub_company,
                    amount=amount,
                    total_invoice=total_invoice,
                )
                records_to_create.append(record)
                records_cache[key] = record
                result["created"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================

        print(f"💾 Creating {len(records_to_create)} records...")
        print(f"💾 Updating {len(records_to_update)} records...")

        BATCH_SIZE = 500

        if records_to_create:
            ServiceRecord.objects.bulk_create(records_to_create, batch_size=BATCH_SIZE)

        if records_to_update:
            total_updated = 0
            for i in range(0, len(records_to_update), BATCH_SIZE):
                batch = records_to_update[i:i+BATCH_SIZE]
                ServiceRecord.objects.bulk_update(
                    batch,
                    fields=[
                        "patient_type",
                        "patient_name",
                        "admission_date",
                        "discharge_date",
                        "stay_duration",
                        "department_name",
                        "service_name",
                        "service_date",
                        "insurance_company",
                        "sub_company",
                        "amount",
                        "total_invoice",
                    ],
                    batch_size=100,
                )
                total_updated += len(batch)
                print(f"   ✅ Updated batch {i//BATCH_SIZE + 1} ({total_updated}/{len(records_to_update)})")

        # ============================================================
        # ✅ Reload Cache بعد الـ Bulk Operations
        # ============================================================
        records_cache = {}
        for r in ServiceRecord.objects.all():
            key = (
                ImportHelpers.normalize_text(r.account_number),
                ImportHelpers.normalize_text(r.service_code),
                r.service_date,
            )
            records_cache[key] = r

        # ============================================================
        # ✅ Delete Records not موجودة في الشيت
        # ============================================================
        records_to_delete = []

        for key, record in records_cache.items():
            if key not in sheet_records:
                records_to_delete.append(record.id)

        if records_to_delete:
            deleted, _ = ServiceRecord.objects.filter(
                id__in=records_to_delete
            ).delete()

            result["deleted"] = deleted
            print(f"🗑️ Deleted {deleted} records")

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result