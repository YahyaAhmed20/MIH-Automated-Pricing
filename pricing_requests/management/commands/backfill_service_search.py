from django.core.management.base import BaseCommand

from pricing_requests.models import ServiceRecord
from imports.utils.import_helpers import ImportHelpers


class Command(BaseCommand):
    help = "Backfill normalized search fields for ServiceRecord"

    def handle(self, *args, **options):
        batch = []
        total = 0

        for record in ServiceRecord.objects.iterator(chunk_size=1000):

            record.service_name_search = (
                ImportHelpers.arabic_search_variants(
                    record.service_name
                )[0]
            )

            record.department_name_search = (
                ImportHelpers.arabic_search_variants(
                    record.department_name
                )[0]
            )

            batch.append(record)

            if len(batch) >= 1000:
                ServiceRecord.objects.bulk_update(
                    batch,
                    [
                        "service_name_search",
                        "department_name_search",
                    ],
                    batch_size=1000,
                )

                total += len(batch)
                self.stdout.write(
                    f"Updated: {total}"
                )

                batch = []

        if batch:
            ServiceRecord.objects.bulk_update(
                batch,
                [
                    "service_name_search",
                    "department_name_search",
                ],
                batch_size=1000,
            )

            total += len(batch)

        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated {total} ServiceRecord records."
            )
        )