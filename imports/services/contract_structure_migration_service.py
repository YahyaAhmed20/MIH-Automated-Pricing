import pandas as pd
import re
from django.db import transaction

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
        try:
            return pd.to_datetime(value).date()
        except Exception:
            return None

    # ============================================================
    # ✅ Helper: معالجة الأرقام
    # ============================================================
    @staticmethod
    def clean_decimal(value):
        if pd.isna(value):
            return None
        try:
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
    # ✅ الخطوة 1: get_or_create_entity
    # ============================================================
    @staticmethod
    def get_or_create_entity(company_name, result):
        entity, created = ContractEntity.objects.get_or_create(
            name=company_name
        )
        if created:
            result["created_entities"] += 1
        else:
            result["existing_entities"] += 1
        return entity

    # ============================================================
    # ✅ الخطوة 2: get_or_create_financial_category
    # ============================================================
    @staticmethod
    def get_or_create_financial_category(entity, result):
        financial_category, created = (
            FinancialCategory.objects.get_or_create(
                entity=entity,
                code="DEFAULT",
                defaults={
                    "description": None,
                    "is_active": True,
                }
            )
        )
        if created:
            result["created_financial_categories"] += 1
        else:
            result["existing_financial_categories"] += 1
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
    # ✅ get_or_create_contract
    # ============================================================
    @staticmethod
    def get_or_create_contract(
        entity,
        financial_category,
        company_name,
        contracts_cache,
        default_price_list,
        result
    ):
        parent_contract = (
            ContractStructureMigrationService.get_parent_contract(
                company_name,
                contracts_cache
            )
        )
        defaults = {
            "financial_category": financial_category,
            "price_list": (
                parent_contract.price_list
                if parent_contract
                else default_price_list
            ),
            "contract_type": (
                parent_contract.contract_type
                if parent_contract
                else None
            ),
            "effective_from": (
                parent_contract.effective_from
                if parent_contract
                else None
            ),
            "is_active": (
                parent_contract.is_active
                if parent_contract
                else True
            ),
            "notes": (
                parent_contract.notes
                if parent_contract
                else ""
            ),
        }
        contract, created = Contract.objects.get_or_create(
            entity=entity,
            defaults=defaults
        )
        if created:
            result["created_contracts"] += 1
            contracts_cache[entity.name] = contract
        else:
            result["existing_contracts"] += 1
        return contract

    # ============================================================
    # ✅ migrate() - المعدل
    # ============================================================
    @staticmethod
    @transaction.atomic
    def migrate(dataframe):

        # ✅ ✅ ✅ Cache للباكدجات - استخدام package_lookup_key
        packages_cache = {
            ImportHelpers.package_lookup_key(  # ⬅️ استخدام الدالة
                p.code,
                p.name,
            ): p
            for p in Package.objects.select_related('entity').all()
        }

        # ✅ Cache للعقود
        contracts_cache = {
            c.entity.name: c
            for c in Contract.objects.select_related(
                "entity",
                "price_list"
            )
        }

        # ✅ Default Price List
        default_price_list = PriceList.objects.get(
            name="DATA IMPORT"
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
        }

        # ✅ تشغيل على كل الصفوف
        for _, row in dataframe.iterrows():
            ContractStructureMigrationService.sync_row(
                row,
                packages_cache,
                contracts_cache,
                default_price_list,
                result
            )

        # ✅ تحويل set إلى list مرتب
        result["missing_codes"] = sorted(list(result["missing_codes"]))

        return result

    # ============================================================
    # ✅ sync_row() - المعدل بالكامل
    # ============================================================
    @staticmethod
    def sync_row(row, packages_cache, contracts_cache, default_price_list, result):

        # ============================================================
        # ✅ استخراج البيانات من الصف
        # ============================================================
        company_name = (
            ContractStructureMigrationService.normalize_company_name(
                row.get("الشركه")
            )
        )

        # ✅ أكواد الباكدجات
        package_codes = (
            ContractStructureMigrationService.normalize_package_codes(
                row.get("الكود")
            )
        )

        # ✅ اسم الباكدج من الـ row
        package_name = (
            ImportHelpers.normalize_text(
                row.get("اسم الباكدج")
            )
        )

        if not company_name or not package_codes:
            return

        result["processed"] += 1

        # ============================================================
        # ✅ Entity
        # ============================================================
        entity = (
            ContractStructureMigrationService.get_or_create_entity(
                company_name,
                result
            )
        )

        # ============================================================
        # ✅ Financial Category
        # ============================================================
        financial_category = (
            ContractStructureMigrationService.get_or_create_financial_category(
                entity,
                result
            )
        )

        # ============================================================
        # ✅ Contract
        # ============================================================
        contract = (
            ContractStructureMigrationService.get_or_create_contract(
                entity,
                financial_category,
                company_name,
                contracts_cache,
                default_price_list,
                result
            )
        )

        # ============================================================
        # ✅ Package Lookup - استخدام package_lookup_key
        # ============================================================
        package = None

        for code in package_codes:
            # ✅ استخدام package_lookup_key
            key = ImportHelpers.package_lookup_key(
                code,
                package_name,
            )

            package = packages_cache.get(key)

            if package:
                break

        if not package:
            result["package_not_found"] += 1
            for code in package_codes:
                result["missing_codes"].add(code)
            return

        # ============================================================
        # ✅ ContractPackage
        # ============================================================
        price = ContractStructureMigrationService.clean_decimal(
            row.get("السعر")
        )

        defaults = {
            "total_before_discount": ContractStructureMigrationService.clean_decimal(
                row.get("الاجمالي")
            ),
            "current_discount_rate": ContractStructureMigrationService.clean_percentage(
                row.get("معدل الخصم الحالي")
            ),
            "current_discount_text": ContractStructureMigrationService.clean_discount_text(
                row.get("معدل الخصم الحالي")
            ),
            "cash_price": ContractStructureMigrationService.clean_decimal(
                row.get("النقدي")
            ),
            "special_offer_price": ContractStructureMigrationService.clean_decimal(
                row.get("Special Offer")
            ),
            "special_offer_company": (
                row.get("الشركه.1") or ""
            ),
            "price_list_applied": row.get(
                "قائمة الاسعار المطبقه / معدل الزياده"
            ),
            "effective_from": ContractStructureMigrationService.clean_date(
                row.get("اعتبارا من")
            ),
            "valid_until": ContractStructureMigrationService.clean_date(
                row.get("ساري حتي")
            ),
            "notes": row.get("ملاحظات الباكدج"),
            "approval_pdf": row.get("الموافقه"),
            "is_active": True,
            "suggested_price": ContractStructureMigrationService.clean_decimal(
                row.get("السعر المقترح")
            ),
            "suggested_discount_rate": ContractStructureMigrationService.clean_percentage(
                row.get("معدل الخصم المقترح")
            ),
        }

        if price is None:
            print("=" * 80)
            print("PRICE IS NONE")
            print("Company :", company_name)
            print("Code    :", package_codes)
            print("Name    :", package_name)
            print("Raw     :", repr(row.get("السعر")))
            print("=" * 80)
            return

        defaults["package_price"] = price

        contract_package, created = ContractPackage.objects.update_or_create(
            contract=contract,
            package=package,
            defaults=defaults
        )

        if created:
            result["created_packages"] += 1
        else:
            result["updated_packages"] += 1