from django.core.management.base import BaseCommand
from django.db.models import Count
from django.db import transaction

from contracts.models import ContractPackage
from medical_catalog.models import Package


class Command(BaseCommand):
    help = "Deduplicate packages safely"

    def add_arguments(self, parser):
        parser.add_argument(
            "--apply",
            action="store_true",
            help="Apply changes",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Maximum duplicate groups to process",
        )

    def handle(self, *args, **options):

        apply = options["apply"]
        limit = options["limit"]

        self.stdout.write("=" * 70)
        self.stdout.write("Scanning duplicate packages...")
        self.stdout.write("=" * 70)

        duplicate_groups = (
            Package.objects
            .values(
                "entity_id",
                "code",
                "name",
            )
            .annotate(
                total=Count("id")
            )
            .filter(total__gt=1)
            .order_by()
        )

        total_groups = duplicate_groups.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Found {total_groups} duplicate groups"
            )
        )

        if limit:
            duplicate_groups = duplicate_groups[:limit]
            self.stdout.write(
                self.style.WARNING(
                    f"Processing only first {limit} groups"
                )
            )

        moved_contract_packages = 0
        deleted_packages = 0
        skipped_packages = 0
        processed_groups = 0

        for group in duplicate_groups:

            processed_groups += 1

            packages = (
                Package.objects
                .filter(
                    entity_id=group["entity_id"],
                    code=group["code"],
                    name=group["name"],
                )
                .annotate(
                    cp_count=Count("contract_packages")
                )
                .order_by("id")
            )

            keep = None
            best_score = -1

            for package in packages:

                score = 0

                # أهم معيار
                score += package.cp_count * 100

                # فيه سعر أساسي؟
                if package.base_price:
                    score += 20

                # فيه Notes؟
                if package.notes:
                    score += 5

                # احتفظ بالأعلى Score
                if (
                    keep is None
                    or score > best_score
                    or (
                        score == best_score
                        and package.id < keep.id
                    )
                ):
                    best_score = score
                    keep = package

            if keep is None:
                continue

            duplicates = packages.exclude(id=keep.id)

            if not apply:

                self.stdout.write(
                    f"KEEP SCORE = {best_score}"
                )

                for p in packages:
                    self.stdout.write(
                        f"    id={p.id}"
                        f" cp={p.cp_count}"
                        f" base_price={'YES' if p.base_price else 'NO'}"
                    )

                duplicate_ids = list(
                    duplicates.values_list("id", flat=True)
                )

                self.stdout.write(
                    self.style.WARNING(
                        f"[DRY RUN]\n"
                        f"Entity ID : {group['entity_id']}\n"
                        f"Code      : {group['code']}\n"
                        f"Name      : {group['name']}\n"
                        f"KEEP ID   : {keep.id}\n"
                        f"DELETE IDs: {duplicate_ids}\n"
                        f"{'-' * 60}"
                    )
                )

                continue

            self.stdout.write(
                f"KEEP -> "
                f"id={keep.id} "
                f"code={keep.code} "
                f"cp={keep.cp_count}"
            )

            for duplicate in duplicates:

                with transaction.atomic():

                    self.stdout.write(
                        f"Processing duplicate {duplicate.id}"
                    )

                    contract_packages = ContractPackage.objects.filter(
                        package=duplicate
                    )

                    # إذا لم يكن هناك ContractPackages، احذف الـ Package مباشرة
                    if not contract_packages.exists():
                        package_id = duplicate.id
                        duplicate.delete()
                        deleted_packages += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Deleted Package {package_id} (no ContractPackages)"
                            )
                        )
                        continue

                    can_delete = True

                    for cp in contract_packages:

                        # Safety Check
                        already_exists = ContractPackage.objects.filter(
                            contract=cp.contract,
                            package=keep,
                        ).exists()

                        if already_exists:

                            self.stdout.write(
                                self.style.WARNING(
                                    f"SKIP ContractPackage {cp.id} "
                                    f"(already exists)"
                                )
                            )

                            skipped_packages += 1
                            can_delete = False
                            continue

                        ContractPackage.objects.filter(pk=cp.pk).update(
                            package=keep
                        )

                        moved_contract_packages += 1

                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Moved ContractPackage {cp.id}"
                            )
                        )

                    if can_delete:
                        package_id = duplicate.id
                        duplicate.delete()
                        deleted_packages += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"Deleted Package {package_id}"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Skipped deleting Package {duplicate.id} "
                                f"(some ContractPackages already exist in target)"
                            )
                        )

        self.stdout.write("=" * 70)

        self.stdout.write(
            self.style.SUCCESS(
                f"Duplicate Groups Processed : {processed_groups}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Moved ContractPackages    : {moved_contract_packages}"
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Deleted Packages          : {deleted_packages}"
            )
        )

        self.stdout.write(
            self.style.WARNING(
                f"Skipped Packages          : {skipped_packages}"
            )
        )

        self.stdout.write("=" * 70)