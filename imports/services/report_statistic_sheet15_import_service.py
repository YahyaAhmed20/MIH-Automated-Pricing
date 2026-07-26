# imports/services/report_statistic_sheet15_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from frontend.models import ReportStatisticSheet15
from imports.utils.import_helpers import ImportHelpers


class ReportStatisticSheet15ImportService:

    @staticmethod
    def clean_amount(value):
        """تنظيف قيمة المبلغ"""
        if value is None or pd.isna(value):
            return Decimal('0.00')
        
        try:
            if isinstance(value, (int, float)):
                return Decimal(str(value)).quantize(Decimal('0.01'))
            
            cleaned = str(value).strip()
            cleaned = cleaned.replace(',', '').replace('٬', '')
            cleaned = cleaned.replace('٫', '.')
            
            return Decimal(cleaned).quantize(Decimal('0.01'))
            
        except (ValueError, TypeError):
            return Decimal('0.00')

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Report Statistics Sheet 15 import...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "errors": 0,
        }

        # ============================================================
        # ✅ تخطي الصف الأول (العناوين)
        # ============================================================
        data = dataframe.iloc[1:].copy()
        data = data.reset_index(drop=True)
        
        print(f"📊 عدد الصفوف بعد تخطي العناوين: {len(data)}")
        print("=" * 50)

        # ============================================================
        # ✅ Cache
        # ============================================================
        print("⏳ Loading existing records...")
        stats_cache = {}
        for stat in ReportStatisticSheet15.objects.all():
            key = (
                ImportHelpers.normalize_text(stat.medical_number),
                ImportHelpers.normalize_text(stat.account_number),
                ImportHelpers.normalize_text(stat.patient_name),
            )
            stats_cache[key] = stat
        print(f"   ✅ {len(stats_cache)} records loaded")

        # ============================================================
        # ✅ قوائم التجميع
        # ============================================================
        to_create = []
        to_update = []

        # ============================================================
        # ✅ Loop
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(data)
        processed = 0

        for index, row in data.iterrows():
            try:
                # ✅ أرقام الأعمدة في شيت 15
                # العمود 0: الرقم الطبي
                medical_number = ""
                if len(row) > 0 and pd.notna(row.iloc[0]):
                    medical_number = ImportHelpers.normalize_text(row.iloc[0])
                
                # العمود 1: الرقم الحسابي
                account_number = ""
                if len(row) > 1 and pd.notna(row.iloc[1]):
                    account_number = ImportHelpers.normalize_text(row.iloc[1])
                
                # العمود 2: اسم المريض
                patient_name = ""
                if len(row) > 2 and pd.notna(row.iloc[2]):
                    patient_name = ImportHelpers.normalize_text(row.iloc[2])
                
                if not patient_name:
                    result["skipped"] += 1
                    continue
                
                # العمود 3: تاريخ الدخول
                admission_date = None
                if len(row) > 3 and pd.notna(row.iloc[3]):
                    admission_date = ImportHelpers.clean_date(row.iloc[3])
                
                # العمود 4: تاريخ الخروج
                discharge_date = None
                if len(row) > 4 and pd.notna(row.iloc[4]):
                    discharge_date = ImportHelpers.clean_date(row.iloc[4])
                
                # العمود 5: الشهر
                month = ""
                if len(row) > 5 and pd.notna(row.iloc[5]):
                    month = ImportHelpers.normalize_text(row.iloc[5])
                
                # العمود 6: التخصص
                specialty = ""
                if len(row) > 6 and pd.notna(row.iloc[6]):
                    specialty = ImportHelpers.normalize_text(row.iloc[6])
                
                # العمود 7: اسم الباكدج
                package_name = ""
                if len(row) > 7 and pd.notna(row.iloc[7]):
                    package_name = ImportHelpers.normalize_text(row.iloc[7])
                
                # العمود 8: الجهه
                entity_name = ""
                if len(row) > 8 and pd.notna(row.iloc[8]):
                    entity_name = ImportHelpers.normalize_text(row.iloc[8])
                
                # العمود 9: القطاع
                sector = ""
                if len(row) > 9 and pd.notna(row.iloc[9]):
                    sector = ImportHelpers.normalize_text(row.iloc[9])
                
                # العمود 10: نوع الدفع
                payment_type = ""
                if len(row) > 10 and pd.notna(row.iloc[10]):
                    payment_type = ImportHelpers.normalize_text(row.iloc[10])
                
                # العمود 11: الشركة الفرعية
                sub_company = ""
                if len(row) > 11 and pd.notna(row.iloc[11]):
                    sub_company = ImportHelpers.normalize_text(row.iloc[11])
                
                # العمود 12: سعر الخدمه
                service_price = Decimal('0.00')
                if len(row) > 12 and pd.notna(row.iloc[12]):
                    service_price = ReportStatisticSheet15ImportService.clean_amount(row.iloc[12])
                
                # العمود 13: قيمة الفاتوره
                invoice_amount = Decimal('0.00')
                if len(row) > 13 and pd.notna(row.iloc[13]):
                    invoice_amount = ReportStatisticSheet15ImportService.clean_amount(row.iloc[13])
                
                # العمود 14: الكود
                code = ""
                if len(row) > 14 and pd.notna(row.iloc[14]):
                    code = ImportHelpers.normalize_text(row.iloc[14])
                
                # ✅ العمود 15: اسم الطبيب (العمود الأخير)
                doctor_name = ""
                if len(row) > 15 and pd.notna(row.iloc[15]):
                    doctor_name = ImportHelpers.normalize_text(row.iloc[15])

                result["processed"] += 1
                processed = result["processed"]

                # ✅ البحث في Cache
                key = (
                    medical_number,
                    account_number,
                    patient_name,
                )
                existing_stat = stats_cache.get(key)

                if existing_stat:
                    # ✅ تحديث البيانات
                    changed = False
                    
                    if existing_stat.admission_date != admission_date:
                        existing_stat.admission_date = admission_date
                        changed = True
                        
                    if existing_stat.discharge_date != discharge_date:
                        existing_stat.discharge_date = discharge_date
                        changed = True
                        
                    if existing_stat.month != month:
                        existing_stat.month = month
                        changed = True
                        
                    if existing_stat.specialty != specialty:
                        existing_stat.specialty = specialty
                        changed = True
                        
                    if existing_stat.package_name != package_name:
                        existing_stat.package_name = package_name
                        changed = True
                        
                    if existing_stat.entity_name != entity_name:
                        existing_stat.entity_name = entity_name
                        changed = True
                        
                    if existing_stat.sector != sector:
                        existing_stat.sector = sector
                        changed = True
                        
                    if existing_stat.payment_type != payment_type:
                        existing_stat.payment_type = payment_type
                        changed = True
                        
                    if existing_stat.sub_company != sub_company:
                        existing_stat.sub_company = sub_company
                        changed = True
                        
                    if existing_stat.service_price != service_price:
                        existing_stat.service_price = service_price
                        changed = True
                        
                    if existing_stat.invoice_amount != invoice_amount:
                        existing_stat.invoice_amount = invoice_amount
                        changed = True
                        
                    if existing_stat.code != code:
                        existing_stat.code = code
                        changed = True
                    
                    # ✅ اسم الطبيب
                    if existing_stat.doctor_name != doctor_name:
                        existing_stat.doctor_name = doctor_name
                        changed = True

                    if changed:
                        to_update.append(existing_stat)
                        result["updated"] += 1

                else:
                    # ✅ إنشاء جديد
                    stat = ReportStatisticSheet15(
                        medical_number=medical_number,
                        account_number=account_number,
                        patient_name=patient_name,
                        admission_date=admission_date,
                        discharge_date=discharge_date,
                        month=month,
                        specialty=specialty,
                        package_name=package_name,
                        entity_name=entity_name,
                        sector=sector,
                        payment_type=payment_type,
                        sub_company=sub_company,
                        service_price=service_price,
                        invoice_amount=invoice_amount,
                        code=code,
                        doctor_name=doctor_name,  # ✅ جديد
                    )
                    to_create.append(stat)
                    stats_cache[key] = stat
                    result["created"] += 1

                # عرض التقدم
                if processed % 1000 == 0:
                    print(f"   📊 Processed {processed}/{total_rows} rows...")

            except Exception as e:
                result["errors"] += 1
                if result["errors"] <= 10:
                    print(f"   ❌ خطأ في الصف {index + 2}: {str(e)[:80]}...")
                continue

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(to_create)} records...")
        print(f"💾 Updating {len(to_update)} records...")

        if to_create:
            ReportStatisticSheet15.objects.bulk_create(to_create, batch_size=1000)

        if to_update:
            ReportStatisticSheet15.objects.bulk_update(
                to_update,
                fields=[
                    "admission_date",
                    "discharge_date",
                    "month",
                    "specialty",
                    "package_name",
                    "entity_name",
                    "sector",
                    "payment_type",
                    "sub_company",
                    "service_price",
                    "invoice_amount",
                    "code",
                    "doctor_name",  # ✅ جديد
                ],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time

        # عرض النتائج النهائية
        print("\n" + "=" * 50)
        print("✅ انتهى استيراد شيت 15!")
        print(f"   📊 تمت المعالجة: {result['processed']}")
        print(f"   ✅ تم الإنشاء: {result['created']}")
        print(f"   🔄 تم التحديث: {result['updated']}")
        print(f"   ⏭️ تم التخطي: {result['skipped']}")
        if result["errors"] > 0:
            print(f"   ❌ الأخطاء: {result['errors']}")
        print(f"   ⏱️ الوقت: {elapsed:.2f} ثانية")
        print("=" * 50)

        return result