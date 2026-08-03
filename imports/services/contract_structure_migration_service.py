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

from medical_catalog.models import Package, Specialty

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
    # ✅ migrate() - المعدل مع Cache و Bulk Operations + الحذف + إنشاء Packages مفقودة
    # ============================================================
    @staticmethod
    def migrate(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting migration...")

        # ✅ ✅ ✅ Cache للباكدجات - استخدام (code, entity_id, name) كمفتاح
        print("⏳ Loading packages...")
        packages_cache = {}
        for p in Package.objects.exclude(code__isnull=True).only('code', 'entity_id', 'name').iterator(chunk_size=200):
            key = (
                ImportHelpers.normalize_text(p.code),
                p.entity_id if p.entity_id else None,
                ImportHelpers.normalize_text(p.name),
            )
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
            "deleted_contract_packages": 0,
        }

        # ✅ قوائم التجميع للـ Bulk Operations
        contract_packages_to_create = []
        contract_packages_to_update = []
        contract_package_keys_in_sheet = set()

        # ✅ تشغيل على كل الصفوف - استخدام to_dict("records") عشان السرعة
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for row in dataframe.to_dict("records"):

            company_name = ContractStructureMigrationService.normalize_company_name(
                row.get(0, "")
            )

            package_codes = ContractStructureMigrationService.normalize_package_codes(
                row.get(6, "")
            )

            package_name = ImportHelpers.normalize_text(
                row.get(2, "")
            )

            financial_code = ImportHelpers.normalize_text(
                row.get(1, "")
            )

            # ✅ جلب التخصص من العمود 3
            specialty_name = ImportHelpers.normalize_text(
                row.get(3, "")
            )

            if not company_name or not package_codes:
                continue

            result["processed"] += 1

            entity = ContractStructureMigrationService.get_or_create_entity(
                company_name,
                entities_cache,
                result,
            )

            if not financial_code:
                financial_code = "DEFAULT"

            financial_category = ContractStructureMigrationService.get_or_create_financial_category(
                entity,
                financial_code,
                financial_categories_cache,
                result,
            )

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
            # ✅ Package Lookup - مع إنشاء Package جديد لو مش موجود
            # ============================================================
            package = None
            found_code = None
            
            for code in package_codes:
                p_key = (
                    ImportHelpers.normalize_text(code),
                    entity.id,
                    ImportHelpers.normalize_text(package_name),
                )
                package = packages_cache.get(p_key)
                if package:
                    found_code = code
                    break

            # ✅ إذا مش موجود، أنشئ Package جديد
            if not package:
                # ✅ جلب التخصص من الاسم
                specialty = None
                if specialty_name:
                    specialty = Specialty.objects.filter(name__icontains=specialty_name).first()
                if not specialty:
                    specialty = Specialty.objects.first()
                
                # ✅ استخدم أول كود من القائمة
                first_code = package_codes[0] if package_codes else f"UNKNOWN_{result['processed']}"
                
                # ✅ إنشاء Package جديد
                package = Package.objects.create(
                    code=first_code,
                    name=package_name,
                    specialty=specialty,
                    entity=entity,
                    is_active=True,
                )
                # ✅ ✅ ✅ أضفه في الـ Cache عشان منكررهوش تاني
                packages_cache[p_key] = package
                print(f"   ✅ Created new package: {first_code} - {package_name}")
                result["created_packages"] += 1

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
                "special_offer_company": (
                    row.get(15, "") or ""
                ),
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
                contract_packages_to_create.append(contract_package)
                contract_packages_cache[contract_package_key] = contract_package
                result["created_packages"] += 1

            processed += 1
            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

            # ✅ تنفيذ الـ Bulk Operations كل 1000 صف عشان الذاكرة
            if len(contract_packages_to_create) >= 500:
                ContractPackage.objects.bulk_create(
                    contract_packages_to_create,
                    batch_size=500,
                )
                contract_packages_to_create = []

            if len(contract_packages_to_update) >= 500:
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
                    batch_size=500,
                )
                contract_packages_to_update = []

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ✅ تنفيذ الـ Bulk Operations المتبقية
        if contract_packages_to_create:
            ContractPackage.objects.bulk_create(
                contract_packages_to_create,
                batch_size=500,
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

        # ============================================================
        # ✅ ✅ ✅ إضافة ContractPackages المفقودة (محسنة)
        # ============================================================
        print("⏳ Checking for missing ContractPackages...")

        # ✅ Query واحدة لجلب كل الـ ContractPackages النشطة
        all_active_cp = ContractPackage.objects.filter(
            is_active=True
        ).select_related('contract', 'package')

        # ✅ بناء set من (contract_id, package_id)
        existing_cp_keys = set()
        for cp in all_active_cp:
            existing_cp_keys.add((cp.contract_id, cp.package_id))

        # ✅ تجميع الـ Entities من الشيت
        entities_in_sheet = set()
        for row in dataframe.to_dict("records"):
            company_name = ContractStructureMigrationService.normalize_company_name(
                row.get(0, "")
            )
            if company_name:
                entity = entities_cache.get(company_name)
                if entity:
                    entities_in_sheet.add(entity.id)

        # ✅ لكل Entity، جيب Packagesها وافحصها
        missing_count = 0
        for entity_id in entities_in_sheet:
            entity = ContractEntity.objects.get(id=entity_id)
            contract = Contract.objects.filter(entity=entity).first()
            if not contract:
                continue
            
            packages = Package.objects.filter(entity=entity, is_active=True)
            
            for p in packages:
                key = (contract.id, p.id)
                if key not in existing_cp_keys:
                    ContractPackage.objects.create(
                        contract=contract,
                        package=p,
                        package_price=0,
                        is_active=True,
                    )
                    missing_count += 1
                    print(f"   ✅ Added missing ContractPackage: {p.code} - {p.name}")

        if missing_count > 0:
            print(f"   ✅ Added {missing_count} missing ContractPackages")
        else:
            print("   ✅ No missing ContractPackages found")

        # ✅ تحويل set إلى list مرتب
        result["missing_codes"] = sorted(list(result["missing_codes"]))

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result