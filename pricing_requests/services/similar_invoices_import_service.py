import time
from decimal import Decimal

from django.db import transaction

from pricing_requests.models import SimilarInvoice
from imports.utils.import_helpers import ImportHelpers


class SimilarInvoicesImportService:

    COLUMN_MAPPING = {
        "account_number": "الرقم الحسابي",
        "medical_number": "الرقم الطبي",
        "patient_name": "اسم المريض",
        "admission_date": "تاريخ الدخول",
        "discharge_date": "تاريخ الخروج",
        "entity_name": "الجهه",
        "building": "الدور",
        "room": "الغرفة",
        "doctor_name": "اسم الطبيب",
        "specialty_name": "التخصص",
        "admission_status": "حالة الدخول",
        "admission_type": "نوع الدخول",
        "total_invoice": "اجمالي الفاتوره",
        "discount": "الخصم",
        "net_invoice": "صافي الفاتوره",
        "company_share": "حصة الشركه",
        "patient_share": "حصة المريض",
        "payments": "المدفوعات",
        "balance": "الرصيد",
        "invoice_status": "حالة الفاتورة",
        "invoice_closed_date": "تاريخ انهاء الفاتوره",
        "operating_room_opened": "فتح غرفة العمليات",
        "operation_name": "اسم العمليه",
        "sub_company": "الشركة الفرعية",
        "notes": "ملاحظات",
        "operation_description": "توصيف العمليه",
        "stay_duration": "مدة الاقامه",
    }

    @staticmethod
    def truncate_text(value, max_length=255, counters=None):
        """تقليص النص إذا تجاوز الحد الأقصى."""

        if not value:
            return value

        cleaned = ImportHelpers.normalize_text(value)

        if len(cleaned) > max_length:
            if counters is not None:
                counters["truncated_texts"] += 1

            return cleaned[:max_length]

        return cleaned

    @staticmethod
    def get_value(row, header_map, field_name, default=""):
        """
        قراءة قيمة من الصف باستخدام اسم الحقل والـ Header Mapping.
        """

        return ImportHelpers.get_mapped_value(
            row=row,
            header_map=header_map,
            field_name=field_name,
            column_mapping=SimilarInvoicesImportService.COLUMN_MAPPING,
            default=default,
        )

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()

        print("⏳ Starting Similar Invoices import from Sheet 10...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
            "truncated_texts": 0,
            "missing_patient_name": 0,
            "missing_operation_name": 0,
        }

        # ============================================================
        # التحقق من وجود بيانات
        # ============================================================

        if len(dataframe) == 0:
            return result

        # ============================================================
        # ✅ استبدال: حذف تحويل أول صف إلى Headers
        # ============================================================

        dataframe = dataframe.reset_index(drop=True)

        header_map = {
            ImportHelpers.normalize_header(column): column
            for column in dataframe.columns
        }

        print("✅ Sheet 10 headers mapped successfully")
        print("   Headers:", list(header_map.keys()))

        # ============================================================
        # التحقق من الأعمدة المطلوبة
        # ============================================================

        required_columns = [
            "الرقم الحسابي",
            "الرقم الطبي",
            "اسم المريض",
            "تاريخ الدخول",
            "تاريخ الخروج",
            "التخصص",
            "اسم الطبيب",
            "اسم العمليه",
            "الجهه",
            "الشركة الفرعية",
            "الدور",
            "الغرفة",
            "اجمالي الفاتوره",
            "الخصم",
            "صافي الفاتوره",
            "حصة الشركه",
            "حصة المريض",
            "المدفوعات",
            "الرصيد",
            "حالة الفاتورة",
            "تاريخ انهاء الفاتوره",
            "ملاحظات",
            "توصيف العمليه",
            "مدة الاقامه",
            "حالة الدخول",
            "نوع الدخول",
            "فتح غرفة العمليات",
        ]

        ImportHelpers.validate_required_columns(
            dataframe,
            required_columns,
        )

        # ============================================================
        # Cache للـ Similar Invoices
        # ============================================================

        print("⏳ Loading existing similar invoices...")

        records_cache = {}

        for record in SimilarInvoice.objects.all():

            key = (
                ImportHelpers.normalize_text(
                    record.account_number or ""
                ),
                ImportHelpers.normalize_text(
                    record.medical_number or ""
                ),
                record.admission_date,
                ImportHelpers.normalize_text(
                    record.operation_name or ""
                ),
            )

            records_cache[key] = record

        print(
            f"   ✅ {len(records_cache)} records loaded"
        )

        # ============================================================
        # Bulk Operations
        # ============================================================

        to_create = []
        to_update = []
        sheet_records = set()

        # ============================================================
        # Processing
        # ============================================================

        print("⏳ Processing rows...")

        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(
            dataframe.to_dict("records"),
            start=1,
        ):

            # ========================================================
            # البيانات الأساسية
            # ========================================================

            account_number = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "account_number",
                )
            )

            if not account_number:
                result["skipped"] += 1
                continue

            medical_number = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "medical_number",
                )
            )

            patient_name = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "patient_name",
                )
            )

            admission_date = ImportHelpers.clean_date_dmy(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "admission_date",
                    default=None,
                )
            )

            discharge_date = ImportHelpers.clean_date_dmy(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "discharge_date",
                    default=None,
                )
            )

            # ========================================================
            # بيانات الطبيب والتخصص والعملية
            # ========================================================

            specialty_name = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "specialty_name",
                )
            )

            specialty_name = (
                SimilarInvoicesImportService.truncate_text(
                    specialty_name,
                    255,
                    result,
                )
            )

            doctor_name = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "doctor_name",
                )
            )

            doctor_name = (
                SimilarInvoicesImportService.truncate_text(
                    doctor_name,
                    255,
                    result,
                )
            )

            operation_name = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "operation_name",
                )
            )

            operation_name = (
                SimilarInvoicesImportService.truncate_text(
                    operation_name,
                    255,
                    result,
                )
            )

            entity_name = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "entity_name",
                )
            )

            entity_name = (
                SimilarInvoicesImportService.truncate_text(
                    entity_name,
                    255,
                    result,
                )
            )

            building = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "building",
                )
            )

            building = (
                SimilarInvoicesImportService.truncate_text(
                    building,
                    255,
                    result,
                )
            )

            room = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "room",
                )
            )

            room = (
                SimilarInvoicesImportService.truncate_text(
                    room,
                    255,
                    result,
                )
            )

            sub_company = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "sub_company",
                )
            )

            sub_company = (
                SimilarInvoicesImportService.truncate_text(
                    sub_company,
                    255,
                    result,
                )
            )

            # ========================================================
            # حالة الدخول ونوعه
            # ========================================================

            admission_status = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "admission_status",
                )
            )

            admission_status = (
                SimilarInvoicesImportService.truncate_text(
                    admission_status,
                    255,
                    result,
                )
            )

            admission_type = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "admission_type",
                )
            )

            admission_type = (
                SimilarInvoicesImportService.truncate_text(
                    admission_type,
                    255,
                    result,
                )
            )

            # ========================================================
            # البيانات المالية
            # ========================================================

            total_invoice = ImportHelpers.clean_decimal(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "total_invoice",
                    default=None,
                )
            )

            if total_invoice is None:
                total_invoice = Decimal("0.00")

            discount = ImportHelpers.clean_decimal(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "discount",
                    default=None,
                )
            )

            if discount is None:
                discount = Decimal("0.00")

            net_invoice = ImportHelpers.clean_decimal(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "net_invoice",
                    default=None,
                )
            )

            if net_invoice is None:
                net_invoice = Decimal("0.00")

            company_share = ImportHelpers.clean_decimal(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "company_share",
                    default=None,
                )
            )

            if company_share is None:
                company_share = Decimal("0.00")

            patient_share = ImportHelpers.clean_decimal(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "patient_share",
                    default=None,
                )
            )

            if patient_share is None:
                patient_share = Decimal("0.00")

            payments = ImportHelpers.clean_decimal(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "payments",
                    default=None,
                )
            )

            if payments is None:
                payments = Decimal("0.00")

            balance = ImportHelpers.clean_decimal(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "balance",
                    default=None,
                )
            )

            if balance is None:
                balance = Decimal("0.00")

            # ========================================================
            # باقي البيانات
            # ========================================================

            invoice_status = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "invoice_status",
                )
            )

            invoice_status = (
                SimilarInvoicesImportService.truncate_text(
                    invoice_status,
                    100,
                    result,
                )
            )

            invoice_closed_date = ImportHelpers.clean_date(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "invoice_closed_date",
                    default=None,
                )
            )

            operating_room_opened = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "operating_room_opened",
                )
            )

            operating_room_opened = (
                SimilarInvoicesImportService.truncate_text(
                    operating_room_opened,
                    255,
                    result,
                )
            )

            notes = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "notes",
                )
            )

            notes = (
                SimilarInvoicesImportService.truncate_text(
                    notes,
                    255,
                    result,
                )
            )

            operation_description = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "operation_description",
                )
            )

            stay_duration = ImportHelpers.normalize_text(
                SimilarInvoicesImportService.get_value(
                    row,
                    header_map,
                    "stay_duration",
                )
            )

            stay_duration = (
                SimilarInvoicesImportService.truncate_text(
                    stay_duration,
                    100,
                    result,
                )
            )

            # ========================================================
            # قيم افتراضية
            # ========================================================

            if not patient_name:
                patient_name = (
                    f"UNKNOWN_PATIENT_{index}"
                )

                result["missing_patient_name"] += 1

            if not operation_name:
                operation_name = (
                    f"UNKNOWN_OPERATION_{index}"
                )

                result["missing_operation_name"] += 1

            # ========================================================
            # Processed
            # ========================================================

            result["processed"] += 1
            processed = result["processed"]

            # ========================================================
            # Cache Key
            # ========================================================

            key = (
                account_number,
                medical_number,
                admission_date,
                operation_name,
            )

            sheet_records.add(key)

            existing_record = records_cache.get(key)

            # ========================================================
            # Update
            # ========================================================

            if existing_record:

                changed = False

                if existing_record.patient_name != patient_name:
                    existing_record.patient_name = patient_name
                    changed = True

                if existing_record.discharge_date != discharge_date:
                    existing_record.discharge_date = discharge_date
                    changed = True

                if existing_record.entity_name != entity_name:
                    existing_record.entity_name = entity_name
                    changed = True

                if existing_record.building != building:
                    existing_record.building = building
                    changed = True

                if existing_record.room != room:
                    existing_record.room = room
                    changed = True

                if existing_record.sub_company != sub_company:
                    existing_record.sub_company = sub_company
                    changed = True

                if existing_record.doctor_name != doctor_name:
                    existing_record.doctor_name = doctor_name
                    changed = True

                if existing_record.specialty_name != specialty_name:
                    existing_record.specialty_name = specialty_name
                    changed = True

                if existing_record.admission_status != admission_status:
                    existing_record.admission_status = admission_status
                    changed = True

                if existing_record.admission_type != admission_type:
                    existing_record.admission_type = admission_type
                    changed = True

                if existing_record.total_invoice != total_invoice:
                    existing_record.total_invoice = total_invoice
                    changed = True

                if existing_record.discount != discount:
                    existing_record.discount = discount
                    changed = True

                if existing_record.net_invoice != net_invoice:
                    existing_record.net_invoice = net_invoice
                    changed = True

                if existing_record.company_share != company_share:
                    existing_record.company_share = company_share
                    changed = True

                if existing_record.patient_share != patient_share:
                    existing_record.patient_share = patient_share
                    changed = True

                if existing_record.payments != payments:
                    existing_record.payments = payments
                    changed = True

                if existing_record.balance != balance:
                    existing_record.balance = balance
                    changed = True

                if existing_record.invoice_status != invoice_status:
                    existing_record.invoice_status = invoice_status
                    changed = True

                if existing_record.invoice_closed_date != invoice_closed_date:
                    existing_record.invoice_closed_date = invoice_closed_date
                    changed = True

                if existing_record.operating_room_opened != operating_room_opened:
                    existing_record.operating_room_opened = operating_room_opened
                    changed = True

                if existing_record.notes != notes:
                    existing_record.notes = notes
                    changed = True

                if existing_record.operation_description != operation_description:
                    existing_record.operation_description = operation_description
                    changed = True

                if existing_record.stay_duration != stay_duration:
                    existing_record.stay_duration = stay_duration
                    changed = True

                if changed:
                    to_update.append(existing_record)
                    result["updated"] += 1

            # ========================================================
            # Create
            # ========================================================

            else:

                record = SimilarInvoice(
                    account_number=account_number,
                    medical_number=medical_number,
                    patient_name=patient_name,
                    admission_date=admission_date,
                    discharge_date=discharge_date,
                    entity_name=entity_name,
                    building=building,
                    room=room,
                    specialty_name=specialty_name,
                    doctor_name=doctor_name,
                    operation_name=operation_name,
                    total_invoice=total_invoice,
                    discount=discount,
                    net_invoice=net_invoice,
                    company_share=company_share,
                    patient_share=patient_share,
                    payments=payments,
                    balance=balance,
                    invoice_status=invoice_status,
                    invoice_closed_date=invoice_closed_date,
                    sub_company=sub_company,
                    admission_status=admission_status,
                    admission_type=admission_type,
                    operating_room_opened=operating_room_opened,
                    notes=notes,
                    operation_description=operation_description,
                    stay_duration=stay_duration,
                )

                to_create.append(record)
                records_cache[key] = record
                result["created"] += 1

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
        # Bulk Create / Update
        # ============================================================

        print(
            f"💾 Creating {len(to_create)} records..."
        )

        print(
            f"💾 Updating {len(to_update)} records..."
        )

        BATCH_SIZE = 500

        if to_create:
            SimilarInvoice.objects.bulk_create(
                to_create,
                batch_size=BATCH_SIZE,
            )

        if to_update:

            total_updated = 0

            update_fields = [
                "patient_name",
                "discharge_date",
                "entity_name",
                "building",
                "room",
                "doctor_name",
                "specialty_name",
                "admission_status",
                "admission_type",
                "total_invoice",
                "discount",
                "net_invoice",
                "company_share",
                "patient_share",
                "payments",
                "balance",
                "invoice_status",
                "invoice_closed_date",
                "sub_company",
                "operating_room_opened",
                "notes",
                "operation_description",
                "stay_duration",
            ]

            for i in range(
                0,
                len(to_update),
                BATCH_SIZE,
            ):

                batch = to_update[
                    i:i + BATCH_SIZE
                ]

                SimilarInvoice.objects.bulk_update(
                    batch,
                    fields=update_fields,
                    batch_size=100,
                )

                total_updated += len(batch)

                print(
                    f"   ✅ Updated batch "
                    f"{i // BATCH_SIZE + 1} "
                    f"({total_updated}/{len(to_update)})"
                )

        # ============================================================
        # Reload Cache
        # ============================================================

        records_cache = {}

        for record in SimilarInvoice.objects.all():

            key = (
                ImportHelpers.normalize_text(
                    record.account_number or ""
                ),
                ImportHelpers.normalize_text(
                    record.medical_number or ""
                ),
                record.admission_date,
                ImportHelpers.normalize_text(
                    record.operation_name or ""
                ),
            )

            records_cache[key] = record

        # ============================================================
        # Delete Records not found in Sheet
        # ============================================================

        to_delete = []

        for key, record in records_cache.items():

            if key not in sheet_records:
                to_delete.append(record.id)

        if to_delete:

            deleted, _ = (
                SimilarInvoice.objects
                .filter(id__in=to_delete)
                .delete()
            )

            result["deleted"] = deleted

            print(
                f"🗑️ Deleted {deleted} records"
            )

        # ============================================================
        # Truncated Summary
        # ============================================================

        if result["truncated_texts"]:
            print(
                f"⚠️ Truncated texts: "
                f"{result['truncated_texts']}"
            )

        # ============================================================
        # Missing Data Summary
        # ============================================================

        if (
            result["missing_patient_name"]
            or result["missing_operation_name"]
        ):
            print(
                f"⚠️ Missing patient names: "
                f"{result['missing_patient_name']}, "
                f"missing operation names: "
                f"{result['missing_operation_name']}"
            )

        # ============================================================
        # Finished
        # ============================================================

        elapsed = time.perf_counter() - start_time

        print(
            f"✅ Completed in {elapsed:.2f} seconds"
        )

        return result