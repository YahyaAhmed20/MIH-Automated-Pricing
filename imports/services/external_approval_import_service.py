import time
from decimal import Decimal

from django.db import transaction

from pricing_requests.models import ExternalApproval
from imports.utils.import_helpers import ImportHelpers


def build_key(
    patient_name,
    card_number,
    procedure,
    date,
    doctor_name,
):
    """Build a stable unique key for ExternalApproval."""

    card_number = ImportHelpers.normalize_text(card_number or "")
    patient_name = ImportHelpers.normalize_text(patient_name or "")
    procedure = ImportHelpers.normalize_text(procedure or "")
    doctor_name = ImportHelpers.normalize_text(doctor_name or "")

    if card_number:
        return (
            "card",
            card_number,
            procedure,
            date,
        )

    return (
        "patient",
        patient_name,
        procedure,
        date,
        doctor_name,
    )


class ExternalApprovalImportService:

    # ============================================================
    # Sheet 12 → Model Field Mapping
    # ============================================================

    COLUMN_MAPPING = {
        "attachment_type": "ملحق او رئيسى",
        "patient_name": "اسم المريض",
        "card_number": "رقم الــكـارنية",
        "company": "الشــركــة",
        "sub_account": "Sub Account",
        "date": "التاريخ",
        "medical_number": "الرقم الطبي",
        "doctor_name": "الطبيب",
        "specialty": "التخصص",
        "required": "المطلوب",
        "procedure": "الاجراء",
        "phone": "رقم التليفون",
        "agent_1": "Agent 1",
        "status": "Status",
        "main_status": "Main Status",
        "initial_cost": "التكلفه المبدئية",
        "pricing_date": "تاريخ التسعير",
        "pricing_responsible": "مسئول التسعير",
        "billing_status": "Billing Status",
        "approval_review_responsible": (
            "مسئول مراجعة الموافقة و التسعير"
        ),
        "accounts_notes": "ملاحظات الحسابات",
        "account_number": "الرقم الحسابى",
        "received_cost": "التكلفة المستلمه",
        "report": "New Reprt",
        "approval": "New Approval",
        "request_approval_no": "Request and Approval NO.",
        "approval_date": "Approval Date",
        "expiry_date": "Expiry Date",
        "notes": "الملاحظات",
        "last_update": "Last Update",
        "agent_2": "Agent 2",
        "or_agent": "OR Agent",
        "opd_sales_cs": "OPD ,Sales or CS",
        "admission_date": "تاريخ الدخول",
        "or_coordinator_notes": (
            "ملاحظات الـ OR Coordinator"
        ),
        "sales_account": "sales account",
        "head": "Head",
        "user": "USER",
        "sales_notes": "ملاحظات السيلز",
    }

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def get_value(
        row,
        header_map,
        field_name,
        default="",
    ):
        return ImportHelpers.get_mapped_value(
            row=row,
            header_map=header_map,
            field_name=field_name,
            column_mapping=ExternalApprovalImportService.COLUMN_MAPPING,
            default=default,
        )

    @staticmethod
    def normalize_optional_text(value):
        value = ImportHelpers.normalize_text(value)

        if not value or value.lower() == "nan":
            return ""

        return value
    
    @staticmethod
    def clean_300_text(value):
        value = ExternalApprovalImportService.normalize_optional_text(value)
        return value[:300]

    @staticmethod
    def clean_decimal(value):
        return ImportHelpers.clean_decimal(value)

    @staticmethod
    def clean_date(value):
        return ImportHelpers.clean_date(value)

    # ============================================================
    # Main Import
    # ============================================================

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()

        print(
            "⏳ Starting External Approvals import from Sheet 12..."
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
        # Validate DataFrame
        # ========================================================

        if dataframe is None or dataframe.empty:

            return result

        data = dataframe.copy().reset_index(drop=True)

        # ========================================================
        # Header Map
        # ========================================================

        header_map = ImportHelpers.build_header_map(data)

        print("✅ External Approvals headers mapped successfully")
        print(
            "   Headers:",
            list(header_map.keys()),
        )

        # ========================================================
        # Required Columns
        # ========================================================

        required_columns = [
            "اسم المريض",
            "رقم الــكـارنية",
            "الشــركــة",
            "Sub Account",
            "التاريخ",
            "الرقم الطبي",
            "الطبيب",
            "التخصص",
            "المطلوب",
            "الاجراء",
            "رقم التليفون",
            "Agent 1",
            "Status",
            "Main Status",
            "التكلفه المبدئية",
            "Billing Status",
            "ملاحظات الحسابات",
            "الرقم الحسابى",
            "التكلفة المستلمه",
            "New Reprt",
            "New Approval",
            "Request and Approval NO.",
            "Approval Date",
            "Expiry Date",
            "الملاحظات",
            "Last Update",
            "Agent 2",
            "OPD ,Sales or CS",
            "تاريخ الدخول",
            "ملاحظات الـ OR Coordinator",
            "sales account",
            "Head",
            "USER",
            "ملاحظات السيلز",
        ]

        ImportHelpers.validate_required_columns(
            data,
            required_columns,
        )

        # ========================================================
        # Existing External Approvals Cache
        # ========================================================

        print("⏳ Loading existing external approvals...")

        approvals_cache = {}

        for approval_obj in ExternalApproval.objects.all():

            key = build_key(
                approval_obj.patient_name,
                approval_obj.card_number,
                approval_obj.procedure,
                approval_obj.date,
                approval_obj.doctor_name,
            )

            approvals_cache[key] = approval_obj

        print(
            f"   ✅ {len(approvals_cache)} approvals loaded"
        )

        # ========================================================
        # Bulk Operation Lists
        # ========================================================

        to_create = []
        to_update = []

        sheet_records = set()

        # ========================================================
        # Processing
        # ========================================================

        print("⏳ Processing rows...")

        total_rows = len(data)

        for idx, row in data.iterrows():

            try:

                # ====================================================
                # Patient Name
                # ====================================================

                patient_name = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "patient_name",
                        )
                    )
                )

                if not patient_name:

                    result["skipped"] += 1
                    continue

                # ====================================================
                # Ignore Header / Summary Rows
                # ====================================================

                if patient_name.lower() in {
                    "اسم المريض",
                    "admission",
                    "approval",
                    "acc",
                    "status",
                    "total",
                }:

                    result["skipped"] += 1
                    continue

                # ====================================================
                # Read Row Data By Header Name
                # ====================================================

                attachment_type = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "attachment_type",
                        )
                    )
                )

                card_number = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "card_number",
                        )
                    )
                )

                if len(card_number) > 100:
                    card_number = ""

                company = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "company",
                        )
                    )
                )

                sub_account = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "sub_account",
                        )
                    )
                )

                date = (
                    ExternalApprovalImportService.clean_date(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "date",
                            default=None,
                        )
                    )
                )

                medical_number = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "medical_number",
                        )
                    )
                )

                doctor_name = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "doctor_name",
                        )
                    )
                )

                specialty = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "specialty",
                        )
                    )
                )

                required = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "required",
                        )
                    )
                )

                procedure = (
                    ExternalApprovalImportService.clean_300_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "procedure",
                        )
                    )
                )
                phone = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "phone",
                        )
                    )
                )

                agent_1 = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "agent_1",
                        )
                    )
                )

                status = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "status",
                        )
                    )
                )

                main_status = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "main_status",
                        )
                    )
                )

                initial_cost = (
                    ExternalApprovalImportService.clean_decimal(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "initial_cost",
                            default=None,
                        )
                    )
                )

                if initial_cost is None:
                    initial_cost = Decimal("0.00")

                pricing_date = (
                    ExternalApprovalImportService.clean_date(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "pricing_date",
                            default=None,
                        )
                    )
                )

                pricing_responsible = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "pricing_responsible",
                        )
                    )
                )

                billing_status = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "billing_status",
                        )
                    )
                )

                approval_review_responsible = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "approval_review_responsible",
                        )
                    )
                )

                accounts_notes = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "accounts_notes",
                        )
                    )
                )

                account_number = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "account_number",
                        )
                    )
                )

                received_cost = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "received_cost",
                        )
                    )
                )

                report = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "report",
                        )
                    )
                )

                approval_value = (
                    ExternalApprovalImportService.clean_300_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "approval",
                        )
                    )
                )

                request_approval_no = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "request_approval_no",
                        )
                    )
                )

                approval_date = (
                    ExternalApprovalImportService.clean_date(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "approval_date",
                            default=None,
                        )
                    )
                )

                expiry_date = (
                    ExternalApprovalImportService.clean_date(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "expiry_date",
                            default=None,
                        )
                    )
                )

                notes = (
                    ExternalApprovalImportService.clean_300_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "notes",
                        )
                    )
                )

                last_update = (
                    ExternalApprovalImportService.clean_date(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "last_update",
                            default=None,
                        )
                    )
                )

                agent_2 = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "agent_2",
                        )
                    )
                )

                opd_sales_cs = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "opd_sales_cs",
                        )
                    )
                )

                admission_date = (
                    ExternalApprovalImportService.clean_date(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "admission_date",
                            default=None,
                        )
                    )
                )

                or_coordinator_notes = (
                    ExternalApprovalImportService.clean_300_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "or_coordinator_notes",
                        )
                    )
                )

                sales_account = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "sales_account",
                        )
                    )
                )

                head = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "head",
                        )
                    )
                )

                user = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "user",
                        )
                    )
                )

                sales_notes = (
                    ExternalApprovalImportService.normalize_optional_text(
                        ExternalApprovalImportService.get_value(
                            row,
                            header_map,
                            "sales_notes",
                        )
                    )
                )

                result["processed"] += 1

                # ====================================================
                # Build Key
                # ====================================================

                key = build_key(
                    patient_name,
                    card_number,
                    procedure,
                    date,
                    doctor_name,
                )

                sheet_records.add(key)

                existing_approval = approvals_cache.get(key)

                # ====================================================
                # Update Existing
                # ====================================================

                if existing_approval:

                    changed = False

                    fields_to_check = [
                        ("attachment_type", attachment_type),
                        ("patient_name", patient_name),
                        ("card_number", card_number),
                        ("company", company),
                        ("sub_account", sub_account),
                        ("date", date),
                        ("medical_number", medical_number),
                        ("doctor_name", doctor_name),
                        ("specialty", specialty),
                        ("required", required),
                        ("procedure", procedure),
                        ("phone", phone),
                        ("agent_1", agent_1),
                        ("status", status),
                        ("main_status", main_status),
                        ("initial_cost", initial_cost),
                        ("pricing_date", pricing_date),
                        ("pricing_responsible", pricing_responsible),
                        ("billing_status", billing_status),
                        (
                            "approval_review_responsible",
                            approval_review_responsible,
                        ),
                        ("accounts_notes", accounts_notes),
                        ("account_number", account_number),
                        ("received_cost", received_cost),
                        ("report", report),
                        ("approval", approval_value),
                        ("request_approval_no", request_approval_no),
                        ("approval_date", approval_date),
                        ("expiry_date", expiry_date),
                        ("notes", notes),
                        ("last_update", last_update),
                        ("agent_2", agent_2),
                        ("opd_sales_cs", opd_sales_cs),
                        ("admission_date", admission_date),
                        (
                            "or_coordinator_notes",
                            or_coordinator_notes,
                        ),
                        ("sales_account", sales_account),
                        ("head", head),
                        ("user", user),
                        ("sales_notes", sales_notes),
                    ]

                    for field_name, value in fields_to_check:

                        old_value = getattr(
                            existing_approval,
                            field_name,
                        )

                        if old_value != value:

                            setattr(
                                existing_approval,
                                field_name,
                                value,
                            )

                            changed = True

                    if changed:

                        to_update.append(
                            existing_approval
                        )

                        result["updated"] += 1

                # ====================================================
                # Create New
                # ====================================================

                else:

                    approval_obj = ExternalApproval(
                        attachment_type=attachment_type,
                        patient_name=patient_name,
                        card_number=card_number,
                        company=company,
                        sub_account=sub_account,
                        date=date,
                        medical_number=medical_number,
                        doctor_name=doctor_name,
                        specialty=specialty,
                        required=required,
                        procedure=procedure,
                        phone=phone,
                        agent_1=agent_1,
                        status=status,
                        main_status=main_status,
                        initial_cost=initial_cost,
                        pricing_date=pricing_date,
                        pricing_responsible=pricing_responsible,
                        billing_status=billing_status,
                        approval_review_responsible=(
                            approval_review_responsible
                        ),
                        accounts_notes=accounts_notes,
                        account_number=account_number,
                        received_cost=received_cost,
                        report=report,
                        approval=approval_value,
                        request_approval_no=request_approval_no,
                        approval_date=approval_date,
                        expiry_date=expiry_date,
                        notes=notes,
                        last_update=last_update,
                        agent_2=agent_2,
                        opd_sales_cs=opd_sales_cs,
                        admission_date=admission_date,
                        or_coordinator_notes=(
                            or_coordinator_notes
                        ),
                        sales_account=sales_account,
                        head=head,
                        user=user,
                        sales_notes=sales_notes,
                    )

                    to_create.append(approval_obj)

                    # مهم جدًا:
                    # نضيف الـ object للـ cache فورًا حتى لو
                    # تكرر نفس المفتاح داخل نفس الـ Sheet.
                    approvals_cache[key] = approval_obj

                    result["created"] += 1

                # ====================================================
                # Progress
                # ====================================================

                if result["processed"] % 100 == 0:

                    print(
                        f"   📊 Processed "
                        f"{result['processed']}/{total_rows} rows..."
                    )

            except Exception as exc:

                result["errors"] += 1

                if result["errors"] <= 10:

                    print(
                        f"\n❌ Error in row {idx + 2}: "
                        f"{str(exc)[:120]}..."
                    )

                continue

        # ========================================================
        # Bulk Create
        # ========================================================

        if to_create:

            print(
                f"💾 Creating {len(to_create)} approvals..."
            )

            ExternalApproval.objects.bulk_create(
                to_create,
                batch_size=500,
            )

        # ========================================================
        # Bulk Update
        # ========================================================

        print(
            f"💾 Updating {len(to_update)} approvals..."
        )

        if to_update:

            update_fields = [
                "attachment_type",
                "patient_name",
                "card_number",
                "company",
                "sub_account",
                "date",
                "medical_number",
                "doctor_name",
                "specialty",
                "required",
                "procedure",
                "phone",
                "agent_1",
                "status",
                "main_status",
                "initial_cost",
                "pricing_date",
                "pricing_responsible",
                "billing_status",
                "approval_review_responsible",
                "accounts_notes",
                "account_number",
                "received_cost",
                "report",
                "approval",
                "request_approval_no",
                "approval_date",
                "expiry_date",
                "notes",
                "last_update",
                "agent_2",
                "opd_sales_cs",
                "admission_date",
                "or_coordinator_notes",
                "sales_account",
                "head",
                "user",
                "sales_notes",
            ]

            BATCH_SIZE = 500

            for i in range(
                0,
                len(to_update),
                BATCH_SIZE,
            ):

                batch = to_update[
                    i:i + BATCH_SIZE
                ]

                ExternalApproval.objects.bulk_update(
                    batch,
                    fields=update_fields,
                    batch_size=BATCH_SIZE,
                )

                print(
                    f"   ✅ Updated batch "
                    f"{i // BATCH_SIZE + 1} "
                    f"({min(i + BATCH_SIZE, len(to_update))}"
                    f"/{len(to_update)})"
                )

        # ========================================================
        # Delete Records Removed From Sheet
        # ========================================================

        to_delete = []

        for key, approval_obj in approvals_cache.items():

            # objects created during this import have no DB id
            # until bulk_create finishes.
            if (
                approval_obj.id
                and key not in sheet_records
            ):

                to_delete.append(
                    approval_obj.id
                )

        if to_delete:

            deleted, _ = (
                ExternalApproval.objects
                .filter(id__in=to_delete)
                .delete()
            )

            result["deleted"] = deleted

            print(
                f"🗑️ Deleted {deleted} approvals"
            )

        # ========================================================
        # Final Output
        # ========================================================

        elapsed = time.perf_counter() - start_time

        print("\n" + "=" * 80)
        print("✅ External Approvals import completed!")
        print(
            f"📊 Processed: {result['processed']}, "
            f"Created: {result['created']}, "
            f"Updated: {result['updated']}, "
            f"Deleted: {result['deleted']}, "
            f"Skipped: {result['skipped']}"
        )

        if result["errors"]:

            print(
                f"❌ Errors: {result['errors']}"
            )

        print("=" * 80)

        print(
            f"⏱️ Completed in {elapsed:.2f} seconds"
        )

        return result