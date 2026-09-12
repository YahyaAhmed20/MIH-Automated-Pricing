# imports/services/report_statistic_sheet15_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from frontend.models import ReportStatisticSheet15
from imports.utils.import_helpers import ImportHelpers


class ReportStatisticSheet15ImportService:

    COLUMN_MAPPING = {
        "medical_number": "الرقم الطبي",
        "account_number": "الرقم الحسابي",
        "patient_name": "اسم المريض",
        "admission_date": "تاريخ الدخول",
        "discharge_date": "تاريخ الخروج",
        "month": "الشهر",
        "specialty": "التخصص",
        "package_name": "اسم الباكدج",
        "entity_name": "الجهه",
        "sector": "القطاع",
        "payment_type": "نوع الدفع",
        "sub_company": "الشركه الفرعيه",
        "package_price": "سعر الباكدج",
        "invoice_amount": "قيمة الفاتوره",
        "code": "الكود",
        "doctor_name": "اسم الطبيب",
    }

    REQUIRED_COLUMNS = list(COLUMN_MAPPING.values())

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Report Statistics Sheet 15 import...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }

        # ============================================================
        # Header Validation & Mapping
        # ============================================================
        header_map = ImportHelpers.validate_required_columns(
            dataframe,
            ReportStatisticSheet15ImportService.REQUIRED_COLUMNS,
        )

        print("✅ Sheet 15 headers validated successfully")

        # ============================================================
        # Data
        # ============================================================
        # GoogleSheetsService already returns data rows
        # with the first row used as headers.
        data = dataframe.copy()

        print(f"📊 عدد الصفوف: {len(data)}")
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
        # ✅ Existing Keys + Sheet Keys
        # ============================================================
        existing_keys = set(stats_cache.keys())
        sheet_keys = set()

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
                
                
                # ====================================================
                # قراءة الأعمدة بالاسم وليس بالترتيب
                # ====================================================

                medical_number = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "medical_number",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                account_number = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "account_number",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                patient_name = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "patient_name",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                if not patient_name:
                    result["skipped"] += 1
                    continue
                

                admission_date = ImportHelpers.clean_date(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "admission_date",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                        default=None,
                    )
                )

                discharge_date = ImportHelpers.clean_date(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "discharge_date",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                        default=None,
                    )
                )

                month = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "month",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                specialty = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "specialty",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                package_name = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "package_name",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                entity_name = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "entity_name",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                sector = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "sector",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                payment_type = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "payment_type",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                sub_company = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "sub_company",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                # ✅ سعر الباكدج من الشيت
                package_price = ImportHelpers.clean_decimal(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "package_price",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                        default=0,
                    )
                )

                invoice_amount = ImportHelpers.clean_decimal(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "invoice_amount",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                        default=0,
                    )
                )

                code = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "code",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                doctor_name = ImportHelpers.normalize_text(
                    ImportHelpers.get_mapped_value(
                        row,
                        header_map,
                        "doctor_name",
                        ReportStatisticSheet15ImportService.COLUMN_MAPPING,
                    )
                )

                result["processed"] += 1
                processed = result["processed"]

                # ✅ إضافة المفتاح إلى sheet_keys
                key = (
                    medical_number,
                    account_number,
                    patient_name,
                )
                sheet_keys.add(key)

                # ✅ البحث في Cache
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
                        
                    if existing_stat.package_price != package_price:
                        existing_stat.package_price = package_price
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
                        package_price=package_price,
                        invoice_amount=invoice_amount,
                        code=code,
                        doctor_name=doctor_name,
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
                    "package_price",
                    "invoice_amount",
                    "code",
                    "doctor_name",
                ],
                batch_size=1000,
            )

        # ============================================================
        # ✅ Delete Removed Records
        # ============================================================
        keys_to_delete = existing_keys - sheet_keys

        if keys_to_delete:
            ids_to_delete = [
                stats_cache[key].id
                for key in keys_to_delete
            ]

            deleted_count, _ = ReportStatisticSheet15.objects.filter(
                id__in=ids_to_delete
            ).delete()

            result["deleted"] = deleted_count
            print(f"🗑️ Deleted {deleted_count} records")

        elapsed = time.perf_counter() - start_time

        # عرض النتائج النهائية
        print("\n" + "=" * 50)
        print("✅ انتهى استيراد شيت 15!")
        print(f"   📊 تمت المعالجة: {result['processed']}")
        print(f"   ✅ تم الإنشاء: {result['created']}")
        print(f"   🔄 تم التحديث: {result['updated']}")
        print(f"   🗑️ تم الحذف: {result['deleted']}")
        print(f"   ⏭️ تم التخطي: {result['skipped']}")
        if result["errors"] > 0:
            print(f"   ❌ الأخطاء: {result['errors']}")
        print(f"   ⏱️ الوقت: {elapsed:.2f} ثانية")
        print("=" * 50)

        return result