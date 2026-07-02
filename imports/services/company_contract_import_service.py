import pandas as pd
from django.db import transaction
from imports.utils.import_helpers import ImportHelpers
from contracts.models import (
    Contract,
    ContractEntity,
    FinancialCategory,
    PriceList,
)


class CompanyContractImportService:

    # ============================================================
    # Entity
    # ============================================================
    @staticmethod
    def get_entity(
        company_name,
        entities_cache,
        result,
    ):

        company_name = ImportHelpers.normalize_text(
            company_name
        )

        if not company_name:
            return None

        entity = entities_cache.get(company_name)

        if entity:
            result["existing_entities"] += 1
            return entity

        entity = ContractEntity.objects.create(
            name=company_name
        )

        entities_cache[company_name] = entity

        result["created_entities"] += 1

        return entity

    # ============================================================
    # Financial Category
    # ============================================================
    @staticmethod
    def get_financial_category(
        entity,
        financial_code,
        financial_cache,
        result,
    ):

        financial_code = ImportHelpers.normalize_text(
            financial_code
        )

        if not financial_code:
            return None

        key = (
            entity.id,
            financial_code,
        )

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
    def get_price_list(
        price_list_name,
        effective_from,
        price_lists_cache,
        result,
    ):

        price_list_name = ImportHelpers.normalize_text(
            price_list_name
        )

        if not price_list_name:
            return None

        price_list = price_lists_cache.get(
            price_list_name
        )

        if price_list:

            if effective_from:
                price_list.effective_from = effective_from
                price_list.save(
                    update_fields=["effective_from"]
                )

            result["existing_price_lists"] += 1

            return price_list

        price_list = PriceList.objects.create(
            name=price_list_name,
            effective_from=effective_from,
            is_active=True,
        )

        price_lists_cache[
            price_list_name
        ] = price_list

        result["created_price_lists"] += 1

        return price_list

    # ============================================================
    # Contract
    # ============================================================
    @staticmethod
    def get_contract(
        entity,
        financial_category,
        price_list,
        contract_type,
        medical_service,
        effective_from,
        operating_instructions,
        contracts_cache,
        result,
    ):

        key = (
            entity.id,
            financial_category.id if financial_category else None,
            price_list.id if price_list else None,
        )

        contract = contracts_cache.get(key)

        if contract:

            contract.contract_type = contract_type
            contract.medical_service = medical_service
            contract.effective_from = effective_from
            contract.operating_instructions = (
                operating_instructions
            )
            contract.is_active = True

            contract.save()

            result["updated_contracts"] += 1

            return contract

        contract = Contract.objects.create(
            entity=entity,
            financial_category=financial_category,
            price_list=price_list,
            contract_type=contract_type,
            medical_service=medical_service,
            effective_from=effective_from,
            operating_instructions=operating_instructions,
            is_active=True,
        )

        contracts_cache[key] = contract

        result["created_contracts"] += 1

        return contract

    # ============================================================
    # Import Data
    # ============================================================
    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

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
        }

        # ============================================================
        # Cache
        # ============================================================

        entities_cache = {
            entity.name: entity
            for entity in ContractEntity.objects.all()
        }

        financial_cache = {
            (
                category.entity_id,
                category.code,
            ): category
            for category in FinancialCategory.objects.all()
        }

        price_lists_cache = {
            price_list.name: price_list
            for price_list in PriceList.objects.all()
        }

        contracts_cache = {
            (
                contract.entity_id,
                contract.financial_category_id,
                contract.price_list_id,
            ): contract
            for contract in Contract.objects.select_related(
                "entity",
                "financial_category",
                "price_list",
            )
        }

        # ============================================================
        # Loop
        # ============================================================

        for _, row in dataframe.iterrows():

            company_name = ImportHelpers.normalize_text(
                row.get("الجهة")
            )

            if not company_name:
                continue

            result["processed"] += 1

            contract_type = ImportHelpers.normalize_text(
                row.get("نوع التعاقد")
            )

            financial_code = ImportHelpers.normalize_text(
                row.get("الفئة المالية")
            )

            price_list_name = ImportHelpers.normalize_text(
                row.get("قائمة الاسعار الحاليه")
            )

            raw_medical_service = row.get("الخدمة الطبية")

            if isinstance(raw_medical_service, (int, float)):
                medical_service = f"{raw_medical_service * 100:.0f}%"
            else:
                medical_service = ImportHelpers.normalize_text(
                    raw_medical_service
                )

            effective_from = ImportHelpers.clean_date(
                row.get("اعتبارا من")
            )

            operating_instructions = (
                ImportHelpers.normalize_text(
                    row.get("تعليمات التشغيل")
                )
            )

            # ✅ جلب أو إنشاء Entity أولاً
            entity = CompanyContractImportService.get_entity(
                company_name,
                entities_cache,
                result,
            )

            if not entity:
                continue

            # ✅ تخطي الصف إذا كانت البيانات الأساسية ناقصة (بعد entity)
            if (
                not contract_type
                or not financial_code
                or not price_list_name
            ):
                result["skipped_incomplete_contracts"] += 1
                continue

            financial_category = (
                CompanyContractImportService.get_financial_category(
                    entity,
                    financial_code,
                    financial_cache,
                    result,
                )
            )

            price_list = (
                CompanyContractImportService.get_price_list(
                    price_list_name,
                    effective_from,
                    price_lists_cache,
                    result,
                )
            )

            if not price_list:
                continue

            CompanyContractImportService.get_contract(
                entity,
                financial_category,
                price_list,
                contract_type,
                medical_service,
                effective_from,
                operating_instructions,
                contracts_cache,
                result,
            )

        return result