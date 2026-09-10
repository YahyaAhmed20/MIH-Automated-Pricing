# imports/services/cash_package_import_service.py

import time
from decimal import Decimal

from django.db import transaction

from medical_catalog.models import Package, Specialty
from imports.utils.import_helpers import ImportHelpers


class CashPackageImportService:

    @staticmethod
    def truncate_text(value, max_length=255, counters=None):
        """تقليص النص إذا تجاوز الحد الأقصى بدون إغراق الـ logs."""
        if not value:
            return value

        cleaned = ImportHelpers.normalize_text(value)

        if len(cleaned) > max_length:
            if counters is not None:
                counters["truncated_texts"] += 1

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
            "missing_code": 0,
            "missing_name": 0,
            "truncated_texts": 0,
        }

        # ============================================================
        # Cache للـ Specialties
        # ============================================================
        print("⏳ Loading specialties...")

        specialties_cache = {}

        for s in Specialty.objects.all():
            specialties_cache[
                ImportHelpers.normalize_text(s.name)
            ] = s

        print(
            f"   ✅ {len(specialties_cache)} specialties loaded"
        )

        # ============================================================
        # Cache للـ Packages - باستخدام code فقط
        # ============================================================
        print("⏳ Loading packages...")

        packages_cache = {}

        for p in Package.objects.exclude(code__isnull=True):
            key = ImportHelpers.normalize_text(p.code)
            packages_cache[key] = p

        print(
            f"   ✅ {len(packages_cache)} packages loaded"
        )

        # ============================================================
        # قوائم التجميع للـ Bulk Operations
        # ============================================================
        packages_to_create = []
        packages_to_update = []

        sheet_codes = set()
        seen_keys = set()

        # ============================================================
        # Processing
        # ============================================================
        print("⏳ Processing rows...")

        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(
            dataframe.to_dict("records"),
            start=1,
        ):

            # ========================================================
            # أعمدة شيت 2
            # ========================================================

            package_name = ImportHelpers.normalize_text(
                row.get(0, "")
            )

            package_name = CashPackageImportService.truncate_text(
                package_name,
                255,
                result,
            )

            contract_type = ImportHelpers.normalize_text(
                row.get(1, "")
            )

            contract_type = CashPackageImportService.truncate_text(
                contract_type,
                255,
                result,
            )

            specialty_name = ImportHelpers.normalize_text(
                row.get(2, "")
            )

            specialty_name = CashPackageImportService.truncate_text(
                specialty_name,
                255,
                result,
            )

            if not specialty_name:
                specialty_name = "نقدي"
                result["missing_specialty"] += 1

            stay_duration = ImportHelpers.normalize_text(
                row.get(3, "")
            )

            package_code = ImportHelpers.normalize_text(
                row.get(4, "")
            )

            package_code = CashPackageImportService.truncate_text(
                package_code,
                50,
                result,
            )

            cash_price = ImportHelpers.clean_decimal(
                row.get(5, None)
            )

            if cash_price is None:
                cash_price = Decimal("0.00")

            notes = ImportHelpers.normalize_text(
                row.get(6, "")
            )

            notes = CashPackageImportService.truncate_text(
                notes,
                255,
                result,
            )

            # ========================================================
            # Missing values
            # ========================================================

            if not package_code:
                package_code = f"UNKNOWN_{index}"
                result["missing_code"] += 1

            if not package_name:
                package_name = f"بدون اسم {index}"
                result["missing_name"] += 1

            # هذه الحالة أصبحت غير ممكنة عمليًا لأننا وضعنا defaults
            if not package_code and not package_name:
                result["skipped"] = result.get("skipped", 0) + 1
                continue

            # ========================================================
            # منع التكرار داخل الشيت
            # ========================================================

            package_key = package_code

            if package_key in seen_keys:
                result["skipped_duplicates"] += 1
                continue

            seen_keys.add(package_key)
            sheet_codes.add(package_code)

            result["processed"] += 1
            processed = result["processed"]

            # ========================================================
            # Specialty
            # ========================================================

            specialty = specialties_cache.get(
                specialty_name
            )

            if not specialty:
                specialty = Specialty.objects.create(
                    name=specialty_name,
                    is_active=True,
                )

                specialties_cache[specialty_name] = specialty
                result["created_specialties"] += 1

            # ========================================================
            # Package
            # ========================================================

            existing_package = packages_cache.get(
                package_key
            )

            if existing_package:

                changed = False

                if existing_package.name != package_name:
                    existing_package.name = package_name
                    changed = True

                if existing_package.specialty_id != (
                    specialty.id if specialty else None
                ):
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
                    packages_to_update.append(
                        existing_package
                    )

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

                packages_to_create.append(
                    new_package
                )

                packages_cache[package_key] = new_package

                result["created"] += 1

            # ========================================================
            # Progress - مرة كل 1000 صف فقط
            # ========================================================

            if processed % 1000 == 0:
                print(
                    f"   📊 Processed "
                    f"{processed}/{total_rows} rows..."
                )

        # ============================================================
        # Summary
        # ============================================================

        print(
            f"   ✅ Processed "
            f"{processed}/{total_rows} rows"
        )

        print(
            f"   ⏭️ Skipped "
            f"{result['skipped_duplicates']} duplicate keys in sheet"
        )

        if result["missing_specialty"] > 0:
            print(
                f"   ⚠️ Missing specialty: "
                f"{result['missing_specialty']} rows "
                f"(defaulted to 'نقدي')"
            )

        if result["missing_code"] > 0:
            print(
                f"   ⚠️ Missing package code: "
                f"{result['missing_code']} rows "
                f"(default codes generated)"
            )

        if result["missing_name"] > 0:
            print(
                f"   ⚠️ Missing package name: "
                f"{result['missing_name']} rows "
                f"(default names generated)"
            )

        if result["truncated_texts"] > 0:
            print(
                f"   ⚠️ Truncated text values: "
                f"{result['truncated_texts']}"
            )

        # ============================================================
        # حذف الباكدجات النقدية فقط
        # ============================================================

        if sheet_codes:

            deleted_count, _ = Package.objects.filter(
                is_cash_package=True
            ).exclude(
                code__in=sheet_codes
            ).delete()

            if deleted_count > 0:

                print(
                    f"🗑️ Deleted "
                    f"{deleted_count} cash packages not in sheet"
                )

                result["deleted"] = deleted_count

        else:

            print(
                "⚠️ No codes in sheet - "
                "skipping deletion to avoid data loss"
            )

        # ============================================================
        # Bulk Operations
        # ============================================================

        print(
            f"💾 Creating "
            f"{len(packages_to_create)} packages..."
        )

        print(
            f"💾 Updating "
            f"{len(packages_to_update)} packages..."
        )

        if packages_to_create:

            Package.objects.bulk_create(
                packages_to_create,
                batch_size=1000,
            )

        if packages_to_update:

            Package.objects.bulk_update(
                packages_to_update,
                fields=[
                    "name",
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

        print(
            f"✅ Completed in "
            f"{elapsed:.2f} seconds"
        )

        return result