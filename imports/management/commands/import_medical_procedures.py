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
            help="Path to Excel file (Optional)",
        )

        parser.add_argument(
            "--no-confirm",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("   Medical Procedures Import")
        self.stdout.write("=" * 60)
        self.stdout.write("")

        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="13",
            header=None,
            force_reload=True,

        )

        total_rows = len(dataframe)

        if options.get("no_confirm"):

            self.stdout.write(
                f"✅ Importing {total_rows} Medical Procedures (auto-confirmed)"
            )

        else:

            confirm = input(
                f"Import {total_rows} Medical Procedures? (y/n): "
            )

            if confirm.lower() != "y":

                self.stdout.write(
                    self.style.WARNING("Import cancelled.")
                )

                return

        result = MedicalProceduresImportService.import_data(
            dataframe
        )

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("Medical Procedures Import Completed")
        self.stdout.write("=" * 60)

        self.stdout.write(
            f"Processed            : {result['processed']}"
        )

        self.stdout.write(
            f"Created Specialties  : {result['created_specialties']}"
        )

        self.stdout.write(
            f"Created Procedures   : {result['created_procedures']}"
        )

        self.stdout.write(
            f"Updated Procedures   : {result['updated_procedures']}"
        )

        self.stdout.write(
            f"Deleted Procedures   : {result['deleted_procedures']}"
        )

        self.stdout.write(
            f"Skipped              : {result['skipped']}"
        )

        self.stdout.write("=" * 60)