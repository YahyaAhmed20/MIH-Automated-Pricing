from contracts.models import ContractPackage
from .exceptions import (
    ContractPackageNotFoundError
)
from decimal import Decimal
class PricingCalculator:

    @staticmethod
    def get_contract_package(
        contract_id,
        package_id
    ):
        try:
            return ContractPackage.objects.select_related(
                "contract",
                "contract__entity",
                "package",
            ).get(
                contract_id=contract_id,
                package_id=package_id,
                is_active=True
            )

        except ContractPackage.DoesNotExist:
            raise ContractPackageNotFoundError(
                "Package pricing not found."
            )
        
    @staticmethod
    def get_package_price(
        contract_id,
        package_id
    ):
        
        contract_package = (
            PricingCalculator.get_contract_package(
                contract_id,
                package_id
            )
        )

        return {
            "package_price":
                contract_package.package_price,

            "cash_price":
                contract_package.cash_price,

            "special_offer_price":
                contract_package.special_offer_price,

            "discount_rate":
                contract_package.current_discount_rate,
        }    
    
    @staticmethod
    def apply_discount(
        amount,
        discount_percentage
    ):
        if not discount_percentage:
            return amount

        discount_percentage = Decimal(
            str(discount_percentage)
        )

        return amount - (
            amount * discount_percentage / Decimal("100")
        )
        
    @staticmethod
    def calculate_final_price(
        contract_id,
        package_id,
        discount_percentage=None
    ):
        data = PricingCalculator.get_package_price(
            contract_id,
            package_id
        )

        final_price = (
            PricingCalculator.apply_discount(
                data["package_price"],
                discount_percentage
            )
        )

        data["final_price"] = final_price
        data["pricing_type"] = "discount"

        return data