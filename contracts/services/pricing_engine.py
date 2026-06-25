from decimal import Decimal


class PricingEngine:

    @staticmethod
    def calculate_suggested_price(
        total_price,
        discount_rate
    ):
        """
        حساب السعر المقترح بعد الخصم
        """

        if total_price is None:
            return Decimal("0.00")

        if discount_rate is None:
            return total_price

        total_price = Decimal(str(total_price))
        discount_rate = Decimal(str(discount_rate))

        return total_price * (
            Decimal("1")
            - (discount_rate / Decimal("100"))
        )
        
    @staticmethod
    def calculate_savings(
        current_price,
        suggested_price
    ):
        """
        قيمة الوفر
        """

        if (
            current_price is None
            or
            suggested_price is None
        ):
            return Decimal("0.00")

        return Decimal(str(current_price)) - Decimal(str(suggested_price))
    
    @staticmethod
    def calculate_savings_percentage(
        current_price,
        suggested_price
    ):

        if (
            current_price is None
            or
            suggested_price is None
            or
            current_price == 0
        ):
            return Decimal("0.00")

        savings = (
            Decimal(str(current_price))
            -
            Decimal(str(suggested_price))
        )

        return (
            savings
            /
            Decimal(str(current_price))
        ) * Decimal("100")
        
        
    @staticmethod
    def get_best_price(contract_package):

        prices = []

        if contract_package.package_price:

            prices.append(
                (
                    "Current",
                    contract_package.package_price
                )
            )

        if contract_package.cash_price:

            prices.append(
                (
                    "Cash",
                    contract_package.cash_price
                )
            )

        if contract_package.special_offer_price:

            prices.append(
                (
                    "Special Offer",
                    contract_package.special_offer_price
                )
            )

        if contract_package.suggested_price:

            prices.append(
                (
                    "Suggested",
                    contract_package.suggested_price
                )
            )

        if not prices:
            return None

        return min(
            prices,
            key=lambda x: x[1]
        )