from django.core.management.base import BaseCommand

from medical_catalog.models import Package


class Command(BaseCommand):

    help = "Fix Cash Package Specialties"

    def handle(self, *args, **kwargs):

        updated = 0

        for package in Package.objects.exclude(code__isnull=True):

            if not package.code.endswith("-C"):
                continue

            original_code = package.code[:-2]

            original = Package.objects.filter(
                code=original_code
            ).first()

            if not original:
                continue

            package.specialty = original.specialty

            package.save(
                update_fields=["specialty"]
            )

            updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Updated: {updated}"
            )
        )