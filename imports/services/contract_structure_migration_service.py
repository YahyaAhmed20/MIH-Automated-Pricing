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
    # ✅ Helper: معالجة النسب المئوية (جديد)
    # ============================================================
    @staticmethod
    def clean_percentage(value):
        value = ContractStructureMigrationService.clean_decimal(value)
        if value is None:
            return None
        # لو جاية من Excel كنسبة عشرية (مثل 0.15)
        if value <= 1:
            value *= 100
        return value

    # ============================================================
    # ✅ Helper: تنظيف أكواد الباكدجات (نسخة قوية بـ re)
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
    # ✅ get_parent_contract (معدل مع Cache)
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
    # ✅ get_or_create_contract (معدل مع Cache)
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

    @staticmethod
    @transaction.atomic
    def migrate(dataframe):

        # ✅ Cache للباكدجات (Performance)
        packages_cache = {
            p.code: p
            for p in Package.objects.all()
        }

        # ✅ Cache للعقود (Performance)
        contracts_cache = {
            c.entity.name: c
            for c in Contract.objects.select_related(
                "entity",
                "price_list"
            )
        }

        # ✅ Default Price List (مرة واحدة)
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

        # ============================================================
        # ✅ طباعة أول 5 صفوف قبل اللوب مباشرة
        # ============================================================
        print("=" * 80)
        print(dataframe.head(5)[
            [
                "الشركه",
                "الكود",
                "السعر"
            ]
        ])
        print("=" * 80)

        # ✅ تشغيل على كل الصفوف مع الـ Caches
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

    @staticmethod
    def sync_row(row, packages_cache, contracts_cache, default_price_list, result):

        # ============================================================
        # ✅ أول جزء في sync_row()
        # ============================================================

        company_name = (
            ContractStructureMigrationService.normalize_company_name(
                row.get("الشركه")
            )
        )

        # ✅ استخدام normalize_package_codes بدلاً من normalize_company_name
        package_codes = (
            ContractStructureMigrationService.normalize_package_codes(
                row.get("الكود")
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
        # ✅ Contract (مع الـ Caches)
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
        # ✅ Package Lookup (من Cache) مع دعم الأكواد المتعددة
        # ============================================================
        package = None
        for code in package_codes:
            package = packages_cache.get(code)
            if package:
                break

        if not package:
            result["package_not_found"] += 1
            for code in package_codes:
                result["missing_codes"].add(code)
            return

        # ============================================================
        # ✅ آخر جزء: ContractPackage (مع الـ Helpers)
        # ============================================================

        # ✅ استخراج السعر مع التحقق من عدم وجود قيمة فارغة
        price = ContractStructureMigrationService.clean_decimal(
            row.get("السعر")
        )

        # ✅ بناء الـ defaults
        defaults = {
            "total_before_discount": ContractStructureMigrationService.clean_decimal(
                row.get("الاجمالي")
            ),
            # ✅ استخدام clean_percentage للخصم الحالي
            "current_discount_rate": ContractStructureMigrationService.clean_percentage(
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

            # ✅ السعر المقترح
            "suggested_price": ContractStructureMigrationService.clean_decimal(
                row.get("السعر المقترح")
            ),
            # ✅ استخدام clean_percentage للخصم المقترح
            "suggested_discount_rate": ContractStructureMigrationService.clean_percentage(
                row.get("معدل الخصم المقترح")
            ),
        }

        # ✅ إضافة السعر فقط إذا كان موجود (لا نمسح السعر الموجود)
        if price is not None:
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