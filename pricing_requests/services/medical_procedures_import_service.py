# pricing_requests/services/medical_procedures_import_service.py

import pandas as pd
import time
from django.db import transaction
from medical_catalog.models import Specialty, Procedure
from imports.utils.import_helpers import ImportHelpers


class MedicalProceduresImportService:

    @staticmethod
    def truncate_text(value, max_length=255):
        """تقليص النص إذا تجاوز الحد الأقصى"""
        if not value:
            return value
        cleaned = ImportHelpers.normalize_text(value)
        if len(cleaned) > max_length:
            print(f"⚠️ تم تقليص نص طويل من {len(cleaned)} إلى {max_length} حرف")
            return cleaned[:max_length]
        return cleaned

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Medical Procedures import from Sheet 13...")

        result = {
            "processed": 0,
            "created_specialties": 0,
            "created_procedures": 0,
            "updated_procedures": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ Cache للـ Specialties
        # ============================================================
        print("⏳ Loading specialties...")
        specialties_cache = {}
        for s in Specialty.objects.all():
            specialties_cache[ImportHelpers.normalize_text(s.name)] = s
        print(f"   ✅ {len(specialties_cache)} specialties loaded")

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
        procedures_to_create = []
        procedures_to_update = []

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة (بدون Header)
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ أرقام الأعمدة حسب ترتيب شيت 13
            # العمود 0: الكود (procedure_code)
            procedure_code = ImportHelpers.normalize_text(row.get(0, ""))
            procedure_code = MedicalProceduresImportService.truncate_text(procedure_code, 50)

            if not procedure_code:
                result["skipped"] += 1
                continue

            # العمود 1: أسم العملية (procedure_name_ar)
            name_ar = ImportHelpers.normalize_text(row.get(1, ""))
            name_ar = MedicalProceduresImportService.truncate_text(name_ar, 255)

            # العمود 2: التخصص (specialty)
            specialty_name = ImportHelpers.normalize_text(row.get(2, ""))
            specialty_name = MedicalProceduresImportService.truncate_text(specialty_name, 255)

            if not specialty_name:
                specialty_name = "بدون تخصص"
                print(f"⚠️ صف {index}: التخصص مفقود - تم استخدام 'بدون تخصص'")

            # العمود 3: التصنيف (procedure_category)
            classification = ImportHelpers.normalize_text(row.get(3, ""))
            classification = MedicalProceduresImportService.truncate_text(classification, 100)

            # العمود 4: المسمي باللغه الانجليزيه (procedure_name_en)
            name_en = ImportHelpers.normalize_text(row.get(4, ""))
            name_en = MedicalProceduresImportService.truncate_text(name_en, 255)

            result["processed"] += 1
            processed = result["processed"]

            # ✅ الحصول على التخصص (أو إنشاؤه)
            specialty = specialties_cache.get(specialty_name)
            if not specialty:
                specialty = Specialty.objects.create(
                    name=specialty_name,
                    is_active=True,
                )
                specialties_cache[specialty_name] = specialty
                result["created_specialties"] += 1

            # ✅ البحث في Cache
            existing_procedure = procedures_cache.get(procedure_code)

            if existing_procedure:
                # ✅ تحديث البيانات
                changed = False

                if existing_procedure.name_ar != name_ar:
                    existing_procedure.name_ar = name_ar
                    changed = True

                if existing_procedure.name_en != name_en:
                    existing_procedure.name_en = name_en
                    changed = True

                if existing_procedure.specialty_id != specialty.id:
                    existing_procedure.specialty = specialty
                    changed = True

                if existing_procedure.classification != classification:
                    existing_procedure.classification = classification
                    changed = True

                if existing_procedure.is_active is not True:
                    existing_procedure.is_active = True
                    changed = True

                if changed:
                    procedures_to_update.append(existing_procedure)
                    result["updated_procedures"] += 1

            else:
                # ✅ إنشاء جديد
                procedure = Procedure(
                    code=procedure_code,
                    name_ar=name_ar,
                    name_en=name_en,
                    specialty=specialty,
                    classification=classification,
                    is_active=True,
                )
                procedures_to_create.append(procedure)
                procedures_cache[procedure_code] = procedure
                result["created_procedures"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(procedures_to_create)} procedures...")
        print(f"💾 Updating {len(procedures_to_update)} procedures...")

        if procedures_to_create:
            Procedure.objects.bulk_create(procedures_to_create, batch_size=1000)

        if procedures_to_update:
            Procedure.objects.bulk_update(
                procedures_to_update,
                fields=[
                    "name_ar",
                    "name_en",
                    "specialty",
                    "classification",
                    "is_active",
                ],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result