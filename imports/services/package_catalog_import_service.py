import pandas as pd

from django.db import transaction
from imports.utils.import_helpers import ImportHelpers
from medical_catalog.models import (
    Package,
    Specialty,
)


class PackageCatalogImportService:

    # ❌ 2) حذف الدالة normalize_text بالكامل
    # @staticmethod
    # def normalize_text(value):
    #     ...

    # ============================================================
    # ✅ Helper: جلب أو إنشاء التخصص
    # ============================================================
    @staticmethod
    def get_specialty(
        specialty_name,
        specialties_cache,
        result
    ):

        specialty_name = (
            ImportHelpers.normalize_text(  # ✅ استخدم ImportHelpers
                specialty_name
            )
        )

        if not specialty_name:
            result["missing_specialty"] += 1
            return None

        specialty = specialties_cache.get(
            specialty_name
        )

        if specialty:
            return specialty

        specialty = Specialty.objects.create(
            name=specialty_name,
            is_active=True
        )

        specialties_cache[specialty_name] = specialty

        result["created_specialties"] += 1

        return specialty

    # ============================================================
    # ✅ Import Data (مع الـ Result)
    # ============================================================
    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "created_specialties": 0,
            "missing_specialty": 0,
        }

        # ✅ جيب كل التخصصات في Cache
        specialties_cache = {
            s.name: s
            for s in Specialty.objects.all()
        }

        # ✅ 3) تعديل packages_cache بالمفتاح المركب (code, name)
        packages_cache = {
            (
                ImportHelpers.normalize_text(p.code),  # ✅ code
                ImportHelpers.normalize_text(p.name),  # ✅ name
            ): p
            for p in Package.objects.exclude(
                code__isnull=True
            )
        }

        for _, row in dataframe.iterrows():

            # ✅ 4) استخدام ImportHelpers.normalize_text لكل القراءات
            package_code = (
                ImportHelpers.normalize_text(  # ✅
                    row.get("الكود")
                )
            )

            package_name = (
                ImportHelpers.normalize_text(  # ✅
                    row.get("اسم الباكدج")
                )
            )

            specialty_name = (
                ImportHelpers.normalize_text(  # ✅
                    row.get("التخصص")
                )
            )

            stay_duration = (
                ImportHelpers.normalize_text(  # ✅
                    row.get("مدة الاقامه")
                )
            )

            package_note = (
                ImportHelpers.normalize_text(  # ✅
                    row.get("ملاحظات الباكدج")
                )
            )

            if not package_code or not package_name:
                continue

            result["processed"] += 1

            specialty = (
                PackageCatalogImportService.get_specialty(
                    specialty_name,
                    specialties_cache,
                    result
                )
            )

            # ✅ 5) البحث بالمفتاح المركب (code, name)
            package_key = (
                package_code,
                package_name,
            )

            package = packages_cache.get(package_key)

            if package:

                package.name = package_name
                package.specialty = specialty
                package.stay_duration = stay_duration
                package.package_note = package_note
                package.is_active = True

                package.save()

                result["updated"] += 1

            else:

                package = Package.objects.create(
                    code=package_code,
                    name=package_name,
                    specialty=specialty,
                    stay_duration=stay_duration,
                    package_note=package_note,
                    is_active=True
                )

                # ✅ 6) التخزين في cache بالمفتاح المركب
                packages_cache[package_key] = package

                result["created"] += 1

        return result