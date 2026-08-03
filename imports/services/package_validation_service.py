from django.db.models import Count

from medical_catalog.models import Package


class PackageValidationService:

    @classmethod
    def duplicate_packages(cls):
        """
        Return duplicate package groups
        based on:
            Entity + Code + Name
        """

        return (
            Package.objects
            .values(
                "entity_id",
                "entity__name",
                "code",
                "name",
            )
            .annotate(
                total=Count("id"),
            )
            .filter(total__gt=1)
            .order_by(
                "entity__name",
                "code",
                "name",
            )
        )

    @classmethod
    def summary(cls):

        duplicates = cls.duplicate_packages()

        duplicate_groups = duplicates.count()

        duplicate_records = sum(
            row["total"] - 1
            for row in duplicates
        )

        print("=" * 80)
        print("PACKAGE VALIDATION")
        print("=" * 80)

        print(f"Duplicate Groups  : {duplicate_groups}")
        print(f"Duplicate Records : {duplicate_records}")

        print("\nDuplicate Details")
        print("-" * 80)
        for row in duplicates:
            print(
                f"Company={row['entity__name']} | "
                f"Code={row['code']} | "
                f"Name={row['name']} | "
                f"Count={row['total']}"
            )

        print("=" * 80)

        return {
            "duplicate_groups": duplicate_groups,
            "duplicate_records": duplicate_records,
        }