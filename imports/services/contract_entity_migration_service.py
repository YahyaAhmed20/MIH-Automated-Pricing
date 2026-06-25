import pandas as pd

from contracts.models import (
    ContractEntity,
    FinancialCategory,
    Contract,
)


class ContractEntityMigrationService:

    @staticmethod
    def clean_company_name(value):
        if pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def import_entities(dataframe):
        created = 0
        existed = 0
        seen = set()

        for _, row in dataframe.iterrows():
            full_name = ContractEntityMigrationService.clean_company_name(
                row.get("الشركه")
            )

            if not full_name:
                continue

            full_name = full_name.replace("\r", "").strip()

            if full_name in seen:
                continue

            seen.add(full_name)

            entity, is_created = ContractEntity.objects.get_or_create(
                name=full_name
            )

            if is_created:
                created += 1
            else:
                existed += 1

        return {
            "created_entities": created,
            "existing_entities": existed,
        }

    @staticmethod
    def create_financial_category(old_contract, new_entity):
        financial_category, _ = FinancialCategory.objects.get_or_create(
            entity=new_entity,
            code=old_contract.financial_category.code,
            defaults={
                "description": old_contract.financial_category.description,
                "is_active": old_contract.financial_category.is_active,
            }
        )
        return financial_category

    @staticmethod
    def create_contract(old_contract, new_entity, financial_category):
        contract, created = Contract.objects.get_or_create(
            entity=new_entity,
            defaults={
                "financial_category": financial_category,
                "price_list": old_contract.price_list,
                "contract_type": old_contract.contract_type,
                "effective_from": old_contract.effective_from,
                "is_active": old_contract.is_active,
                "notes": old_contract.notes,
            }
        )
        return contract