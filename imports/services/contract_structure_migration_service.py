import pandas as pd
import re
import time
from django.db import transaction
from django.db.models import Prefetch
from collections import Counter, defaultdict

from contracts.models import (
    Contract,
    ContractEntity,
    ContractPackage,
    FinancialCategory,
    PriceList,
)

from medical_catalog.models import Package, Specialty

from imports.utils.import_helpers import ImportHelpers
from imports.services.import_validation_service import (
    ImportValidationService,
)


class ContractStructureMigrationService:

    @staticmethod
    def normalize_company_name(value):
        if pd.isna(value):
            return ""
        return " ".join(
            str(value)
            .replace("\r", " ")
            .replace("\n", " ")
            .split()
        )

    @staticmethod
    def clean_date(value):
        if pd.isna(value):
            return None
        if value in ("", None):
            return None
        try:
            date = pd.to_datetime(
                value,
                dayfirst=True,
                errors="coerce",
            )
            if pd.isna(date):
                return None
            return date.date()
        except Exception:
            return None

    @staticmethod
    def clean_decimal(value):
        if pd.isna(value):
            return None
        if value in ("", None):
            return None
        try:
            value = str(value).strip()
            value = value.replace(" ", "")
            value = value.replace(",", "")
            value = value.replace("٬", "")
            value = value.replace("٫", ".")
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def clean_percentage(value):
        value = ContractStructureMigrationService.clean_decimal(value)
        if value is None:
            return None
        if value <= 1:
            value *= 100
        return value

    @staticmethod
    def clean_discount_text(value):
        if pd.isna(value):
            return None
        text = str(value).strip()
        if not text:
            return None
        try:
            number = float(text)
            if number <= 1:
                number *= 100
            if number.is_integer():
                return f"{int(number)}%"
            return f"{number:.1f}%"
        except ValueError:
            return text

    @staticmethod
    def normalize_package_codes(value):
        if pd.isna(value):
            return []
        value = str(value).strip()
        if not value:
            return []
        codes = re.split(r"[\n\r,،;/]+", value)
        return [code.strip() for code in codes if code.strip()]

    @staticmethod
    def get_or_create_entity(company_name, entities_cache, result):
        key = ImportHelpers.normalize_text(company_name)
        entity = entities_cache.get(key)
        if entity:
            result["existing_entities"] += 1
            return entity
        entity = ContractEntity.objects.create(name=company_name)
        entities_cache[key] = entity
        result["created_entities"] += 1
        return entity

    @staticmethod
    def get_or_create_financial_category(
        entity, financial_code, financial_categories_cache, result
    ):
        key = (entity.id, ImportHelpers.normalize_text(financial_code))
        financial_category = financial_categories_cache.get(key)
        if financial_category:
            result["existing_financial_categories"] += 1
            return financial_category
        financial_category = FinancialCategory.objects.create(
            entity=entity,
            code=financial_code,
            description=None,
            is_active=True,
        )
        financial_categories_cache[key] = financial_category
        result["created_financial_categories"] += 1
        return financial_category

    @staticmethod
    def get_parent_company_name(company_name):
        if "(" in company_name:
            return company_name.split("(")[0].strip()
        return company_name

    @staticmethod
    def get_parent_contract(company_name, contracts_cache):
        parent_name = ContractStructureMigrationService.get_parent_company_name(
            company_name
        )
        return contracts_cache.get(parent_name)

    @staticmethod
    def get_or_create_contract_cached(
        entity,
        financial_category,
        company_name,
        contracts_cache,
        contracts_cache_full,
        default_price_list,
        result,
    ):
        contract_key = (entity.id, financial_category.id)
        contract = contracts_cache_full.get(contract_key)
        if contract:
            result["existing_contracts"] += 1
            return contract
        parent_contract = ContractStructureMigrationService.get_parent_contract(
            company_name, contracts_cache
        )
        contract = Contract.objects.create(
            entity=entity,
            financial_category=financial_category,
            price_list=parent_contract.price_list if parent_contract else default_price_list,
            contract_type=parent_contract.contract_type if parent_contract else None,
            effective_from=parent_contract.effective_from if parent_contract else None,
            is_active=parent_contract.is_active if parent_contract else True,
            notes=parent_contract.notes if parent_contract else "",
        )
        contracts_cache_full[contract_key] = contract
        result["created_contracts"] += 1
        return contract

    @staticmethod
    def _get_or_create_package(
        entity,
        package_codes,
        package_name,
        packages_cache,
        specialty,
        result,
    ):
        package = None
        normalized_name = ImportHelpers.normalize_text(package_name)

        for code in package_codes:
            key = (
                ImportHelpers.normalize_text(code),
                entity.id,
                normalized_name,
            )
            package = packages_cache.get(key)
            if package:
                return package

        first_code = package_codes[0] if package_codes else None
        package, created = Package.objects.get_or_create(
            entity=entity,
            code=first_code,
            name=package_name,
            defaults={
                "specialty": specialty,
                "is_active": True,
            },
        )

        for code in package_codes:
            key = (
                ImportHelpers.normalize_text(code),
                entity.id,
                normalized_name,
            )
            packages_cache[key] = package

        if created:
            result["created_packages"] += 1

        return package

    @staticmethod
    def migrate(dataframe):
        start_time = time.perf_counter()
        print("⏳ Starting migration...")

        # ============================================================
        # ✅ Cache للباكدجات
        # ============================================================
        print("⏳ Loading packages...")
        packages_cache = {}
        for p in Package.objects.exclude(code__isnull=True).iterator(chunk_size=500):
            key = (
                ImportHelpers.normalize_text(p.code),
                p.entity_id if p.entity_id else None,
                ImportHelpers.normalize_text(p.name),
            )
            packages_cache[key] = p
        print(f"   ✅ {len(packages_cache)} packages loaded")

        # ============================================================
        # ✅ Cache للـ Entity
        # ============================================================
        print("⏳ Loading entities...")
        entities_cache = {
            ImportHelpers.normalize_text(e.name): e
            for e in ContractEntity.objects.all()
        }
        print(f"   ✅ {len(entities_cache)} entities loaded")

        # ============================================================
        # ✅ Cache للتخصصات
        # ============================================================
        print("⏳ Loading specialties...")
        specialties_cache = {
            ImportHelpers.normalize_text(s.name): s
            for s in Specialty.objects.all()
        }
        print(f"   ✅ {len(specialties_cache)} specialties loaded")

        # ============================================================
        # ✅ Cache للـ FinancialCategory
        # ============================================================
        print("⏳ Loading financial categories...")
        financial_categories_cache = {
            (fc.entity_id, ImportHelpers.normalize_text(fc.code)): fc
            for fc in FinancialCategory.objects.all()
        }
        print(f"   ✅ {len(financial_categories_cache)} financial categories loaded")

        # ============================================================
        # ✅ Cache للعقود
        # ============================================================
        print("⏳ Loading contracts...")
        contracts_cache = {
            c.entity.name: c
            for c in Contract.objects.select_related("entity", "price_list")
        }
        print(f"   ✅ {len(contracts_cache)} contracts loaded")

        contracts_cache_full = {
            (c.entity_id, c.financial_category_id): c
            for c in Contract.objects.select_related("entity", "price_list").all()
        }
        print(f"   ✅ {len(contracts_cache_full)} contracts (full cache) loaded")

        # ============================================================
        # ✅ Cache كامل لـ ContractPackage (بدون select_related)
        # ============================================================
        print("⏳ Loading contract packages into cache...")
        contract_packages_cache = {
            (cp.contract_id, cp.package_id): cp
            for cp in ContractPackage.objects.iterator(chunk_size=1000)
        }
        print(f"   ✅ {len(contract_packages_cache)} contract packages cached")

        # ============================================================
        # ✅ Default Price List
        # ============================================================
        default_price_list, _ = PriceList.objects.get_or_create(
            name="DATA IMPORT",
            defaults={"is_active": True},
        )

        result = {
            "processed": 0,
            "created_entities": 0,
            "existing_entities": 0,
            "created_financial_categories": 0,
            "existing_financial_categories": 0,
            "created_contracts": 0,
            "existing_contracts": 0,
            "created_packages": 0,
            "created_contract_packages": 0,
            "updated_packages": 0,
            "package_not_found": 0,
            "missing_codes": set(),
            "missing_price": 0,
            "deleted_contract_packages": 0,
            "skipped_invalid_company": 0,
            "skipped_invalid_package": 0,
            "skipped_invalid_code": 0,
        }

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        contract_packages_to_create = []
        contract_packages_to_update = []
        contract_package_keys_in_sheet = set()

        # ============================================================
        # ✅ المعالجة
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        chunk_size = 1000  # ✅ تم التعديل من 200 إلى 1000
        for chunk_start in range(0, total_rows, chunk_size):
            chunk_end = min(chunk_start + chunk_size, total_rows)
            chunk = dataframe.iloc[chunk_start:chunk_end]
            chunk_data = chunk.to_dict("records")

            for row in chunk_data:
                company_name = ContractStructureMigrationService.normalize_company_name(
                    row.get(0, "")
                )

                package_codes = ImportValidationService.valid_package_codes(
                    ContractStructureMigrationService.normalize_package_codes(
                        row.get(6, "")
                    )
                )

                package_name = ImportHelpers.normalize_text(row.get(2, ""))
                financial_code = ImportHelpers.normalize_text(row.get(1, ""))
                specialty_name = ImportHelpers.normalize_text(row.get(3, ""))

                if not ImportValidationService.has_company(company_name):
                    result.setdefault("skipped_invalid_company", 0)
                    result["skipped_invalid_company"] += 1
                    continue

                if not ImportValidationService.has_package_name(package_name):
                    result.setdefault("skipped_invalid_package", 0)
                    result["skipped_invalid_package"] += 1
                    continue

                if not package_codes:
                    result.setdefault("skipped_invalid_code", 0)
                    result["skipped_invalid_code"] += 1
                    continue

                result["processed"] += 1

                entity = ContractStructureMigrationService.get_or_create_entity(
                    company_name, entities_cache, result
                )

                if not financial_code:
                    financial_code = "DEFAULT"

                financial_category = ContractStructureMigrationService.get_or_create_financial_category(
                    entity, financial_code, financial_categories_cache, result
                )

                contract = ContractStructureMigrationService.get_or_create_contract_cached(
                    entity,
                    financial_category,
                    company_name,
                    contracts_cache,
                    contracts_cache_full,
                    default_price_list,
                    result,
                )

                specialty = specialties_cache.get(
                    ImportHelpers.normalize_text(specialty_name)
                )
                if not specialty:
                    specialty = Specialty.objects.first()

                package = ContractStructureMigrationService._get_or_create_package(
                    entity=entity,
                    package_codes=package_codes,
                    package_name=package_name,
                    packages_cache=packages_cache,
                    specialty=specialty,
                    result=result,
                )

                price = ContractStructureMigrationService.clean_decimal(
                    row.get(4, None)
                )
                if price is None:
                    price = ContractStructureMigrationService.clean_decimal(
                        row.get(10, None)
                    )
                if price is None:
                    price = ContractStructureMigrationService.clean_decimal(
                        row.get(16, None)
                    )
                if price is None:
                    price = 0
                    result["missing_price"] += 1

                defaults = {
                    "package_price": price,
                    "total_before_discount": ContractStructureMigrationService.clean_decimal(
                        row.get(10, None)
                    ),
                    "current_discount_rate": ContractStructureMigrationService.clean_percentage(
                        row.get(12, None)
                    ),
                    "current_discount_text": ContractStructureMigrationService.clean_discount_text(
                        row.get(12, None)
                    ),
                    "cash_price": ContractStructureMigrationService.clean_decimal(
                        row.get(16, None)
                    ),
                    "special_offer_price": ContractStructureMigrationService.clean_decimal(
                        row.get(14, None)
                    ),
                    "special_offer_company": (row.get(15, "") or ""),
                    "price_list_applied": row.get(13, None),
                    "effective_from": ContractStructureMigrationService.clean_date(
                        row.get(7, None)
                    ),
                    "valid_until": ContractStructureMigrationService.clean_date(
                        row.get(8, None)
                    ),
                    "notes": row.get(9, None),
                    "approval_pdf": row.get(19, None),
                    "is_active": True,
                    "suggested_price": ContractStructureMigrationService.clean_decimal(
                        row.get(18, None)
                    ),
                    "suggested_discount_rate": ContractStructureMigrationService.clean_percentage(
                        row.get(17, None)
                    ),
                }

                contract_package_key = (contract.id, package.id)
                contract_package_keys_in_sheet.add(contract_package_key)

                # ✅ البحث في Cache مباشرة - بدون أي Query
                contract_package = contract_packages_cache.get(contract_package_key)

                if contract_package:
                    changed = False
                    for field, value in defaults.items():
                        if getattr(contract_package, field) != value:
                            setattr(contract_package, field, value)
                            changed = True

                    if changed:
                        contract_packages_to_update.append(contract_package)
                        result["updated_packages"] += 1

                else:
                    contract_package = ContractPackage(
                        contract=contract,
                        package=package,
                        **defaults,
                    )

                    # ✅ نضيف للـ Cache عشان لو تكرر في نفس الجلسة
                    contract_packages_cache[contract_package_key] = contract_package
                    contract_packages_to_create.append(contract_package)
                    result["created_contract_packages"] += 1

                processed += 1
                if processed % 1000 == 0:
                    print(f"   📊 Processed {processed}/{total_rows} rows...")

                # ✅ Bulk Create كل 500 صف
                if len(contract_packages_to_create) >= 500:
                    ContractPackage.objects.bulk_create(
                        contract_packages_to_create,
                        batch_size=500,
                        ignore_conflicts=True,
                    )
                    contract_packages_to_create = []

                # ✅ Bulk Update كل 500 صف
                if len(contract_packages_to_update) >= 500:
                    valid_updates = [cp for cp in contract_packages_to_update if cp.id]
                    if valid_updates:
                        ContractPackage.objects.bulk_update(
                            valid_updates,
                            fields=[
                                "package_price",
                                "total_before_discount",
                                "current_discount_rate",
                                "current_discount_text",
                                "cash_price",
                                "special_offer_price",
                                "special_offer_company",
                                "price_list_applied",
                                "effective_from",
                                "valid_until",
                                "notes",
                                "approval_pdf",
                                "is_active",
                                "suggested_price",
                                "suggested_discount_rate",
                            ],
                            batch_size=500,
                        )
                    contract_packages_to_update = []

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ المتبقي
        # ============================================================
        if contract_packages_to_create:
            ContractPackage.objects.bulk_create(
                contract_packages_to_create,
                batch_size=500,
                ignore_conflicts=True,
            )
            contract_packages_to_create = []

        if contract_packages_to_update:
            valid_updates = [cp for cp in contract_packages_to_update if cp.id]
            if valid_updates:
                ContractPackage.objects.bulk_update(
                    valid_updates,
                    fields=[
                        "package_price",
                        "total_before_discount",
                        "current_discount_rate",
                        "current_discount_text",
                        "cash_price",
                        "special_offer_price",
                        "special_offer_company",
                        "price_list_applied",
                        "effective_from",
                        "valid_until",
                        "notes",
                        "approval_pdf",
                        "is_active",
                        "suggested_price",
                        "suggested_discount_rate",
                    ],
                    batch_size=500,
                )

        # ============================================================
        # ✅ حذف ContractPackages غير الموجودة في الشيت
        # ============================================================
        if contract_package_keys_in_sheet:
            all_keys = set(contract_packages_cache.keys())
            keys_to_delete = all_keys - contract_package_keys_in_sheet

            if keys_to_delete:
                ids_to_delete = []
                for key in keys_to_delete:
                    cp = contract_packages_cache.get(key)
                    if cp and cp.id:
                        ids_to_delete.append(cp.id)

                if ids_to_delete:
                    deleted_count = ContractPackage.objects.filter(
                        id__in=ids_to_delete
                    ).delete()[0]
                    if deleted_count > 0:
                        print(f"🗑️ Deleted {deleted_count} contract packages not in sheet")
                        result["deleted_contract_packages"] = deleted_count
        else:
            print("⚠️ No contract packages in sheet - skipping deletion to avoid data loss")

        result["missing_codes"] = sorted(list(result["missing_codes"]))

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result