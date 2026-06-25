import pandas as pd

from contracts.models import ContractPackage
from imports.utils.import_helpers import ImportHelpers


class PackagePriceMetadataImportService:

    @staticmethod
    def clean_text(value):

        if pd.isna(value):
            return ""

        return str(value).strip()

    @staticmethod
    def import_data(dataframe):

        updated = 0
        not_found = 0

        for _, row in dataframe.iterrows():

            company_name = PackagePriceMetadataImportService.clean_text(
                row.get("Companyname")
            )

            package_name = PackagePriceMetadataImportService.clean_text(
                row.get("Packagename")
            )

            cp = ContractPackage.objects.filter(
                contract__entity__name=company_name,
                package__name=package_name
            ).first()

            if not cp:
                not_found += 1
                continue

            cp.notes = row.get("notes")

            cp.approval_pdf = row.get("Approvalpdf")
            cp.effective_from = row.get("Lastupdatedate")

            cp.valid_until = ImportHelpers.clean_date(
                row.get("ساري حتي")
)


            cp.save()

            updated += 1

        return {
            "updated": updated,
            "not_found": not_found,
        }