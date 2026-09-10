# imports/services/report_statistic_import_service.py

import pandas as pd
import time
from django.db import transaction

from pricing_requests.models import ReportStatistic
from imports.utils.import_helpers import ImportHelpers


class ReportStatisticImportService:

    # ============================================================
    # Sheet 11 Column Mapping
    # ============================================================
    COLUMN_MAPPING = {
        "medical_number": "الرقم الطبي",
        "account_number": "الرقم الحسابي",
        "patient_name": "اسم المريض",
        "admission_date": "تاريخ الدخول",
        "discharge_date": "تاريخ الخروج",
        "month": "الشهر",
        "specialty": "التخصص",
        "package_name": "اسم الباكدج",
        "department_name": "اسم القسم",
        "service_name_ar": "اسم الخدمة عربي",
        "procedure_date": "تاريخ الاجراء",
        "entity_name": "الجهه",
        "sector": "القطاع",
        "payment_type": "نوع الدفع",
        "sub_company": "الشركه الفرعيه",
        "amount": "سعر الباكدج",
        "invoice_amount": "قيمة الفاتوره",
        "code": "الكود",
        "patient_type": "نوع المريض",
        "stay_duration": "مدة الاقامة",
        "doctor_name": "اسم الطبيب",
    }

    REQUIRED_COLUMNS = list(COLUMN_MAPPING.values())

    # ============================================================
    # Import
    # ============================================================
    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()

        print(
            "⏳ Starting Report Statistics "
            "import from Sheet 11..."
        )

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
            "errors": 0,
        }

        # ========================================================
        # Header Validation & Mapping
        # ========================================================
        header_map = ImportHelpers.validate_required_columns(
            dataframe,
            ReportStatisticImportService.REQUIRED_COLUMNS,
        )

        print(
            "✅ Sheet 11 headers "
            "validated successfully"
        )

        # ========================================================
        # Data
        # ========================================================
        data = dataframe.copy()
        data = data.reset_index(drop=True)

        # ========================================================
        # Remove duplicated header row from Sheet 11
        # ========================================================
        if not data.empty:

            first_row = data.iloc[0]

            first_value = ImportHelpers.normalize_text(
                first_row.get("Item", "")
            )

            if first_value == "الرقم الطبي":

                print(
                    "⚠️ Detected duplicated header row in Sheet 11. "
                    "Removing it..."
                )

                data = data.iloc[1:].reset_index(drop=True)

        print(f"📊 Rows: {len(data)}")
        print("=" * 50)

        # ========================================================
        # Cache Existing Records
        # ========================================================
        print(
            "⏳ Loading existing report statistics..."
        )

        stats_cache = {}

        for stat in ReportStatistic.objects.all():

            key = (
                ImportHelpers.normalize_text(
                    stat.medical_number
                ),
                ImportHelpers.normalize_text(
                    stat.account_number
                ),
                ImportHelpers.normalize_text(
                    stat.code
                ),
                stat.procedure_date,
            )

            stats_cache[key] = stat

        print(
            f"   ✅ {len(stats_cache)} records loaded"
        )

        # ========================================================
        # Sheet Keys
        # ========================================================
        sheet_records = set()

        # ========================================================
        # Bulk Lists
        # ========================================================
        to_create = []
        to_update = []

        # ========================================================
        # Processing
        # ========================================================
        print("⏳ Processing rows...")

        total_rows = len(data)
        processed = 0

        for index, row in data.iterrows():

            try:

                # ====================================================
                # Medical Number
                # ====================================================
                medical_number = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "medical_number",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Account Number
                # ====================================================
                account_number = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "account_number",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Patient Name
                # ====================================================
                patient_name = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "patient_name",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Skip Empty Patient
                # ====================================================
                if not patient_name:

                    result["skipped"] += 1

                    continue

                # ====================================================
                # Admission Date
                # ====================================================
                admission_date = (
                    ImportHelpers.clean_date(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "admission_date",
                            ReportStatisticImportService.COLUMN_MAPPING,
                            default=None,
                        )
                    )
                )

                # ====================================================
                # Discharge Date
                # ====================================================
                discharge_date = (
                    ImportHelpers.clean_date(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "discharge_date",
                            ReportStatisticImportService.COLUMN_MAPPING,
                            default=None,
                        )
                    )
                )

                # ====================================================
                # Month
                # ====================================================
                month = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "month",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Specialty
                # ====================================================
                specialty = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "specialty",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Package
                # ====================================================
                package_name = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "package_name",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Entity
                # ====================================================
                entity_name = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "entity_name",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Sector
                # ====================================================
                sector = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "sector",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Payment Type
                # ====================================================
                payment_type = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "payment_type",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Sub Company
                # ====================================================
                sub_company = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "sub_company",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Amount
                # Sheet 11 -> سعر الباكدج
                # ====================================================
                amount = (
                    ImportHelpers.clean_amount(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "amount",
                            ReportStatisticImportService.COLUMN_MAPPING,
                            default=0,
                        )
                    )
                )

                # ====================================================
                # Invoice Amount
                # ====================================================
                invoice_amount = (
                    ImportHelpers.clean_amount(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "invoice_amount",
                            ReportStatisticImportService.COLUMN_MAPPING,
                            default=0,
                        )
                    )
                )

                # ====================================================
                # Code
                # ====================================================
                code = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "code",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Patient Type
                # ====================================================
                patient_type = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "patient_type",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Stay Duration
                # ====================================================
                stay_duration = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "stay_duration",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Department Name
                # ====================================================
                department_name = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "department_name",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Service Name Arabic
                # ====================================================
                service_name_ar = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "service_name_ar",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Procedure Date
                # ====================================================
                procedure_date = (
                    ImportHelpers.clean_datetime(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "procedure_date",
                            ReportStatisticImportService.COLUMN_MAPPING,
                            default=None,
                        )
                    )
                )

                # ====================================================
                # Doctor Name
                # ====================================================
                doctor_name = (
                    ImportHelpers.normalize_text(
                        ImportHelpers.get_mapped_value(
                            row,
                            header_map,
                            "doctor_name",
                            ReportStatisticImportService.COLUMN_MAPPING,
                        )
                    )
                )

                # ====================================================
                # Processed
                # ====================================================
                result["processed"] += 1
                processed = result["processed"]

                # ====================================================
                # Record Key
                # ====================================================
                key = (
                    medical_number,
                    account_number,
                    code,
                    procedure_date,
                )

                sheet_records.add(key)

                existing_stat = stats_cache.get(key)

                # ====================================================
                # UPDATE
                # ====================================================
                if existing_stat:

                    changed = False

                    if existing_stat.patient_name != patient_name:
                        existing_stat.patient_name = patient_name
                        changed = True

                    if existing_stat.admission_date != admission_date:
                        existing_stat.admission_date = admission_date
                        changed = True

                    if existing_stat.discharge_date != discharge_date:
                        existing_stat.discharge_date = discharge_date
                        changed = True

                    if existing_stat.month != month:
                        existing_stat.month = month
                        changed = True

                    if existing_stat.specialty != specialty:
                        existing_stat.specialty = specialty
                        changed = True

                    if existing_stat.package_name != package_name:
                        existing_stat.package_name = package_name
                        changed = True

                    if existing_stat.department_name != department_name:
                        existing_stat.department_name = department_name
                        changed = True

                    if existing_stat.service_name_ar != service_name_ar:
                        existing_stat.service_name_ar = service_name_ar
                        changed = True

                    if existing_stat.procedure_date != procedure_date:
                        existing_stat.procedure_date = procedure_date
                        changed = True

                    if existing_stat.entity_name != entity_name:
                        existing_stat.entity_name = entity_name
                        changed = True

                    if existing_stat.sector != sector:
                        existing_stat.sector = sector
                        changed = True

                    if existing_stat.payment_type != payment_type:
                        existing_stat.payment_type = payment_type
                        changed = True

                    if existing_stat.sub_company != sub_company:
                        existing_stat.sub_company = sub_company
                        changed = True

                    if existing_stat.amount != amount:
                        existing_stat.amount = amount
                        changed = True

                    if existing_stat.invoice_amount != invoice_amount:
                        existing_stat.invoice_amount = invoice_amount
                        changed = True

                    if existing_stat.code != code:
                        existing_stat.code = code
                        changed = True

                    if existing_stat.patient_type != patient_type:
                        existing_stat.patient_type = patient_type
                        changed = True

                    if existing_stat.stay_duration != stay_duration:
                        existing_stat.stay_duration = stay_duration
                        changed = True

                    if existing_stat.doctor_name != doctor_name:
                        existing_stat.doctor_name = doctor_name
                        changed = True

                    if changed:

                        to_update.append(
                            existing_stat
                        )

                        result["updated"] += 1

                # ====================================================
                # CREATE
                # ====================================================
                else:

                    stat = ReportStatistic(

                        medical_number=medical_number,

                        account_number=account_number,

                        patient_name=patient_name,

                        admission_date=admission_date,

                        discharge_date=discharge_date,

                        month=month,

                        specialty=specialty,

                        package_name=package_name,

                        entity_name=entity_name,

                        sector=sector,

                        payment_type=payment_type,

                        sub_company=sub_company,

                        amount=amount,

                        invoice_amount=invoice_amount,

                        code=code,

                        patient_type=patient_type,

                        stay_duration=stay_duration,

                        department_name=department_name,

                        service_name_ar=service_name_ar,

                        procedure_date=procedure_date,

                        doctor_name=doctor_name,

                    )

                    to_create.append(stat)

                    stats_cache[key] = stat

                    result["created"] += 1

                # ====================================================
                # Progress
                # ====================================================
                if processed % 1000 == 0:

                    print(
                        f"   📊 Processed "
                        f"{processed}/{total_rows} rows..."
                    )

            except Exception as e:

                result["errors"] += 1

                if result["errors"] <= 10:

                    print(
                        f"   ❌ Error in row "
                        f"{index + 2}: "
                        f"{str(e)[:120]}..."
                    )

                continue

        # ============================================================
        # Processing Finished
        # ============================================================
        print(
            f"   ✅ Processed "
            f"{processed}/{total_rows} rows"
        )

        # ============================================================
        # Bulk Operations
        # ============================================================
        BATCH_SIZE = 500

        print(
            f"💾 Creating "
            f"{len(to_create)} records..."
        )

        print(
            f"💾 Updating "
            f"{len(to_update)} records..."
        )

        # ============================================================
        # Bulk Create
        # ============================================================
        if to_create:

            ReportStatistic.objects.bulk_create(
                to_create,
                batch_size=BATCH_SIZE,
            )

        # ============================================================
        # Bulk Update
        # ============================================================
        if to_update:

            total_updated = 0

            for i in range(
                0,
                len(to_update),
                BATCH_SIZE,
            ):

                batch = to_update[
                    i:i + BATCH_SIZE
                ]

                ReportStatistic.objects.bulk_update(

                    batch,

                    fields=[

                        "patient_name",

                        "admission_date",

                        "discharge_date",

                        "month",

                        "specialty",

                        "package_name",

                        "entity_name",

                        "sector",

                        "payment_type",

                        "sub_company",

                        "amount",

                        "invoice_amount",

                        "code",

                        "patient_type",

                        "stay_duration",

                        "department_name",

                        "service_name_ar",

                        "procedure_date",

                        "doctor_name",

                    ],

                    batch_size=100,

                )

                total_updated += len(batch)

                print(
                    f"   ✅ Updated batch "
                    f"{i // BATCH_SIZE + 1} "
                    f"({total_updated}/"
                    f"{len(to_update)})"
                )

        # ============================================================
        # Delete Records Not Found in Sheet
        # ============================================================
        #
        # ملاحظة:
        # لا نحذف إلا بعد نجاح معالجة الشيت.
        #
        # ============================================================
        stats_cache = {}

        for stat in ReportStatistic.objects.all():

            key = (
                ImportHelpers.normalize_text(
                    stat.medical_number
                ),
                ImportHelpers.normalize_text(
                    stat.account_number
                ),
                ImportHelpers.normalize_text(
                    stat.code
                ),
                stat.procedure_date,
            )

            stats_cache[key] = stat

        to_delete = []

        for key, stat in stats_cache.items():

            if key not in sheet_records:

                to_delete.append(stat.id)

        if to_delete:

            deleted, _ = (
                ReportStatistic.objects
                .filter(id__in=to_delete)
                .delete()
            )

            result["deleted"] = deleted

            print(
                f"🗑️ Deleted {deleted} records"
            )

        # ============================================================
        # Final Result
        # ============================================================
        elapsed = (
            time.perf_counter()
            - start_time
        )

        print(
            "\n"
            + "=" * 80
        )

        print(
            "✅ انتهى الاستيراد بنجاح!"
        )

        print(
            f"📊 Processed: "
            f"{result['processed']}, "
            f"Created: "
            f"{result['created']}, "
            f"Updated: "
            f"{result['updated']}, "
            f"Deleted: "
            f"{result['deleted']}, "
            f"Skipped: "
            f"{result['skipped']}"
        )

        if result["errors"]:

            print(
                f"❌ Errors: "
                f"{result['errors']}"
            )

        print("=" * 80)

        print(
            f"⏱️ Completed in "
            f"{elapsed:.2f} seconds"
        )

        return result