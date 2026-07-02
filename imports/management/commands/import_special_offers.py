import pandas as pd

from django.core.management.base import BaseCommand

from imports.services.special_offers_service import (
    SpecialOfferImportService,
)


class Command(BaseCommand):

    help = "Import Special Offers"

    def add_arguments(self, parser):

        parser.add_argument(
            "excel_file",
            type=str,
        )

    def handle(self, *args, **options):

        self.stdout.write("")

        self.stdout.write(
            "========== Special Offers Import =========="
        )

        dataframe = pd.read_excel(
            options["excel_file"],
            sheet_name="5",
        )
        dataframe.columns = dataframe.columns.str.strip()

        result = SpecialOfferImportService.import_data(
            dataframe
        )

        self.stdout.write(
            f"Processed            : {result['processed']}"
        )

        self.stdout.write(
            f"Created Entities     : {result['created_entities']}"
        )

        self.stdout.write(
            f"Created Specialties  : {result['created_specialties']}"
        )

        self.stdout.write(
            f"Created Offers       : {result['created_offers']}"
        )

        self.stdout.write(
            f"Updated Offers       : {result['updated_offers']}"
        )

        self.stdout.write(
            "==========================================="
        )