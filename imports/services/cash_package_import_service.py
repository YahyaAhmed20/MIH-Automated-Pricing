import pandas as pd
from django.db import transaction
from imports.utils.import_helpers import ImportHelpers
from medical_catalog.models import Package, Specialty


class CashPackageImportService:

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

        # ==========================================
        # Cache
        # ==========================================

        specialties_cache = {
            s.name: s
            for s in Specialty.objects.all()
        }

        packages_cache = {
            (
                ImportHelpers.normalize_text(p.code),
                ImportHelpers.normalize_text(p.name),
            ): p
            for p in Package.objects.exclude(code__isnull=True)
        }

        # ==========================================
        # Loop
        # ==========================================

        for _, row in dataframe.iterrows():

            package_code = ImportHelpers.normalize_text(
                row.get("الكود")
            )

            package_name = ImportHelpers.normalize_text(
                row.get("الباكدجات")
            )

            contract_type = ImportHelpers.normalize_text(
                row.get("نوع التعاقد")
            )

            specialty_name = ImportHelpers.normalize_text(
                row.get("التخصص")
            )

            stay_duration = ImportHelpers.normalize_text(
                row.get("مدة الاقامه")
            )

            notes = ImportHelpers.normalize_text(
                row.get("ملاحظات")
            )

            cash_price = ImportHelpers.clean_decimal(
                row.get("السعر")
            )

            if not package_code or not package_name:
                continue

            result["processed"] += 1

            specialty = ImportHelpers.get_or_create_specialty(
                specialty_name,
                specialties_cache,
                result,
            )

            package_key = (
                package_code,
                package_name,
            )

            package = packages_cache.get(package_key)

            if package:

                package.specialty = specialty
                package.stay_duration = stay_duration
                package.contract_type = contract_type
                package.cash_price = cash_price
                package.notes = notes
                package.is_cash_package = True
                package.is_active = True

                package.save()

                result["updated"] += 1

            else:

                package = Package.objects.create(
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

                packages_cache[package_key] = package

                result["created"] += 1

        return result