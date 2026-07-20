# imports/management/commands/import_medical_procedures.py

from django.core.management.base import BaseCommand
from imports.services.excel_provider import ExcelProvider
from pricing_requests.services.medical_procedures_import_service import (
    MedicalProceduresImportService,
)


class Command(BaseCommand):

    help = "Import Medical Procedures from Sheet 13"

    def add_arguments(self, parser):
        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("========== Medical Procedures Import ==========")

        # ✅ استخدم header=None
        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="13",  # ✅ شيت 13
            header=None,      # ✅ مفيش Header
        )

        result = MedicalProceduresImportService.import_data(dataframe)

        self.stdout.write(f"Processed            : {result['processed']}")
        self.stdout.write(f"Created Specialties  : {result['created_specialties']}")
        self.stdout.write(f"Created Procedures   : {result['created_procedures']}")
        self.stdout.write(f"Updated Procedures   : {result['updated_procedures']}")
        self.stdout.write(f"Skipped              : {result['skipped']}")
        self.stdout.write("===========================================")