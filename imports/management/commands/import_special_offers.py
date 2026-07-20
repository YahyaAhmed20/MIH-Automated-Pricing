# imports/management/commands/import_special_offers.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from imports.services.special_offers_service import SpecialOfferImportService


class Command(BaseCommand):

    help = "Import Special Offers from Sheet 5"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Special Offers Import ==========")

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="5",  # ✅ شيت 5
            header=None,     # ✅ مفيش Header
        )

        result = SpecialOfferImportService.import_data(dataframe)

        self.stdout.write("")
        self.stdout.write("===========================================")
        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created Entities     : {result['created_entities']}")
        self.stdout.write(f"Created Specialties  : {result['created_specialties']}")
        self.stdout.write(f"Created Offers       : {result['created_offers']}")
        self.stdout.write(f"Updated Offers       : {result['updated_offers']}")
        self.stdout.write("===========================================")