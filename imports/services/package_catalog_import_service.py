import pandas as pd

from django.db import transaction

from medical_catalog.models import (
    Package,
    Specialty,
)


class PackageCatalogImportService:

    @staticmethod
    def normalize_text(value):

        if pd.isna(value):
            return ""

        return " ".join(
            str(value)
            .replace("\r", " ")
            .replace("\n", " ")
            .split()
        )

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
            PackageCatalogImportService.normalize_text(
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

        # ✅ جيب كل الباكدجات في Cache
        packages_cache = {
            p.code: p
            for p in Package.objects.exclude(
                code__isnull=True
            )
        }

        for _, row in dataframe.iterrows():

            package_code = (
                PackageCatalogImportService.normalize_text(
                    row.get("الكود")
                )
            )

            package_name = (
                PackageCatalogImportService.normalize_text(
                    row.get("اسم الباكدج")
                )
            )

            specialty_name = (
                PackageCatalogImportService.normalize_text(
                    row.get("التخصص")
                )
            )

            stay_duration = (
                PackageCatalogImportService.normalize_text(
                    row.get("مدة الاقامه")
                )
            )

            package_note = (
                PackageCatalogImportService.normalize_text(
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

            package = packages_cache.get(package_code)

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

                packages_cache[package_code] = package

                result["created"] += 1

        return result