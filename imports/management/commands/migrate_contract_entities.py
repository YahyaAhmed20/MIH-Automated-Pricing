from django.core.management.base import BaseCommand

from imports.services.excel_provider import ExcelProvider

from imports.services.contract_structure_migration_service import (
    ContractStructureMigrationService,
)


class Command(BaseCommand):

    help = "Migrate Contract Structure"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            nargs="?",
            default=None,
            help="Path to Excel file (Optional)"
        )

    def handle(self, *args, **options):

        dataframe = ExcelProvider.read(
            file_path=options["file_path"],
            sheet_name="1",
            header=0,
        )

        result = (
            ContractStructureMigrationService.migrate(
                dataframe
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                str(result)
            )
        )