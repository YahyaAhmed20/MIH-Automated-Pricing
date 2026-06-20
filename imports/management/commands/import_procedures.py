from django.core.management.base import BaseCommand

from imports.utils.excel_reader import ExcelReader
from imports.services.procedure_import_service import (
    ProcedureImportService,
)


class Command(BaseCommand):

    help = "Import Medical Procedures Sheet"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            type=str
        )

    def handle(
        self,
        *args,
        **options
    ):

        file_path = options["file_path"]

        self.stdout.write(
            self.style.WARNING(
                "Starting procedures import..."
            )
        )

        dataframe = ExcelReader.read_sheet(
            file_path=file_path,
            sheet_name="Medical Procedures"
        )

        result = (
            ProcedureImportService.import_data(
                dataframe
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created Specialties: {result['created_specialties']}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created Procedures: {result['created_procedures']}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated Procedures: {result['updated_procedures']}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Errors Count: {result['errors_count']}"
            )
        )

        if result["errors"]:

            self.stdout.write(
                self.style.ERROR(
                    "\nImport Errors:"
                )
            )

            for error in result["errors"]:
                self.stdout.write(
                    self.style.ERROR(error)
                )

        self.stdout.write(
            self.style.SUCCESS(
                "\nImport Completed Successfully."
            )
        )
        
        
        
        
        
        
        
        
       