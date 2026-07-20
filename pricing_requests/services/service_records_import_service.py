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
        print("⏳ Starting Service Records import...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ Cache للـ Service Records
        # ============================================================
        print("⏳ Loading existing service records...")
        records_cache = {}
        for r in ServiceRecord.objects.all():
            key = (
                ImportHelpers.normalize_text(r.account_number),
                ImportHelpers.normalize_text(r.service_code),
            )
            records_cache[key] = r
        print(f"   ✅ {len(records_cache)} records loaded")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        records_to_create = []
        records_to_update = []

        # ============================================================
        # ✅ متغير لتتبع التغييرات (للتحليل)
        # ============================================================
        change_log = []

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة (بدون Header)
        # ============================================================

        print("⏳ Processing rows...")
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

            # ✅ Debugging للسجل 4250/3794997
            if account_number == "4250" and service_code == "3794997":
                print("=" * 60)
                print("🔍 DEBUG - Found target record:")
                print(f"   account_number: {account_number}")
                print(f"   service_code: {service_code}")
                print(f"   patient_name: {patient_name}")
                print(f"   service_date (col 10): {service_date}")
                print(f"   insurance_company (col 11): {insurance_company}")
                print(f"   sub_company (col 12): {sub_company}")
                print(f"   amount (col 13): {amount}")
                print("=" * 60)

            # ✅ البحث في Cache
            key = (account_number, service_code)
            record = records_cache.get(key)

            if record:
                # ✅ تحديث البيانات مع تتبع التغييرات
                changes = []
                
                if record.patient_type != patient_type:
                    changes.append(f"patient_type: '{record.patient_type}' -> '{patient_type}'")
                    record.patient_type = patient_type
                    
                if record.patient_name != patient_name:
                    changes.append(f"patient_name: '{record.patient_name}' -> '{patient_name}'")
                    record.patient_name = patient_name
                    
                if record.admission_date != admission_date:
                    changes.append(f"admission_date: {record.admission_date} -> {admission_date}")
                    record.admission_date = admission_date
                    
                if record.discharge_date != discharge_date:
                    changes.append(f"discharge_date: {record.discharge_date} -> {discharge_date}")
                    record.discharge_date = discharge_date
                    
                if record.stay_duration != stay_duration:
                    changes.append(f"stay_duration: '{record.stay_duration}' -> '{stay_duration}'")
                    record.stay_duration = stay_duration
                    
                if record.department_name != department_name:
                    changes.append(f"department_name: '{record.department_name}' -> '{department_name}'")
                    record.department_name = department_name
                    
                if record.service_name != service_name:
                    changes.append(f"service_name: '{record.service_name}' -> '{service_name}'")
                    record.service_name = service_name
                    
                if record.service_date != service_date:
                    changes.append(
                        f"service_date: {record.service_date} (type: {type(record.service_date)}) -> "
                        f"{service_date} (type: {type(service_date)})"
                    )
                    record.service_date = service_date
                    
                if record.insurance_company != insurance_company:
                    changes.append(f"insurance_company: '{record.insurance_company}' -> '{insurance_company}'")
                    record.insurance_company = insurance_company
                    
                if record.sub_company != sub_company:
                    changes.append(f"sub_company: '{record.sub_company}' -> '{sub_company}'")
                    record.sub_company = sub_company
                    
                if record.amount != amount:
                    changes.append(f"amount: {record.amount} (type: {type(record.amount)}) -> {amount} (type: {type(amount)})")
                    record.amount = amount

                if changes:
                    change_log.append({
                        "account_number": account_number,
                        "service_code": service_code,
                        "changes": changes
                    })
                    
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
                )
                records_to_create.append(record)
                records_cache[key] = record
                result["created"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ عرض التغييرات للتحليل
        # ============================================================
        if change_log:
            print("\n" + "="*80)
            print("🔍 DETAILED CHANGE LOG (First 10 changes only):")
            print("="*80)
            for i, log in enumerate(change_log[:10]):
                print(f"\n📝 Change #{i+1}:")
                print(f"   Account: {log['account_number']}")
                print(f"   Service Code: {log['service_code']}")
                for change in log['changes']:
                    print(f"   • {change}")
            print(f"\n... and {len(change_log) - 10} more changes" if len(change_log) > 10 else "")
            print("="*80 + "\n")

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
                    ],
                    batch_size=100,
                )
                total_updated += len(batch)
                print(f"   ✅ Updated batch {i//BATCH_SIZE + 1} ({total_updated}/{len(records_to_update)})")

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result