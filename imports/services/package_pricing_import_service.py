from decimal import Decimal
import pandas as pd

from medical_catalog.models import Specialty, Package

from contracts.models import (
    ContractEntity,
    FinancialCategory,
    PriceList,
    Contract,
    ContractPackage,
)


class PackagePricingImportService:

    FIXED_SPECIALTY_NAME = "عام"

    SKIP_COLUMNS = [
        "الباكدجات",
        "مدة الاقامه",
        "الكود",
        "بدون خصم ",
        "Unnamed: 154",
    ]

    # ---------------------------
    # Helpers
    # ---------------------------

    @staticmethod
    def clean_text(value):
        if pd.isna(value):
            return ""
        return str(value).strip()

    @staticmethod
    def parse_decimal(value):
        if pd.isna(value):
            return None

        value = str(value).strip()
        value = value.replace(",", "")

        try:
            return Decimal(value)
        except Exception:
            return None

    @staticmethod
    def parse_discount(value):
        if pd.isna(value):
            return None

        value = str(value).strip()

        if value.endswith("%"):
            try:
                return Decimal(value.replace("%", ""))
            except Exception:
                return None

        return None

    @staticmethod
    def get_pricing_type(value):
        if pd.isna(value):
            return None

        value = str(value).strip()

        if value == "عرض خاص":
            return "special_offer"

        if value == "بدون خصم":
            return "cash"

        if "%" in value:
            return "discount"

        return None

    # ---------------------------
    # Main Import
    # ---------------------------

    @staticmethod
    def import_data(dataframe):

        created_packages = 0
        updated_packages = 0

        created_entities = 0
        created_contracts = 0

        created_contract_packages = 0
        updated_contract_packages = 0

        specialty, _ = Specialty.objects.get_or_create(
            name=PackagePricingImportService.FIXED_SPECIALTY_NAME,
            defaults={"is_active": True},
        )

        default_price_list, _ = PriceList.objects.get_or_create(
            name="DATA IMPORT"
        )

        metadata_row = dataframe.iloc[0]

        company_columns = [
            c for c in dataframe.columns
            if c not in PackagePricingImportService.SKIP_COLUMNS
        ]

        # ---------------------------
        # Contracts map (performance)
        # ---------------------------
        contracts_map = {}

        for company_name in company_columns:

            company_name = PackagePricingImportService.clean_text(company_name)
            if not company_name:
                continue

            entity, _ = ContractEntity.objects.get_or_create(
                name=company_name,
                defaults={"is_active": True},
            )

            financial_category, _ = FinancialCategory.objects.get_or_create(
                entity=entity,
                code="DEFAULT",
                defaults={"is_active": True},
            )

            contract, contract_created = Contract.objects.get_or_create(
                entity=entity,
                financial_category=financial_category,
                price_list=default_price_list,
                defaults={"is_active": True},
            )

            contracts_map[company_name] = contract

            if contract_created:
                created_contracts += 1

        # ---------------------------
        # Rows loop
        # ---------------------------
        for index in range(1, len(dataframe)):

            row = dataframe.iloc[index]

            package_name = PackagePricingImportService.clean_text(
                row.get("الباكدجات")
            )

            if (
                not package_name
                or package_name == "ملاحظات الباكدج"
            ):
                continue

            package_code = PackagePricingImportService.clean_text(
                row.get("الكود", "")
            )

            if package_code.lower() == "nan":
                package_code = ""

            stay_duration = PackagePricingImportService.clean_text(
                row.get("مدة الاقامه", "")
            )

            base_price = PackagePricingImportService.parse_decimal(
                row.get("بدون خصم ")
            )

            if base_price is None:
                continue

            # ---------------------------
            # Safe package lookup
            # ---------------------------
            lookup = {"code": package_code} if package_code else {"name": package_name}

            package, created = Package.objects.update_or_create(
                **lookup,
                defaults={
                    "specialty": specialty,
                    "name": package_name,
                    "stay_duration": stay_duration,
                    "is_active": True,
                },
            )

            if created:
                created_packages += 1
            else:
                updated_packages += 1

            # ---------------------------
            # Pricing loop
            # ---------------------------
            for company_name in company_columns:

                company_name = PackagePricingImportService.clean_text(company_name)
                if not company_name:
                    continue

                contract = contracts_map.get(company_name)
                if not contract:
                    continue

                price = PackagePricingImportService.parse_decimal(
                    row.get(company_name)
                )

                if price is None:
                    continue

                discount_rate = PackagePricingImportService.parse_discount(
                    metadata_row.get(company_name)
                )

                contract_package, cp_created = ContractPackage.objects.update_or_create(
                    contract=contract,
                    package=package,
                    defaults={
                        "package_price": price,
                        "cash_price": base_price,
                        "current_discount_rate": discount_rate,
                        "is_active": True,
                    },
                )

                if cp_created:
                    created_contract_packages += 1
                else:
                    updated_contract_packages += 1

        return {
            "created_entities": created_entities,
            "created_contracts": created_contracts,
            "created_packages": created_packages,
            "updated_packages": updated_packages,
            "created_contract_packages": created_contract_packages,
            "updated_contract_packages": updated_contract_packages,
        }