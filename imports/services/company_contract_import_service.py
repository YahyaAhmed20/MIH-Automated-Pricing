# imports/services/company_contract_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from imports.utils.import_helpers import ImportHelpers
from contracts.models import (
    Contract,
    ContractEntity,
    FinancialCategory,
    PriceList,
)


class CompanyContractImportService:

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
    def parse_medical_service(value):
        """
        تحويل الخدمة الطبية (نسبة الخصم) إلى نص مناسب
        مثال: 0.15 -> "15%"
        مثال: 15 -> "15%"
        مثال: "15%" -> "15%"
        """
        if value is None or pd.isna(value):
            return ""
        
        try:
            if isinstance(value, (int, float)):
                if 0 < value <= 1:
                    value = value * 100
                return f"{round(value)}%"
            
            cleaned = str(value).strip()
            if not cleaned:
                return ""
            
            cleaned = cleaned.replace('%', '').strip()
            num = float(cleaned)
            
            if 0 < num <= 1:
                num = num * 100
            
            return f"{round(num)}%"
            
        except (ValueError, TypeError):
            return str(value) if value else ""

    # ============================================================
    # Entity
    # ============================================================
    @staticmethod
    def get_entity(company_name, entities_cache, result):
        company_name = ImportHelpers.normalize_text(company_name)
        if not company_name:
            return None

        entity = entities_cache.get(company_name)
        if entity:
            result["existing_entities"] += 1
            return entity

        entity = ContractEntity.objects.create(name=company_name)
        entities_cache[company_name] = entity
        result["created_entities"] += 1
        return entity

    # ============================================================
    # Financial Category
    # ============================================================
    @staticmethod
    def get_financial_category(entity, financial_code, financial_cache, result):
        financial_code = ImportHelpers.normalize_text(financial_code)
        if not financial_code:
            return None

        key = (entity.id, financial_code)
        category = financial_cache.get(key)
        if category:
            result["existing_financial_categories"] += 1
            return category

        category = FinancialCategory.objects.create(
            entity=entity,
            code=financial_code,
            description=financial_code,
            is_active=True,
        )
        financial_cache[key] = category
        result["created_financial_categories"] += 1
        return category

    # ============================================================
    # Price List
    # ============================================================
    @staticmethod
    def get_price_list(price_list_name, effective_from, price_lists_cache, result):
        price_list_name = ImportHelpers.normalize_text(price_list_name)
        if not price_list_name:
            return None

        price_list = price_lists_cache.get(price_list_name)
        if price_list:
            result["existing_price_lists"] += 1
            return price_list

        price_list = PriceList.objects.create(
            name=price_list_name,
            effective_from=effective_from,
            is_active=True,
        )
        price_lists_cache[price_list_name] = price_list
        result["created_price_lists"] += 1
        return price_list

    # ============================================================
    # Import Data
    # ============================================================
    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Company Contracts import from Sheet 3...")

        result = {
            "processed": 0,
            "created_entities": 0,
            "existing_entities": 0,
            "created_financial_categories": 0,
            "existing_financial_categories": 0,
            "created_price_lists": 0,
            "existing_price_lists": 0,
            "created_contracts": 0,
            "updated_contracts": 0,
            "skipped_incomplete_contracts": 0,
            "deleted_contracts": 0,
        }

        # ============================================================
        # Cache
        # ============================================================
        print("⏳ Loading entities...")
        entities_cache = {}
        for entity in ContractEntity.objects.all():
            entities_cache[ImportHelpers.normalize_text(entity.name)] = entity
        print(f"   ✅ {len(entities_cache)} entities loaded")

        print("⏳ Loading financial categories...")
        financial_cache = {}
        for category in FinancialCategory.objects.all():
            key = (category.entity_id, ImportHelpers.normalize_text(category.code))
            financial_cache[key] = category
        print(f"   ✅ {len(financial_cache)} financial categories loaded")

        print("⏳ Loading price lists...")
        price_lists_cache = {}
        for price_list in PriceList.objects.all():
            price_lists_cache[ImportHelpers.normalize_text(price_list.name)] = price_list
        print(f"   ✅ {len(price_lists_cache)} price lists loaded")

        print("⏳ Loading contracts...")
        contracts_cache = {}
        for contract in Contract.objects.select_related("entity", "financial_category", "price_list"):
            key = (
                contract.entity_id,
                contract.financial_category_id,
                contract.price_list_id,
            )
            contracts_cache[key] = contract
        print(f"   ✅ {len(contracts_cache)} contracts loaded")

        # ============================================================
        # قوائم التجميع
        # ============================================================
        contracts_to_create = []
        contracts_to_update = []
        contract_keys_in_sheet = set()
        seen_keys = set()

        # ============================================================
        # Loop - الأعمدة الصحيحة لشيت 3
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ العمود 0: الجهة (الشركة)
            company_name = ImportHelpers.normalize_text(row.get(0, ""))
            company_name = CompanyContractImportService.truncate_text(company_name, 255)

            if not company_name:
                continue

            # ✅ العمود 1: نوع التعاقد
            contract_type = ImportHelpers.normalize_text(row.get(1, ""))
            contract_type = CompanyContractImportService.truncate_text(contract_type, 255)

            # ✅ العمود 2: الفئة المالية
            financial_code = ImportHelpers.normalize_text(row.get(2, ""))
            financial_code = CompanyContractImportService.truncate_text(financial_code, 50)

            # ✅ العمود 3: قائمة الاسعار الحاليه
            price_list_name = ImportHelpers.normalize_text(row.get(3, ""))
            price_list_name = CompanyContractImportService.truncate_text(price_list_name, 255)

            # ✅ العمود 4: الخدمة الطبية (نسبة الخصم)
            medical_service = CompanyContractImportService.parse_medical_service(row.get(4, None))

            # ✅ العمود 5: اعتباراً من (التاريخ)
            effective_from = ImportHelpers.clean_date(row.get(5, None))

            # ✅ العمود 6: تعليمات التشغيل
            operating_instructions = ImportHelpers.normalize_text(row.get(6, ""))
            operating_instructions = CompanyContractImportService.truncate_text(operating_instructions, 255)

            # ✅ العمود 12: ملاحظات
            notes = ImportHelpers.normalize_text(row.get(12, ""))
            notes = CompanyContractImportService.truncate_text(notes, 255)

            # ✅ منع التكرار في نفس الملف
            contract_key = (
                company_name,
                financial_code,
                price_list_name,
            )
            if contract_key in seen_keys:
                continue
            seen_keys.add(contract_key)

            processed += 1
            result["processed"] = processed

            # ✅ جلب أو إنشاء Entity
            entity = CompanyContractImportService.get_entity(
                company_name, entities_cache, result
            )
            if not entity:
                continue

            # ✅ تخطي الصف إذا كانت البيانات الأساسية ناقصة
            if not contract_type or not financial_code or not price_list_name:
                result["skipped_incomplete_contracts"] += 1
                if processed <= 10:
                    print(f"⚠️ صف {index}: بيانات ناقصة")
                continue

            # ✅ جلب أو إنشاء Financial Category
            financial_category = CompanyContractImportService.get_financial_category(
                entity, financial_code, financial_cache, result
            )

            # ✅ جلب أو إنشاء Price List
            price_list = CompanyContractImportService.get_price_list(
                price_list_name, effective_from, price_lists_cache, result
            )
            if not price_list:
                continue

            # ✅ تخزين المفتاح للحذف
            contract_db_key = (
                entity.id,
                financial_category.id if financial_category else None,
                price_list.id,
            )
            contract_keys_in_sheet.add(contract_db_key)

            # ✅ البحث في Cache
            existing_contract = contracts_cache.get(contract_db_key)

            if existing_contract:
                # ✅ تحديث البيانات
                changed = False

                if existing_contract.contract_type != contract_type:
                    existing_contract.contract_type = contract_type
                    changed = True

                if existing_contract.medical_service != medical_service:
                    existing_contract.medical_service = medical_service
                    changed = True

                if existing_contract.effective_from != effective_from:
                    existing_contract.effective_from = effective_from
                    changed = True

                if existing_contract.operating_instructions != operating_instructions:
                    existing_contract.operating_instructions = operating_instructions
                    changed = True

                if existing_contract.notes != notes:
                    existing_contract.notes = notes
                    changed = True

                if existing_contract.is_active is not True:
                    existing_contract.is_active = True
                    changed = True

                if changed:
                    contracts_to_update.append(existing_contract)
                    result["updated_contracts"] += 1

            else:
                # ✅ إنشاء جديد
                new_contract = Contract(
                    entity=entity,
                    financial_category=financial_category,
                    price_list=price_list,
                    contract_type=contract_type,
                    medical_service=medical_service,
                    effective_from=effective_from,
                    operating_instructions=operating_instructions,
                    notes=notes,
                    is_active=True,
                )
                contracts_to_create.append(new_contract)
                contracts_cache[contract_db_key] = new_contract
                result["created_contracts"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ حذف العقود غير الموجودة في الشيت
        # ============================================================
        if contract_keys_in_sheet:
            all_contract_keys = set(contracts_cache.keys())
            keys_to_delete = all_contract_keys - contract_keys_in_sheet
            
            if keys_to_delete:
                deleted_count = 0
                for key in keys_to_delete:
                    contract = contracts_cache.get(key)
                    if contract:
                        contract.delete()
                        deleted_count += 1
                if deleted_count > 0:
                    print(f"🗑️ Deleted {deleted_count} contracts not in sheet")
                    result["deleted_contracts"] = deleted_count
        else:
            print("⚠️ No contracts in sheet - skipping deletion to avoid data loss")

        # ============================================================
        # Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(contracts_to_create)} contracts...")
        print(f"💾 Updating {len(contracts_to_update)} contracts...")

        if contracts_to_create:
            Contract.objects.bulk_create(contracts_to_create, batch_size=1000)

        if contracts_to_update:
            Contract.objects.bulk_update(
                contracts_to_update,
                fields=[
                    "contract_type",
                    "medical_service",
                    "effective_from",
                    "operating_instructions",
                    "notes",
                    "is_active",
                ],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result