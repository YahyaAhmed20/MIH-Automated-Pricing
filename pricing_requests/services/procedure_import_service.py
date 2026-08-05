# pricing_requests/services/procedure_import_service.py

import pandas as pd
import time
from django.db import transaction
from pricing_requests.models import Procedure
from imports.utils.import_helpers import ImportHelpers


class ProcedureImportService:

    @staticmethod
    def extract_procedures_from_row(row):
        """
        استخراج الإجراءات من صف واحد في شيت 9
        """
        procedures = []
        
        # ✅ قراءة البيانات الأساسية
        company_name = ImportHelpers.normalize_text(row.get(0, ""))
        company_code = ImportHelpers.normalize_text(row.get(1, ""))
        year = ImportHelpers.normalize_text(row.get(2, ""))
        
        # ✅ إذا كان الصف فارغاً (بدون شركة)، نتخطاه
        if not company_name or not company_code:
            return procedures
        
        # ✅ تعريف مجموعات الخدمات في الشيت
        # كل مجموعة تتكون من: [العمود, اسم الخدمة]
        service_groups = [
            # (العمود, اسم الخدمة)
            (3, "الاشعه التداخليه"),
            (5, "خدمات الكلي"),
            (8, "العلاج الاشعاعي"),
            (11, "علاج الالم"),
            (13, "خدمات بنك الدم"),
            (16, "المرافق"),
            (18, "الاسعاف"),
            (21, "خدمات الكلي (خارجي)"),
            (24, "العلاج الاشعاعي (خارجي)"),
            (27, "الاسعاف (خارجي)"),
        ]
        
        for start_col, specialty_name in service_groups:
            # نسبة الخصم
            discount = row.get(start_col, "")
            # التفاصيل (قد يكون هناك عدة أسطر من الخدمات)
            details = row.get(start_col + 1, "")
            
            # ✅ إذا كانت الخدمة موجودة
            if details and str(details).strip():
                # تقسيم التفاصيل (قد تحتوي على عدة خدمات)
                service_items = str(details).split('\n') if '\n' in str(details) else [details]
                
                for item in service_items:
                    if item and str(item).strip():
                        operation_name = ImportHelpers.normalize_text(item)
                        
                        # ✅ إنشاء كود فريد للخدمة
                        code = (
                            f"{company_code}_"
                            f"{specialty_name}_"
                            f"{operation_name}"
                        )
                        code = ImportHelpers.normalize_text(code)[:100]
                        
                        procedures.append({
                            'code': code,
                            'operation_name': operation_name,
                            'specialty_name': specialty_name,
                            'category': f"{company_name} - {year}",
                            'english_name': "",
                        })
        
        return procedures

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Procedures import from Sheet 9...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ Cache للـ Procedures
        # ============================================================
        print("⏳ Loading existing procedures...")
        procedures_cache = {}
        for procedure in Procedure.objects.all():
            code = ImportHelpers.normalize_text(procedure.code)
            procedures_cache[code] = procedure
        print(f"   ✅ {len(procedures_cache)} procedures loaded")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        to_create = []
        to_update = []
        sheet_records = set()

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة (بدون Header)
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):
            
            # ✅ استخراج الإجراءات من الصف
            procedures_data = ProcedureImportService.extract_procedures_from_row(row)
            
            if not procedures_data:
                result["skipped"] += 1
                continue

            result["processed"] += 1
            processed = result["processed"]

            for proc_data in procedures_data:
                code = proc_data['code']
                sheet_records.add(code)
                
                operation_name = proc_data['operation_name']
                specialty_name = proc_data['specialty_name']
                category = proc_data['category']

                # ✅ البحث في Cache
                existing_procedure = procedures_cache.get(code)

                if existing_procedure:
                    # ✅ تحديث البيانات
                    changed = False
                    
                    if existing_procedure.operation_name != operation_name:
                        existing_procedure.operation_name = operation_name
                        changed = True
                        
                    if existing_procedure.specialty_name != specialty_name:
                        existing_procedure.specialty_name = specialty_name
                        changed = True
                        
                    if existing_procedure.category != category:
                        existing_procedure.category = category
                        changed = True

                    if changed:
                        to_update.append(existing_procedure)
                        result["updated"] += 1

                else:
                    # ✅ إنشاء جديد
                    procedure = Procedure(
                        code=code,
                        operation_name=operation_name,
                        specialty_name=specialty_name,
                        category=category,
                        english_name="",
                    )
                    to_create.append(procedure)
                    procedures_cache[code] = procedure
                    result["created"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(to_create)} procedures...")
        print(f"💾 Updating {len(to_update)} procedures...")

        BATCH_SIZE = 500

        if to_create:
            Procedure.objects.bulk_create(
                to_create,
                batch_size=BATCH_SIZE,
            )

        if to_update:
            total_updated = 0

            for i in range(0, len(to_update), BATCH_SIZE):
                batch = to_update[i:i + BATCH_SIZE]

                Procedure.objects.bulk_update(
                    batch,
                    fields=[
                        "operation_name",
                        "specialty_name",
                        "category",
                    ],
                    batch_size=100,
                )

                total_updated += len(batch)

                print(
                    f"   ✅ Updated batch {i // BATCH_SIZE + 1} "
                    f"({total_updated}/{len(to_update)})"
                )

        # ============================================================
        # ✅ Reload Cache بعد الـ Bulk Operations
        # ============================================================
        procedures_cache = {}
        for procedure in Procedure.objects.all():
            code = ImportHelpers.normalize_text(procedure.code)
            procedures_cache[code] = procedure

        # ============================================================
        # ✅ Delete Procedures not found in Sheet
        # ============================================================
        to_delete = []

        for code, procedure in procedures_cache.items():
            if code not in sheet_records:
                to_delete.append(procedure.id)

        if to_delete:
            deleted, _ = Procedure.objects.filter(
                id__in=to_delete
            ).delete()

            result["deleted"] = deleted
            print(f"🗑️ Deleted {deleted} procedures")

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result