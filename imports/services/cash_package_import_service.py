# imports/services/cash_package_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from medical_catalog.models import Package, Specialty
from imports.utils.import_helpers import ImportHelpers


class CashPackageImportService:

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
        print("⏳ Starting Cash Packages import from Sheet 2...")

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
        # ✅ Cache للـ Packages - باستخدام (code, name)
        # ============================================================
        print("⏳ Loading packages...")
        packages_cache = {}
        for p in Package.objects.exclude(code__isnull=True):
            key = (
                ImportHelpers.normalize_text(p.code),
                ImportHelpers.normalize_text(p.name),
            )
            packages_cache[key] = p
        print(f"   ✅ {len(packages_cache)} packages loaded")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        packages_to_create = []
        packages_to_update = []
        sheet_codes = set()
        seen_keys = set()

        # ============================================================
        # ✅ Loop - استخدام الأعمدة الصحيحة لشيت 2
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ أعمدة شيت 2 الصحيحة
            package_name = ImportHelpers.normalize_text(row.get(0, ""))
            package_name = CashPackageImportService.truncate_text(package_name, 255)
            
            contract_type = ImportHelpers.normalize_text(row.get(1, ""))
            contract_type = CashPackageImportService.truncate_text(contract_type, 255)
            
            specialty_name = ImportHelpers.normalize_text(row.get(2, ""))
            specialty_name = CashPackageImportService.truncate_text(specialty_name, 255)
            
            if not specialty_name:
                specialty_name = "نقدي"
                print(f"⚠️ صف {index}: تخصص مفقود - تم استخدام 'نقدي'")
            
            stay_duration = ImportHelpers.normalize_text(row.get(3, ""))
            
            package_code = ImportHelpers.normalize_text(row.get(4, ""))
            package_code = CashPackageImportService.truncate_text(package_code, 50)
            
            cash_price = ImportHelpers.clean_decimal(row.get(5, None))
            if cash_price is None:
                cash_price = Decimal('0.00')
            
            notes = ImportHelpers.normalize_text(row.get(6, ""))
            notes = CashPackageImportService.truncate_text(notes, 255)

            if not package_code:
                package_code = f"UNKNOWN_{index}"
                print(f"⚠️ صف {index}: كود مفقود - تم استخدام كود افتراضي")

            if not package_name:
                package_name = f"بدون اسم {index}"
                print(f"⚠️ صف {index}: اسم مفقود - تم استخدام اسم افتراضي")

            if not package_code and not package_name:
                result["skipped"] = result.get("skipped", 0) + 1
                continue

            package_key = (package_code, package_name)
            if package_key in seen_keys:
                result["skipped_duplicates"] += 1
                continue
            seen_keys.add(package_key)

            sheet_codes.add(package_code)

            result["processed"] += 1
            processed = result["processed"]

            specialty = specialties_cache.get(specialty_name)
            if not specialty:
                specialty = Specialty.objects.create(
                    name=specialty_name,
                    is_active=True,
                )
                specialties_cache[specialty_name] = specialty
                result["created_specialties"] += 1

            existing_package = packages_cache.get(package_key)

            if existing_package:
                changed = False

                if existing_package.specialty_id != (specialty.id if specialty else None):
                    existing_package.specialty = specialty
                    changed = True

                if existing_package.stay_duration != stay_duration:
                    existing_package.stay_duration = stay_duration
                    changed = True

                if existing_package.contract_type != contract_type:
                    existing_package.contract_type = contract_type
                    changed = True

                if existing_package.cash_price != cash_price:
                    existing_package.cash_price = cash_price
                    changed = True

                if existing_package.notes != notes:
                    existing_package.notes = notes
                    changed = True

                if existing_package.is_cash_package is not True:
                    existing_package.is_cash_package = True
                    changed = True

                if existing_package.is_active is not True:
                    existing_package.is_active = True
                    changed = True

                if changed:
                    packages_to_update.append(existing_package)
                    result["updated"] += 1

            else:
                new_package = Package(
                    code=package_code,
                    name=package_name,
                    specialty=specialty,
                    stay_duration=stay_duration,
                    contract_type=contract_type,
                    cash_price=cash_price,
                    notes=notes,
                    is_cash_package=True,
                    is_active=True,
                )
                packages_to_create.append(new_package)
                packages_cache[package_key] = new_package
                result["created"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")
        print(f"   ⏭️ Skipped {result['skipped_duplicates']} duplicate keys in sheet")

        # ============================================================
        # ✅ ✅ ✅ حذف الباكدجات النقدية فقط (غير الموجودة في الشيت)
        # ============================================================
        if sheet_codes:
            deleted_count, _ = Package.objects.filter(
                is_cash_package=True  # ✅ احذف النقدي بس
            ).exclude(
                code__in=sheet_codes
            ).delete()
            if deleted_count > 0:
                print(f"🗑️ Deleted {deleted_count} cash packages not in sheet")
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
                    "specialty",
                    "stay_duration",
                    "contract_type",
                    "cash_price",
                    "notes",
                    "is_cash_package",
                    "is_active",
                ],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result