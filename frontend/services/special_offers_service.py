from django.db.models import Q

from contracts.models import (
    SpecialOffer,
)


class SpecialOffersService:

    COLORS = [
        "primary",
        "success",
        "danger",
        "warning",
        "info",
        "secondary",
        "dark",
    ]

    @staticmethod
    def get_company_color(company_name):

        index = abs(hash(company_name)) % len(
            SpecialOffersService.COLORS
        )

        return SpecialOffersService.COLORS[index]

    @staticmethod
    def get_special_offers(search=""):

        offers = SpecialOffer.objects.select_related(
            "entity",
            "specialty",
        ).filter(
            is_active=True,
        )

        if search:

            offers = offers.filter(

                Q(entity__name__icontains=search)

                |

                Q(procedure_name__icontains=search)

            )

        offers = offers.order_by(

            "entity__name",

            "procedure_name",

        )

        for offer in offers:

            offer.company_color = (
                SpecialOffersService.get_company_color(
                    offer.entity.name
                )
            )

        return offers