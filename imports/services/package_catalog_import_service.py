import pandas as pd
import time
from django.db import transaction
from medical_catalog.models import Package, Specialty
from contracts.models import ContractEntity
from imports.utils.import_helpers import ImportHelpers


class PackageCatalogImportService:

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
        print("⏳ Starting Package Catalog import from Sheet 1...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "created_specialties": 0,
            "deleted": 0,
            "skipped_duplicates": 0,
            "missing_specialty": 0,
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
        # ✅ Cache للـ ContractEntity (الشركات)
        # ============================================================
        print("⏳ Loading entities...")
        entities_cache = {}
        for e in ContractEntity.objects.all():
            entities_cache[ImportHelpers.normalize_text(e.name)] = e
        print(f"   ✅ {len(entities_cache)} entities loaded")

        # ============================================================
        # ✅ Cache للـ Packages - باستخدام (code, entity_id) كمفتاح
        # ============================================================
        print("⏳ Loading packages...")
        packages_cache = {}
        for p in Package.objects.exclude(code__isnull=True):
            key = (
                ImportHelpers.normalize_text(p.code),
                p.entity_id if p.entity_id else None,
            )
            packages_cache[key] = p
        print(f"   ✅ {len(packages_cache)} packages loaded")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        packages_to_create = []
        packages_to_update = []
        sheet_codes = set()
        # ✅ إزالة seen_keys عشان تظهر كل الصفوف حتى المكررة
        # seen_keys = set()

        # ============================================================
        # ✅ Loop - استخدام to_dict("records") (الأسرع)
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ الأعمدة الصحيحة حسب ترتيب شيت 1
            company_name = ImportHelpers.normalize_text(row.get(0, ""))
            contract_type = ImportHelpers.normalize_text(row.get(1, ""))
            
            package_name = ImportHelpers.normalize_text(row.get(2, ""))
            package_name = PackageCatalogImportService.truncate_text(package_name, 255)
            
            specialty_name = ImportHelpers.normalize_text(row.get(3, ""))
            specialty_name = PackageCatalogImportService.truncate_text(specialty_name, 255)
            
            # ✅ قراءة السعر
            price_value = ImportHelpers.clean_decimal(row.get(4, None))
            
            stay_duration = ImportHelpers.normalize_text(row.get(5, ""))
            
            package_code = ImportHelpers.normalize_text(row.get(6, ""))
            
            valid_from = row.get(7, "")
            valid_until = row.get(8, "")
            
            package_note = ImportHelpers.normalize_text(row.get(9, ""))
            # package_note = PackageCatalogImportService.truncate_text(package_note, 255)

            # ✅ قيم افتراضية
            if not package_code:
                package_code = f"UNKNOWN_CODE_{index}"
                print(f"⚠️ صف {index}: الكود مفقود - تم استخدام كود افتراضي")

            if not package_name:
                package_name = f"UNKNOWN_PACKAGE_{index}"
                print(f"⚠️ صف {index}: اسم الباكدج مفقود - تم استخدام اسم افتراضي")

            # ✅ تخطي الصفوف الفارغة
            if not package_code and not package_name:
                result["skipped"] = result.get("skipped", 0) + 1
                continue

            # ✅ جلب الـ entity (الشركة)
            entity = entities_cache.get(company_name)
            if not entity:
                print(f"⚠️ صف {index}: الشركة '{company_name}' غير موجودة - سيتم تخطي الصف")
                continue

            # ✅ ❌ إزالة منع التكرار عشان تظهر كل الصفوف
            # key = (package_code, entity.id)
            # if key in seen_keys:
            #     result["skipped_duplicates"] += 1
            #     continue
            # seen_keys.add(key)

            # ✅ تخزين الأكواد للحذف
            sheet_codes.add(package_code)

            result["processed"] += 1
            processed = result["processed"]

            # ✅ الحصول على التخصص (أو إنشاؤه)
            specialty = None
            if specialty_name:
                specialty = specialties_cache.get(specialty_name)
                if not specialty:
                    specialty = Specialty.objects.create(
                        name=specialty_name,
                        is_active=True,
                    )
                    specialties_cache[specialty_name] = specialty
                    result["created_specialties"] += 1

            # ✅ البحث في Cache بـ (code, entity_id)
            package_key = (package_code, entity.id)
            existing_package = packages_cache.get(package_key)

            if existing_package:
                # ✅ تحديث البيانات
                changed = False

                if existing_package.name != package_name:
                    existing_package.name = package_name
                    changed = True

                if existing_package.specialty_id != (specialty.id if specialty else None):
                    existing_package.specialty = specialty
                    changed = True

                if existing_package.stay_duration != stay_duration:
                    existing_package.stay_duration = stay_duration
                    changed = True

                if existing_package.package_note != package_note:
                    existing_package.package_note = package_note
                    changed = True

                if existing_package.base_price != price_value:
                    existing_package.base_price = price_value
                    changed = True

                if existing_package.is_active is not True:
                    existing_package.is_active = True
                    changed = True

                if changed:
                    packages_to_update.append(existing_package)
                    result["updated"] += 1

            else:
                # ✅ إنشاء جديد مع ربط الـ entity و base_price
                new_package = Package(
                    code=package_code,
                    name=package_name,
                    specialty=specialty,
                    entity=entity,
                    base_price=price_value,
                    stay_duration=stay_duration,
                    package_note=package_note,
                    is_active=True,
                )
                packages_to_create.append(new_package)
                packages_cache[package_key] = new_package
                result["created"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ حذف الباكدجات غير الموجودة في الـ Sheet
        # ============================================================
        if sheet_codes:
            deleted_count, _ = Package.objects.exclude(
                code__in=sheet_codes
            ).delete()
            if deleted_count > 0:
                print(f"🗑️ Deleted {deleted_count} packages not in sheet")
                result["deleted"] = deleted_count
        else:
            print("⚠️ No codes in sheet - skipping deletion to avoid data loss")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(packages_to_create)} packages...")
        print(f"💾 Updating {len(packages_to_update)} packages...")

        if packages_to_create:
            Package.objects.bulk_create(packages_to_create, batch_size=1000)

        if packages_to_update:
            Package.objects.bulk_update(
                packages_to_update,
                fields=[
                    "name",
                    "specialty",
                    "stay_duration",
                    "base_price",
                    "package_note",
                    "is_active",
                ],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result