from django.core.management.base import BaseCommand

from imports.utils.excel_reader import ExcelReader

from imports.services.contract_structure_migration_service import (
    ContractStructureMigrationService,
)


class Command(BaseCommand):

    help = "Migrate Contract Structure"

    def add_arguments(self, parser):

        parser.add_argument(
            "file_path",
            type=str
        )

    def handle(self, *args, **options):

        dataframe = ExcelReader.read_sheet(
            file_path=options["file_path"],
            sheet_name="1"
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