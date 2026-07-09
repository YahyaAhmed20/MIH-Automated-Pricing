from contracts.models import CompanyDiscountProfile


class CompanyComparisonService:

    @staticmethod
    def get_company(company_name):

        if not company_name:
            return None

        return (
            CompanyDiscountProfile.objects
            .prefetch_related("discounts")
            .filter(company_name=company_name)
            .first()
        )

    @staticmethod
    def build_comparison(company1, company2, section="all"):

        rows = {}

        for company, key in [
            (company1, "company1"),
            (company2, "company2"),
        ]:

            if not company:
                continue

            for discount in company.discounts.all():

                if (
                    section == "internal"
                    and discount.section != "داخلي"
                ):
                    continue

                if (
                    section == "external"
                    and discount.section != "خارجي"
                ):
                    continue

                item = discount.item_name

                if item not in rows:

                    rows[item] = {
                        "item": item,
                        "company1": "",
                        "company2": "",
                    }

                rows[item][key] = discount.discount

        return list(rows.values())