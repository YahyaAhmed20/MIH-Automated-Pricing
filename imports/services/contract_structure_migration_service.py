import pandas as pd
import re
import time
from django.db import transaction
from django.db.models import Prefetch

from contracts.models import (
    Contract,
    ContractEntity,
    ContractPackage,
    FinancialCategory,
    PriceList,
)

from medical_catalog.models import Package

# ============================================================
# ✅ استيراد ImportHelpers
# ============================================================
from imports.utils.import_helpers import ImportHelpers


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

    # ============================================================
    # ✅ Helper: معالجة التواريخ
    # ============================================================
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

    # ============================================================
    # ✅ Helper: معالجة الأرقام
    # ============================================================
    @staticmethod
    def clean_decimal(value):

        if pd.isna(value):
            return None

        if value in ("", None):
            return None

        try:

            value = str(value).strip()

            # إزالة المسافات
            value = value.replace(" ", "")

            # إزالة فواصل الآلاف
            value = value.replace(",", "")
            value = value.replace("٬", "")

            # تحويل العلامة العشرية العربية
            value = value.replace("٫", ".")

            return float(value)

        except (ValueError, TypeError):

            return None

    # ============================================================
    # ✅ Helper: معالجة النسب المئوية
    # ============================================================
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

    # ============================================================
    # ✅ Helper: تنظيف أكواد الباكدجات
    # ============================================================
    @staticmethod
    def normalize_package_codes(value):
        if pd.isna(value):
            return []
        value = str(value).strip()
        if not value:
            return []
        codes = re.split(r"[\n\r,،;/]+", value)
        return [code.strip() for code in codes if code.strip()]

    # ============================================================
    # ✅ الخطوة 1: get_or_create_entity - مع Cache
    # ============================================================
    @staticmethod
    def get_or_create_entity(
        company_name,
        entities_cache,
        result,
    ):

        key = ImportHelpers.normalize_text(company_name)

        entity = entities_cache.get(key)

        if entity:
            result["existing_entities"] += 1
            return entity

        entity = ContractEntity.objects.create(
            name=company_name
        )

        entities_cache[key] = entity

        result["created_entities"] += 1

        return entity

    # ============================================================
    # ✅ الخطوة 2: get_or_create_financial_category - مع Cache
    # ============================================================
    @staticmethod
    def get_or_create_financial_category(
        entity,
        financial_code,
        financial_categories_cache,
        result,
    ):

        key = (
            entity.id,
            ImportHelpers.normalize_text(financial_code),
        )

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

    # ============================================================
    # ✅ get_parent_company_name
    # ============================================================
    @staticmethod
    def get_parent_company_name(company_name):
        if "(" in company_name:
            return company_name.split("(")[0].strip()
        return company_name

    # ============================================================
    # ✅ get_parent_contract
    # ============================================================
    @staticmethod
    def get_parent_contract(company_name, contracts_cache):
        parent_name = (
            ContractStructureMigrationService.get_parent_company_name(
                company_name
            )
        )
        return contracts_cache.get(parent_name)

    # ============================================================
    # ✅ get_or_create_contract_cached - نسخة محسنة مع Cache
    # ============================================================
    @staticmethod
    def get_or_create_contract_cached(
        entity,
        financial_category,
        company_name,
        contracts_cache,
        contracts_cache_full,
        default_price_list,
        result
    ):
        """إصدار محسن يستخدم Cache بدلاً من get_or_create"""

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

    # ============================================================
    # ✅ migrate() - المعدل مع Cache و Bulk Operations
    # ============================================================
    @staticmethod
    @transaction.atomic
    def migrate(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting migration...")

        # ✅ ✅ ✅ Cache للباكدجات - استخدام package_lookup_key
        print("⏳ Loading packages...")
        packages_cache = {}
        for p in Package.objects.exclude(code__isnull=True).iterator(chunk_size=1000):
            key = ImportHelpers.package_lookup_key(p.code, p.name)
            packages_cache[key] = p
        print(f"   ✅ {len(packages_cache)} packages loaded")

        # ✅ Cache للـ Entity
        print("⏳ Loading entities...")
        entities_cache = {
            ImportHelpers.normalize_text(e.name): e
            for e in ContractEntity.objects.all()
        }
        print(f"   ✅ {len(entities_cache)} entities loaded")

        # ✅ Cache للـ FinancialCategory
        print("⏳ Loading financial categories...")
        financial_categories_cache = {
            (
                fc.entity_id,
                ImportHelpers.normalize_text(fc.code),
            ): fc
            for fc in FinancialCategory.objects.all()
        }
        print(f"   ✅ {len(financial_categories_cache)} financial categories loaded")

        # ✅ Cache للعقود (للـ Parent)
        print("⏳ Loading contracts...")
        contracts_cache = {
            c.entity.name: c
            for c in Contract.objects.select_related(
                "entity",
                "price_list"
            )
        }
        print(f"   ✅ {len(contracts_cache)} contracts loaded")

        # ✅ Cache كامل للعقود (للتخلص من get_or_create)
        contracts_cache_full = {
            (c.entity_id, c.financial_category_id): c
            for c in Contract.objects.select_related('entity', 'price_list').all()
        }
        print(f"   ✅ {len(contracts_cache_full)} contracts (full cache) loaded")

        # ✅ Cache لـ ContractPackage
        print("⏳ Loading contract packages...")
        contract_packages_cache = {
            (
                cp.contract_id,
                cp.package_id,
            ): cp
            for cp in ContractPackage.objects.all()
        }
        print(f"   ✅ {len(contract_packages_cache)} contract packages loaded")

        # ✅ Default Price List
        default_price_list, _ = PriceList.objects.get_or_create(
            name="DATA IMPORT",
            defaults={
                "is_active": True,
            },
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
            "updated_packages": 0,
            "package_not_found": 0,
            "missing_codes": set(),
            "missing_price": 0,
        }

        # ✅ قوائم التجميع للـ Bulk Operations
        contract_packages_to_create = []
        contract_packages_to_update = []

        # ✅ تشغيل على كل الصفوف - استخدام to_dict("records")
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        # ✅ استخدام أرقام الأعمدة (بدون Header)
        for row in dataframe.to_dict("records"):

            # ✅ العمود 0: الشركه
            company_name = ContractStructureMigrationService.normalize_company_name(
                row.get(0, "")
            )

            # ✅ العمود 6: الكود
            package_codes = ContractStructureMigrationService.normalize_package_codes(
                row.get(6, "")
            )

            # ✅ العمود 2: اسم الباكدج
            package_name = ImportHelpers.normalize_text(
                row.get(2, "")
            )

            # ✅ العمود 1: نوع التعاقد (الفئة المالية)
            financial_code = ImportHelpers.normalize_text(
                row.get(1, "")
            )

            if not company_name or not package_codes:
                continue

            result["processed"] += 1

            # ============================================================
            # ✅ Entity - باستخدام Cache
            # ============================================================
            entity = ContractStructureMigrationService.get_or_create_entity(
                company_name,
                entities_cache,
                result,
            )

            # ============================================================
            # ✅ Financial Category - باستخدام Cache
            # ============================================================
            if not financial_code:
                financial_code = "DEFAULT"

            financial_category = ContractStructureMigrationService.get_or_create_financial_category(
                entity,
                financial_code,
                financial_categories_cache,
                result,
            )

            # ============================================================
            # ✅ Contract - باستخدام Cache (بدون get_or_create)
            # ============================================================
            contract = ContractStructureMigrationService.get_or_create_contract_cached(
                entity,
                financial_category,
                company_name,
                contracts_cache,
                contracts_cache_full,
                default_price_list,
                result
            )

            # ============================================================
            # ✅ Package Lookup
            # ============================================================
            package = None

            for code in package_codes:
                key = ImportHelpers.package_lookup_key(code, package_name)
                package = packages_cache.get(key)
                if package:
                    break

            if not package:
                result["package_not_found"] += 1
                for code in package_codes:
                    result["missing_codes"].add(code)
                continue

            # ============================================================
            # ✅ Price - استخدام قيم افتراضية
            # ============================================================
            price = ContractStructureMigrationService.clean_decimal(
                row.get(4, None)  # ✅ العمود 4: السعر
            )

            # ✅ إذا كان السعر فارغاً، استخدم الاجمالي (العمود 10)
            if price is None:
                price = ContractStructureMigrationService.clean_decimal(
                    row.get(10, None)
                )

            # ✅ إذا كان الاجمالي فارغاً، استخدم النقدي (العمود 16)
            if price is None:
                price = ContractStructureMigrationService.clean_decimal(
                    row.get(16, None)
                )

            # ✅ إذا كان كل شيء فارغاً، استخدم 0 كقيمة افتراضية
            if price is None:
                price = 0
                result["missing_price"] += 1

            # ============================================================
            # ✅ ContractPackage - باستخدام Bulk بدلاً من update_or_create
            # ============================================================
            defaults = {
                "package_price": price,
                "total_before_discount": ContractStructureMigrationService.clean_decimal(
                    row.get(10, None)  # ✅ العمود 10: الاجمالي
                ),
                "current_discount_rate": ContractStructureMigrationService.clean_percentage(
                    row.get(12, None)  # ✅ العمود 12: معدل الخصم الحالي
                ),
                "current_discount_text": ContractStructureMigrationService.clean_discount_text(
                    row.get(12, None)
                ),
                "cash_price": ContractStructureMigrationService.clean_decimal(
                    row.get(16, None)  # ✅ العمود 16: النقدي
                ),
                "special_offer_price": ContractStructureMigrationService.clean_decimal(
                    row.get(14, None)  # ✅ العمود 14: Special Offer
                ),
                "special_offer_company": (
                    row.get(15, "") or ""  # ✅ العمود 15: الشركه.1
                ),
                "price_list_applied": row.get(13, None),  # ✅ العمود 13: قائمة الاسعار
                "effective_from": ContractStructureMigrationService.clean_date(
                    row.get(7, None)  # ✅ العمود 7: اعتبارا من
                ),
                "valid_until": ContractStructureMigrationService.clean_date(
                    row.get(8, None)  # ✅ العمود 8: ساري حتي
                ),
                "notes": row.get(9, None),  # ✅ العمود 9: ملاحظات الباكدج
                "approval_pdf": row.get(19, None),  # ✅ العمود 19: مشتملات الباكدج
                "is_active": True,
                "suggested_price": ContractStructureMigrationService.clean_decimal(
                    row.get(18, None)  # ✅ العمود 18: السعر المقترح
                ),
                "suggested_discount_rate": ContractStructureMigrationService.clean_percentage(
                    row.get(17, None)  # ✅ العمود 17: معدل الخصم المقترح
                ),
            }

            key = (contract.id, package.id)
            contract_package = contract_packages_cache.get(key)

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

                contract_packages_to_create.append(contract_package)
                contract_packages_cache[key] = contract_package
                result["created_packages"] += 1

            processed += 1
            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ✅ تنفيذ الـ Bulk Operations
        print(f"💾 Creating {len(contract_packages_to_create)} ContractPackages...")
        print(f"💾 Updating {len(contract_packages_to_update)} ContractPackages...")

        if contract_packages_to_create:
            ContractPackage.objects.bulk_create(
                contract_packages_to_create,
                batch_size=1000,
            )

        if contract_packages_to_update:
            ContractPackage.objects.bulk_update(
                contract_packages_to_update,
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
                batch_size=1000,
            )

        # ✅ تحويل set إلى list مرتب
        result["missing_codes"] = sorted(list(result["missing_codes"]))

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result