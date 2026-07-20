from django.core.management.base import BaseCommand

from imports.services.google_sheets_service import (
    GoogleSheetsService,
)


class Command(BaseCommand):

    help = "Test Google Sheets Connection"

    def handle(self, *args, **options):

        GoogleSheetsService.test_connection()