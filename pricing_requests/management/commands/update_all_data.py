from django.core.management.base import BaseCommand

from imports.services.update_all_data_service import (
    UpdateAllDataService,
)


class Command(BaseCommand):

    help = "Update all MIH data from Google Sheets"

    def handle(self, *args, **options):

        UpdateAllDataService.run(
            stdout=self.stdout,
        )