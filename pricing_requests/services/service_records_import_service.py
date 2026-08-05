# pricing_requests/services/service_records_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from pricing_requests.models import ServiceRecord
from imports.utils.import_helpers import ImportHelpers


class ServiceRecordsImportService:

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
        # ✅ Cache للـ Service Records
        # ============================================================
        records_cache = {}
        for r in ServiceRecord.objects.all():
            key = (
                ImportHelpers.normalize_text(r.account_number),
                ImportHelpers.normalize_text(r.service_code),
            )
            records_cache[key] = r

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        records_to_create = []
        records_to_update = []
        sheet_records = set()

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة (بدون Header)
        # ============================================================

        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ العمود 0: م (مفتاح) - لا نستخدمه
            # ✅ العمود 1: الرقم الحسابى
            account_number = ImportHelpers.normalize_text(
                row.get(1, "")
            )

            # ✅ العمود 9: الكود (service_code)
            service_code = ImportHelpers.normalize_text(
                row.get(9, "")
            )

            if not account_number or not service_code:
                result["skipped"] += 1
                continue

            result["processed"] += 1
            processed = result["processed"]

            # ✅ العمود 2: نوع المريض
            patient_type = ImportHelpers.normalize_text(
                row.get(2, "")
            )

            # ✅ العمود 3: اسم المريض
            patient_name = ImportHelpers.normalize_text(
                row.get(3, "")
            )

            # ✅ العمود 4: تاريخ الدخول
            admission_date = ImportHelpers.clean_date(
                row.get(4, None)
            )

            # ✅ العمود 5: تاريخ الخروج
            discharge_date = ImportHelpers.clean_date(
                row.get(5, None)
            )

            # ✅ العمود 6: مدة الاقامه
            stay_duration = ImportHelpers.normalize_text(
                row.get(6, "")
            )

            # ✅ العمود 7: اسم القسم
            department_name = ImportHelpers.normalize_text(
                row.get(7, "")
            )

            # ✅ العمود 8: اسم الخدمة
            service_name = ImportHelpers.normalize_text(
                row.get(8, "")
            )

            # ✅ العمود 10: التاريخ (service_date)
            service_date = ImportHelpers.clean_date(
                row.get(10, None)
            )

            # ✅ العمود 11: شركة التامين (insurance_company)
            insurance_company = ImportHelpers.normalize_text(
                row.get(11, "")
            )

            # ✅ العمود 12: الشركة الفرعية (sub_company)
            sub_company = ImportHelpers.normalize_text(
                row.get(12, "")
            )

            # ✅ العمود 13: المبلغ (amount)
            amount = ImportHelpers.clean_decimal(
                row.get(13, None)
            )
            if amount is None:
                amount = Decimal('0.00')

            # ✅ العمود 14: اجمالي الفاتورة (total_invoice)
            total_invoice = ImportHelpers.clean_decimal(
                row.get(14, None)
            )
            if total_invoice is None:
                total_invoice = Decimal('0.00')

            # ✅ البحث في Cache
            key = (account_number, service_code)
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