import pandas as pd
import time

from django.db import transaction, close_old_connections

from medical_catalog.models import (
    Package,
    PackageAttachment,
    Specialty,
)

from contracts.models import ContractEntity

from imports.services.google_sheets_service import GoogleSheetsService
from imports.utils.import_helpers import ImportHelpers


class PackageCatalogImportService:

    @staticmethod
    def truncate_text(value, max_length=255, counters=None):
        """تقليص النص إذا تجاوز الحد الأقصى"""

        if not value:
            return value

        cleaned = ImportHelpers.normalize_text(value)

        if len(cleaned) > max_length:
            if counters is not None:
                counters["truncated_texts"] += 1

            return cleaned[:max_length]

        return cleaned

    @staticmethod
    def extract_drive_data(
        drive_links,
        dataframe_index,
        column_index,
    ):
        """
        استخراج بيانات Smart Chip من Google Drive.

        Google Sheets API يستخدم row index يبدأ من 0.
        أول صف بيانات في DataFrame يقابل Sheet row 2.
        لذلك:
            dataframe_index 0 -> sheet API row 1
            dataframe_index 1 -> sheet API row 2
            ...

        وبالتالي نستخدم:
            dataframe_index + 1
        """

        position = (
            dataframe_index + 1,
            column_index,
        )

        return drive_links.get(position)

    @staticmethod
    def build_attachment_data(
        drive_links,
        dataframe_index,
    ):
        """
        تجهيز بيانات PackageAttachment
        من العمود T و U.

        T = 19 = مشتملات الباكدج
        U = 20 = تعليمات التشغيل
        """

        package_pdf = (
            PackageCatalogImportService.extract_drive_data(
                drive_links,
                dataframe_index,
                19,
            )
        )

        operation_instruction = (
            PackageCatalogImportService.extract_drive_data(
                drive_links,
                dataframe_index,
                20,
            )
        )

        data = {
            "package_pdf_name": None,
            "package_pdf_url": None,
            "package_pdf_drive_id": None,

            "operation_instruction_name": None,
            "operation_instruction_url": None,
            "operation_instruction_drive_id": None,
        }

        # ========================================================
        # مشتملات الباكدج - Column T
        # ========================================================

        if package_pdf:

            data["package_pdf_name"] = (
                package_pdf.get("name") or None
            )

            data["package_pdf_url"] = (
                package_pdf.get("url") or None
            )

            data["package_pdf_drive_id"] = (
                package_pdf.get("file_id") or None
            )

        # ========================================================
        # تعليمات التشغيل - Column U
        # ========================================================

        if operation_instruction:

            data["operation_instruction_name"] = (
                operation_instruction.get("name") or None
            )

            data["operation_instruction_url"] = (
                operation_instruction.get("url") or None
            )

            data["operation_instruction_drive_id"] = (
                operation_instruction.get("file_id") or None
            )

        return data

    @staticmethod
    def import_data(dataframe):

        start_time = time.perf_counter()

        print(
            "⏳ Starting Package Catalog import from Sheet 1..."
        )

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "created_specialties": 0,
            "deleted": 0,
            "skipped_duplicates": 0,
            "missing_specialty": 0,
            "truncated_texts": 0,

            # Drive statistics
            "created_attachments": 0,
            "updated_attachments": 0,
        }

        # ============================================================
        # ✅ تحميل Smart Chips من Google Drive مرة واحدة
        # ============================================================

        print(
            "⏳ Loading Google Drive Smart Chips "
            "from Sheet 1..."
        )

        drive_links = GoogleSheetsService.get_drive_links(
            sheet_name="1",
            start_row=1,
            end_row=len(dataframe) + 1,
        )

        print(
            f"   ✅ Loaded {len(drive_links)} Drive links"
        )

        # The Google API call above is external I/O. Ensure Django starts
        # the database phase with a healthy connection.
        close_old_connections()

        # ============================================================
        # ✅ Cache للـ Specialties
        # ============================================================

        print("⏳ Loading specialties...")

        specialties_cache = {}

        for s in Specialty.objects.all():

            specialties_cache[
                ImportHelpers.normalize_text(s.name)
            ] = s

        print(
            f"   ✅ {len(specialties_cache)} specialties loaded"
        )

        # ============================================================
        # ✅ Cache للـ ContractEntity
        # ============================================================

        print("⏳ Loading entities...")

        entities_cache = {}

        for e in ContractEntity.objects.all():

            entities_cache[
                ImportHelpers.normalize_text(e.name)
            ] = e

        print(
            f"   ✅ {len(entities_cache)} entities loaded"
        )

        # ============================================================
        # ✅ Cache للـ Packages
        # ============================================================

        print("⏳ Loading packages...")

        packages_cache = {}

        for p in Package.objects.exclude(
            code__isnull=True
        ):

            key = (
                p.entity_id
                if p.entity_id
                else None,

                ImportHelpers.normalize_text(
                    p.code
                ),

                ImportHelpers.normalize_text(
                    p.name
                ),
            )

            packages_cache[key] = p

        print(
            f"   ✅ {len(packages_cache)} packages loaded"
        )

        # ============================================================
        # ✅ Cache للـ Package Attachments
        # ============================================================

        print("⏳ Loading package attachments...")

        attachments_cache = {}

        for attachment in PackageAttachment.objects.all():

            attachments_cache[
                attachment.package_id
            ] = attachment

        print(
            f"   ✅ {len(attachments_cache)} attachments loaded"
        )

        # ============================================================
        # ✅ Bulk operation lists
        # ============================================================

        packages_to_create = []
        packages_to_update = []

        attachments_to_create = []
        attachments_to_update = []

        # ============================================================
        # ✅ المفاتيح الموجودة في Sheet
        # ============================================================

        sheet_package_keys = set()

        # ============================================================
        # ✅ بيانات الـDrive الخاصة بكل Package
        # ============================================================

        attachment_payloads = {}

        # ============================================================
        # ✅ Processing
        # ============================================================

        print("⏳ Processing rows...")

        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(
            dataframe.to_dict("records"),
            start=1,
        ):

            # ========================================================
            # الأعمدة الأساسية Sheet 1
            # ========================================================

            company_name = ImportHelpers.normalize_text(
                row.get(0, "")
            )

            contract_type = ImportHelpers.normalize_text(
                row.get(1, "")
            )

            package_name = ImportHelpers.normalize_text(
                row.get(2, "")
            )

            package_name = (
                PackageCatalogImportService.truncate_text(
                    package_name,
                    255,
                    result,
                )
            )

            specialty_name = ImportHelpers.normalize_text(
                row.get(3, "")
            )

            specialty_name = (
                PackageCatalogImportService.truncate_text(
                    specialty_name,
                    255,
                    result,
                )
            )

            # ========================================================
            # السعر
            # ========================================================

            price_value = ImportHelpers.clean_decimal(
                row.get(4, None)
            )

            # ========================================================
            # مدة الإقامة
            # ========================================================

            stay_duration = ImportHelpers.normalize_text(
                row.get(5, "")
            )

            # ========================================================
            # الكود
            # ========================================================

            package_code = ImportHelpers.normalize_text(
                row.get(6, "")
            )

            # ========================================================
            # التواريخ
            # ========================================================

            valid_from = row.get(7, "")
            valid_until = row.get(8, "")

            # ========================================================
            # ملاحظات
            # ========================================================

            package_note = ImportHelpers.normalize_text(
                row.get(9, "")
            )

            # ========================================================
            # قيم افتراضية
            # ========================================================

            if not package_code:

                package_code = (
                    f"UNKNOWN_CODE_{index}"
                )

            if not package_name:

                package_name = (
                    f"UNKNOWN_PACKAGE_{index}"
                )

            # ========================================================
            # تخطي الصفوف الفارغة
            # ========================================================

            if not package_code and not package_name:

                result["skipped"] = (
                    result.get("skipped", 0) + 1
                )

                continue

            # ========================================================
            # Entity
            # ========================================================

            entity = entities_cache.get(
                company_name
            )

            if not entity:

                continue

            # ========================================================
            # Package Key
            # ========================================================

            package_key = (
                entity.id,
                package_code,
                package_name,
            )

            sheet_package_keys.add(
                package_key
            )

            # ========================================================
            # Drive Attachment Data
            # ========================================================

            attachment_payloads[
                package_key
            ] = (
                PackageCatalogImportService
                .build_attachment_data(
                    drive_links,
                    index - 1,
                )
            )

            # ========================================================
            # Processed
            # ========================================================

            result["processed"] += 1

            processed = result["processed"]

            # ========================================================
            # Specialty
            # ========================================================

            specialty = None

            if specialty_name:

                specialty = specialties_cache.get(
                    specialty_name
                )

                if not specialty:

                    specialty = Specialty.objects.create(
                        name=specialty_name,
                        is_active=True,
                    )

                    specialties_cache[
                        specialty_name
                    ] = specialty

                    result[
                        "created_specialties"
                    ] += 1

            # ========================================================
            # Existing Package
            # ========================================================

            existing_package = packages_cache.get(
                package_key
            )

            if existing_package:

                changed = False

                if existing_package.name != package_name:

                    existing_package.name = package_name
                    changed = True

                if existing_package.specialty_id != (
                    specialty.id
                    if specialty
                    else None
                ):

                    existing_package.specialty = specialty
                    changed = True

                if (
                    existing_package.stay_duration
                    != stay_duration
                ):

                    existing_package.stay_duration = (
                        stay_duration
                    )

                    changed = True

                if (
                    existing_package.package_note
                    != package_note
                ):

                    existing_package.package_note = (
                        package_note
                    )

                    changed = True

                if (
                    existing_package.base_price
                    != price_value
                ):

                    existing_package.base_price = (
                        price_value
                    )

                    changed = True

                if existing_package.is_active is not True:

                    existing_package.is_active = True
                    changed = True

                if changed:

                    packages_to_update.append(
                        existing_package
                    )

                    result["updated"] += 1

            # ========================================================
            # New Package
            # ========================================================

            else:

                new_package = Package(
                    code=package_code,
                    name=package_name,
                    specialty=specialty,
                    entity=entity,
                    base_price=price_value,
                    stay_duration=stay_duration,
                    package_note=package_note,
                    is_active=True,
                )

                packages_to_create.append(
                    new_package
                )

                packages_cache[
                    package_key
                ] = new_package

                result["created"] += 1

            # ========================================================
            # Progress
            # ========================================================

            if processed % 1000 == 0:

                print(
                    f"   📊 Processed "
                    f"{processed}/{total_rows} rows..."
                )

        print(
            f"   ✅ Processed "
            f"{processed}/{total_rows} rows"
        )

        # ============================================================
        # ✅ Create Packages
        # ============================================================

        print(
            f"💾 Creating "
            f"{len(packages_to_create)} packages..."
        )

        print(
            f"💾 Updating "
            f"{len(packages_to_update)} packages..."
        )

        if packages_to_create or packages_to_update:
            close_old_connections()

            with transaction.atomic():
                if packages_to_create:
                    Package.objects.bulk_create(
                        packages_to_create,
                        batch_size=1000,
                    )

                # ========================================================
                # ✅ Update Packages
                # ========================================================

                if packages_to_update:
                    Package.objects.bulk_update(
                        packages_to_update,
                        fields=[
                            "name",
                            "specialty",
                            "stay_duration",
                            "base_price",
                            "package_note",
                            "is_active",
                        ],
                        batch_size=1000,
                    )

            close_old_connections()

        # bulk_create() on PostgreSQL populates primary keys, and the
        # newly-created objects are already present in packages_cache.
        # No second full-table SELECT is needed here.

        # ============================================================
        # ✅ Prepare Package Attachments
        # ============================================================

        print(
            "⏳ Processing Package Drive attachments..."
        )

        # attachments_cache was loaded once at the beginning.
        # No second full-table SELECT is needed here.

        # ============================================================
        # إنشاء / تحديث Attachments
        # ============================================================

        for package_key, payload in (
            attachment_payloads.items()
        ):

            package = packages_cache.get(
                package_key
            )

            if not package:
                continue

            existing_attachment = (
                attachments_cache.get(
                    package.id
                )
            )

            if existing_attachment:

                changed = False

                # ----------------------------------------------------
                # Package PDF
                # ----------------------------------------------------

                if (
                    existing_attachment.package_pdf_name
                    != payload["package_pdf_name"]
                ):

                    existing_attachment.package_pdf_name = (
                        payload["package_pdf_name"]
                    )

                    changed = True

                if (
                    existing_attachment.package_pdf_url
                    != payload["package_pdf_url"]
                ):

                    existing_attachment.package_pdf_url = (
                        payload["package_pdf_url"]
                    )

                    changed = True

                if (
                    existing_attachment.package_pdf_drive_id
                    != payload["package_pdf_drive_id"]
                ):

                    existing_attachment.package_pdf_drive_id = (
                        payload["package_pdf_drive_id"]
                    )

                    changed = True

                # ----------------------------------------------------
                # Operation Instruction
                # ----------------------------------------------------

                if (
                    existing_attachment.operation_instruction_name
                    != payload[
                        "operation_instruction_name"
                    ]
                ):

                    existing_attachment.operation_instruction_name = (
                        payload[
                            "operation_instruction_name"
                        ]
                    )

                    changed = True

                if (
                    existing_attachment.operation_instruction_url
                    != payload[
                        "operation_instruction_url"
                    ]
                ):

                    existing_attachment.operation_instruction_url = (
                        payload[
                            "operation_instruction_url"
                        ]
                    )

                    changed = True

                if (
                    existing_attachment.operation_instruction_drive_id
                    != payload[
                        "operation_instruction_drive_id"
                    ]
                ):

                    existing_attachment.operation_instruction_drive_id = (
                        payload[
                            "operation_instruction_drive_id"
                        ]
                    )

                    changed = True

                if changed:

                    attachments_to_update.append(
                        existing_attachment
                    )

                    result[
                        "updated_attachments"
                    ] += 1

            else:

                # ----------------------------------------------------
                # لا ننشئ Attachment فاضي تمامًا
                # ----------------------------------------------------

                has_drive_data = any(
                    payload.values()
                )

                if not has_drive_data:
                    continue

                attachment = PackageAttachment(
                    package=package,

                    package_pdf_name=(
                        payload[
                            "package_pdf_name"
                        ]
                    ),

                    package_pdf_url=(
                        payload[
                            "package_pdf_url"
                        ]
                    ),

                    package_pdf_drive_id=(
                        payload[
                            "package_pdf_drive_id"
                        ]
                    ),

                    operation_instruction_name=(
                        payload[
                            "operation_instruction_name"
                        ]
                    ),

                    operation_instruction_url=(
                        payload[
                            "operation_instruction_url"
                        ]
                    ),

                    operation_instruction_drive_id=(
                        payload[
                            "operation_instruction_drive_id"
                        ]
                    ),
                )

                attachments_to_create.append(
                    attachment
                )

                result[
                    "created_attachments"
                ] += 1

        # ============================================================
        # ✅ Bulk Create Attachments
        # ============================================================

        if attachments_to_create or attachments_to_update:
            close_old_connections()

            with transaction.atomic():
                if attachments_to_create:

                    print(
                        f"💾 Creating "
                        f"{len(attachments_to_create)} "
                        f"package attachments..."
                    )

                    PackageAttachment.objects.bulk_create(
                        attachments_to_create,
                        batch_size=1000,
                    )

                # ========================================================
                # ✅ Bulk Update Attachments
                # ========================================================

                if attachments_to_update:

                    print(
                        f"💾 Updating "
                        f"{len(attachments_to_update)} "
                        f"package attachments..."
                    )

                    PackageAttachment.objects.bulk_update(
                        attachments_to_update,
                        fields=[
                            "package_pdf_name",
                            "package_pdf_url",
                            "package_pdf_drive_id",
                            "operation_instruction_name",
                            "operation_instruction_url",
                            "operation_instruction_drive_id",
                        ],
                        batch_size=1000,
                    )

            close_old_connections()

        # ============================================================
        # ✅ Delete Packages not found in Sheet
        # ============================================================

        if sheet_package_keys:

            packages_to_delete = []

            for package in Package.objects.all():

                key = (
                    package.entity_id,

                    ImportHelpers.normalize_text(
                        package.code
                    ),

                    ImportHelpers.normalize_text(
                        package.name
                    ),
                )

                if key not in sheet_package_keys:

                    packages_to_delete.append(
                        package.id
                    )

            if packages_to_delete:
                close_old_connections()

                with transaction.atomic():
                    deleted_count, _ = (
                        Package.objects.filter(
                            id__in=packages_to_delete
                        ).delete()
                    )

                print(
                    f"🗑️ Deleted "
                    f"{deleted_count} packages "
                    f"not in sheet"
                )

                result["deleted"] = (
                    deleted_count
                )

        else:

            print(
                "⚠️ No package keys in sheet "
                "- skipping deletion"
            )

        # ============================================================
        # ✅ Truncated Summary
        # ============================================================

        if result["truncated_texts"]:
            print(
                f"⚠️ Truncated texts: "
                f"{result['truncated_texts']}"
            )

        # ============================================================
        # ✅ Finish
        # ============================================================

        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            f"📎 Created attachments: "
            f"{result['created_attachments']}"
        )

        print(
            f"📎 Updated attachments: "
            f"{result['updated_attachments']}"
        )

        print(
            f"✅ Completed in "
            f"{elapsed:.2f} seconds"
        )

        return result