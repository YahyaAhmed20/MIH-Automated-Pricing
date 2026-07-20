# pricing_requests/services/pricing_details_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from pricing_requests.models import PricingDetail
from imports.utils.import_helpers import ImportHelpers


class PricingDetailsImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Pricing Details import...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ Cache للـ Pricing Details
        # ============================================================
        print("⏳ Loading existing pricing details...")
        records_cache = {}
        
        # ✅ بناء مفتاح مركب للبحث
        for record in PricingDetail.objects.all():
            key = (
                ImportHelpers.normalize_text(record.patient_name),
                ImportHelpers.normalize_text(record.company_name),
                ImportHelpers.normalize_text(record.procedure_name),
                record.pricing_date,
            )
            records_cache[key] = record
            
        print(f"   ✅ {len(records_cache)} records loaded")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        to_create = []
        to_update = []

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة (بدون Header)
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ أرقام الأعمدة حسب ترتيب الشيت
            # العمود 0: تاريخ التسعير
            pricing_date = ImportHelpers.clean_date(row.get(0, None))
            
            # العمود 1: الجروب
            group_name = ImportHelpers.normalize_text(row.get(1, ""))
            
            # العمود 2: اسم المريض
            patient_name = ImportHelpers.normalize_text(row.get(2, ""))
            
            # العمود 3: الشركة
            company_name = ImportHelpers.normalize_text(row.get(3, ""))
            
            # العمود 4: اسم الطبيب
            doctor_name = ImportHelpers.normalize_text(row.get(4, ""))
            
            # العمود 5: التقرير
            report_name = ImportHelpers.normalize_text(row.get(5, ""))
            
            # العمود 6: الاجراء
            procedure_name = ImportHelpers.normalize_text(row.get(6, ""))
            
            # العمود 7: التخصص
            specialty_name = ImportHelpers.normalize_text(row.get(7, ""))
            
            # العمود 8: نوع التسعير
            pricing_type = ImportHelpers.normalize_text(row.get(8, ""))
            
            # العمود 9: رقم الكارنية
            card_number = ImportHelpers.normalize_text(row.get(9, ""))
            
            # العمود 10: اسم المحاسب
            accountant_name = ImportHelpers.normalize_text(row.get(10, ""))
            
            # العمود 11: ملاحظات خاصة بالتكلفة
            cost_notes = ImportHelpers.normalize_text(row.get(11, ""))
            
            # العمود 12: التكلفه
            cost = ImportHelpers.clean_decimal(row.get(12, None))
            if cost is None:
                cost = Decimal('0.00')
            
            # العمود 13: التفاصيل
            details = ImportHelpers.normalize_text(row.get(13, ""))

            # ✅ قيم افتراضية
            if not patient_name:
                patient_name = f"UNKNOWN_PATIENT_{index}"
                print(f"⚠️ صف {index}: اسم المريض مفقود - تم استخدام اسم افتراضي")

            if not company_name:
                company_name = "بدون شركة"
                print(f"⚠️ صف {index}: اسم الشركة مفقود - تم استخدام اسم افتراضي")

            if not procedure_name:
                procedure_name = "بدون اجراء"
                print(f"⚠️ صف {index}: اسم الاجراء مفقود - تم استخدام اسم افتراضي")

            result["processed"] += 1
            processed = result["processed"]

            # ✅ البحث في Cache
            key = (
                patient_name,
                company_name,
                procedure_name,
                pricing_date,
            )
            
            existing_record = records_cache.get(key)

            if existing_record:
                # ✅ تحديث البيانات
                changed = False
                
                if existing_record.group_name != group_name:
                    existing_record.group_name = group_name
                    changed = True
                    
                if existing_record.doctor_name != doctor_name:
                    existing_record.doctor_name = doctor_name
                    changed = True
                    
                if existing_record.report_name != report_name:
                    existing_record.report_name = report_name
                    changed = True
                    
                if existing_record.specialty_name != specialty_name:
                    existing_record.specialty_name = specialty_name
                    changed = True
                    
                if existing_record.pricing_type != pricing_type:
                    existing_record.pricing_type = pricing_type
                    changed = True
                    
                if existing_record.card_number != card_number:
                    existing_record.card_number = card_number
                    changed = True
                    
                if existing_record.accountant_name != accountant_name:
                    existing_record.accountant_name = accountant_name
                    changed = True
                    
                if existing_record.cost_notes != cost_notes:
                    existing_record.cost_notes = cost_notes
                    changed = True
                    
                if existing_record.cost != cost:
                    existing_record.cost = cost
                    changed = True
                    
                if existing_record.details != details:
                    existing_record.details = details
                    changed = True

                if changed:
                    to_update.append(existing_record)
                    result["updated"] += 1

            else:
                # ✅ إنشاء جديد
                record = PricingDetail(
                    pricing_date=pricing_date,
                    group_name=group_name,
                    patient_name=patient_name,
                    company_name=company_name,
                    doctor_name=doctor_name,
                    report_name=report_name,
                    procedure_name=procedure_name,
                    specialty_name=specialty_name,
                    pricing_type=pricing_type,
                    card_number=card_number,
                    accountant_name=accountant_name,
                    cost_notes=cost_notes,
                    cost=cost,
                    details=details,
                )
                to_create.append(record)
                records_cache[key] = record
                result["created"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(to_create)} records...")
        print(f"💾 Updating {len(to_update)} records...")

        if to_create:
            PricingDetail.objects.bulk_create(to_create, batch_size=1000)

        if to_update:
            PricingDetail.objects.bulk_update(
                to_update,
                fields=[
                    "group_name",
                    "doctor_name",
                    "report_name",
                    "specialty_name",
                    "pricing_type",
                    "card_number",
                    "accountant_name",
                    "cost_notes",
                    "cost",
                    "details",
                ],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result