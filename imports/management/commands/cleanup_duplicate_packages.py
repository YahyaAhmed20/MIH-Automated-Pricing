from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from medical_catalog.models import Package


class Command(BaseCommand):
    help = "Cleanup duplicate packages safely"

    @transaction.atomic
    def handle(self, *args, **options):

        self.stdout.write("=" * 70)
        self.stdout.write("Scanning duplicate packages...")
        self.stdout.write("=" * 70)

        # خد Snapshot للمجموعات قبل أي حذف
        duplicate_groups = list(
            Package.objects
            .values("entity_id", "code", "name")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        self.stdout.write(
            f"Found {len(duplicate_groups)} duplicate groups\n"
        )

        ids_to_delete = []

        for group in duplicate_groups:

            packages = list(
                Package.objects
                .filter(
                    entity_id=group["entity_id"],
                    code=group["code"],
                    name=group["name"],
                )
                .annotate(cp_count=Count("contract_packages"))
                .order_by("-cp_count", "-created_at")
            )

            keep = packages[0]

            self.stdout.write(
                f"Keeping #{keep.id} "
                f"{keep.code} "
                f"(cp={keep.cp_count})"
            )

            for package in packages[1:]:

                if package.cp_count == 0:
                    ids_to_delete.append(package.id)

                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Skip #{package.id} "
                            f"(still linked)"
                        )
                    )

        self.stdout.write("\n")
        self.stdout.write(
            f"Packages to delete : {len(ids_to_delete)}"
        )

        answer = input(
            "\nDelete them? (yes/no): "
        )

        if answer.lower() != "yes":

            self.stdout.write(
                self.style.WARNING(
                    "Cancelled."
                )
            )
            return

        deleted, _ = Package.objects.filter(
            id__in=ids_to_delete
        ).delete()

        self.stdout.write("\n")
        self.stdout.write("=" * 70)

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted : {deleted}"
            )
        )

        self.stdout.write("=" * 70)