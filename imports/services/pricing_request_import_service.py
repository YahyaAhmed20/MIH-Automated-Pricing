# pricing_requests/services/pricing_request_import_service.py

from pricing_requests.models import (
    Patient,
    PricingRequest,
    PricingRequestNote,
)
from accounts.models import User
from contracts.models import ContractEntity, SubCompany
from medical_catalog.models import Specialty
from imports.utils.import_helpers import ImportHelpers


class PricingRequestImportService:

    STATUS_MAPPING = {
        "Serv. Done": "service_done",
        "Patient refused": "patient_refused",
        "Approved": "approved",
        "Approved مؤجل": "approved",
        "Approved by refferal": "approved",
        "Approved with limit": "approved",
        "Pending by OPD": "pending",
        "Pending by pat.": "pending",
        "Pending by sales": "pending",
        "Pending by refferal": "pending",
        "Reject غير مغطاه": "rejected",
        "Reject امراض سابق للتعاقد": "rejected",
        "Reject تحويل على مقدم خدم اخر": "rejected",
        "Reject الحد المالى": "rejected",
        "Reject لايوجد داعى طبى": "rejected",
    }

    # ============================================================
    # Sheet 12 → Model Field Mapping
    # ============================================================

    COLUMN_MAPPING = {
        "patient_name": "اسم المريض",
        "medical_number": "الرقم الطبي",
        "card_number": "رقم الــكـارنية",
        "phone": "رقم التليفون",

        "entity_name": "الشــركــة",
        "sub_company_name": "Sub Account",

        "request_date": "التاريخ",
        "doctor_name": "الطبيب",
        "specialty_name": "التخصص",
        "procedure_name": "الاجراء",

        "agent_1": "Agent 1",
        "status": "Status",
        "main_status": "Main Status",

        "requested_cost": "التكلفه المبدئية",
        "service_date": "تاريخ التسعير",
        "pricing_responsible": "مسئول التسعير",
        "billing_status": "Billing Status",

        "approval_review_responsible": (
            "مسئول مراجعة الموافقة و التسعير"
        ),

        "accounts_notes": "ملاحظات الحسابات",
        "account_number": "الرقم الحسابى",

        "expected_admission_actual": "تاريخ الدخول الفعلى",
        "received_cost": "التكلفة المستلمه",

        "report": "Report",
        "approval": "Approval",

        # الاسم الحقيقي الموجود في Sheet 12
        "approval_number": "Request and Approval NO.",

        "approval_date": "Approval Date",
        "approval_expiry_date": "Expiry Date",

        "notes": "الملاحظات",
        "last_update": "Last Update",

        "agent_2": "Agent 2",
        "or_agent": "OR Agent",
        "opd_sales_cs": "OPD ,Sales or CS",

        "expected_admission_date": "تاريخ الدخول",

        "or_coordinator_notes": (
            "ملاحظات الـ OR Coordinator"
        ),

        "sales_account": "sales account",
        "head": "Head",
        "user": "USER",
        "sales_notes": "ملاحظات السيلز",
    }

    TEMP_MEDICAL_NUMBERS = {
        "سيلز",
        "نرمين",
        "وحيد",
        "وائل",
        "خارجى",
        "باسل",
    }

    NOTES_MAPPING = {
        "الملاحظات": "approvals",
        "ملاحظات الحسابات": "accounts",
        "ملاحظات الـ OR Coordinator": "or_coordinator",
        "ملاحظات السيلز": "sales",
    }

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def get_status(value):
        value = ImportHelpers.normalize_text(value)

        return PricingRequestImportService.STATUS_MAPPING.get(
            value,
            "unknown",
        )

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
            column_mapping=PricingRequestImportService.COLUMN_MAPPING,
            default=default,
        )

    @staticmethod
    def normalize_optional_text(value):
        value = ImportHelpers.normalize_text(value)

        if not value or value.lower() == "nan":
            return ""

        return value

    @staticmethod
    def clean_medical_number(value):
        value = PricingRequestImportService.normalize_optional_text(
            value
        )

        if value in PricingRequestImportService.TEMP_MEDICAL_NUMBERS:
            return None

        return value or None

    @staticmethod
    def clean_decimal(value):
        return ImportHelpers.clean_decimal(value)

    @staticmethod
    def clean_date(value):
        return ImportHelpers.clean_date(value)

    # ============================================================
    # Patient Matching Helpers
    # ============================================================

    INVALID_CARD_NUMBERS = {
        "",
        "غير متوفر",
        "--------",
        "-",
        "--",
        "---",
        "n/a",
        "na",
        "none",
        "null",
    }

    @staticmethod
    def normalize_card_number(value):
        """
        تنظيف رقم الكارنية لاستخدامه في المطابقة.
        القيم الوهمية مثل "غير متوفر" و "-" تعتبر فارغة.
        """

        value = PricingRequestImportService.normalize_optional_text(
            value
        )

        if not value:
            return ""

        if value.lower() in {
            "غير متوفر",
            "n/a",
            "na",
            "none",
            "null",
        }:
            return ""

        if set(value) <= {"-"}:
            return ""

        return value

    @staticmethod
    def is_valid_card_number(value):
        normalized = (
            PricingRequestImportService.normalize_card_number(
                value
            )
        )

        return (
            normalized != ""
            and normalized.lower()
            not in PricingRequestImportService.INVALID_CARD_NUMBERS
        )

    # ============================================================
    # Patient Cache Builder
    # ============================================================

    @staticmethod
    def build_patient_caches():

        patients_by_identity = {}
        patients_by_card = {}
        patients_by_medical = {}

        patients = Patient.objects.only(
            "id",
            "full_name",
            "card_number",
            "medical_number",
            "phone",
        )

        for patient in patients:

            name_key = ImportHelpers.normalize_text(
                patient.full_name
            )

            card_key = (
                PricingRequestImportService
                .normalize_card_number(
                    patient.card_number
                )
            )

            medical_key = (
                PricingRequestImportService
                .normalize_optional_text(
                    patient.medical_number
                )
            )

            if name_key:
                patients_by_identity[
                    (name_key, card_key)
                ] = patient

            if card_key:
                patients_by_card.setdefault(
                    card_key,
                    []
                ).append(patient)

            if medical_key:
                patients_by_medical[
                    medical_key
                ] = patient

        unique_patients_by_card = {
            card: patients[0]
            for card, patients in patients_by_card.items()
            if len(patients) == 1
        }

        return (
            patients_by_identity,
            patients_by_card,
            unique_patients_by_card,
            patients_by_medical,
        )

    # ============================================================
    # Patient Matching
    # ============================================================

    @staticmethod
    def find_patient(
        patient_name,
        card_number,
        medical_number,
        patients_by_identity,
        unique_patients_by_card,
        patients_by_medical,
    ):
        """
        ترتيب المطابقة:

        1. الاسم + الكارنية
        2. الكارنية إذا كان Unique
        3. الرقم الطبي

        الرقم الطبي لا يتم نقله من Patient إلى آخر.
        """

        identity_key = (
            patient_name,
            card_number,
        )

        # --------------------------------------------------------
        # 1. Exact Identity
        # --------------------------------------------------------

        patient = patients_by_identity.get(
            identity_key
        )

        if patient is not None:
            return patient

        # --------------------------------------------------------
        # 2. Unique Card
        # --------------------------------------------------------

        if card_number:

            patient = unique_patients_by_card.get(
                card_number
            )

            if patient is not None:
                return patient

        # --------------------------------------------------------
        # 3. Medical Number
        # --------------------------------------------------------

        if medical_number:

            patient = patients_by_medical.get(
                medical_number
            )

            if patient is not None:
                return patient

        return None

    # ============================================================
    # Main Import
    # ============================================================

    @staticmethod
    def import_data(dataframe):

        created_patients = 0
        created_requests = 0
        updated_requests = 0
        created_users = 0
        created_notes = 0
        deleted_requests = 0

        # ========================================================
        # Validate DataFrame
        # ========================================================

        if dataframe is None or dataframe.empty:
            return {
                "created_patients": 0,
                "created_requests": 0,
                "updated_requests": 0,
                "deleted_requests": 0,
                "created_users": 0,
                "created_notes": 0,
            }

        # ========================================================
        # Header Map
        # ========================================================

        header_map = ImportHelpers.build_header_map(
            dataframe
        )

        print("✅ Pricing Requests headers mapped successfully")
        print(
            "   Headers:",
            list(header_map.keys()),
        )

        # ========================================================
        # Validate Required Columns
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
            "الاجراء",
            "Agent 1",
            "Status",
            "Main Status",
            "التكلفه المبدئية",
            "Billing Status",
            "الرقم الحسابى",
            "التكلفة المستلمه",
            "Approval",
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
            dataframe,
            required_columns,
        )

        # ========================================================
        # Users Cache
        # ========================================================

        users_cache = {
            ImportHelpers.normalize_text(user.username): user
            for user in User.objects.all()
        }

        # ========================================================
        # Entities Cache
        # ========================================================

        entities_cache = {
            ImportHelpers.normalize_text(entity.name): entity
            for entity in ContractEntity.objects.all()
        }

        # ========================================================
        # SubCompanies Cache
        # ========================================================

        subcompanies_cache = {
            (
                sub.entity_id,
                ImportHelpers.normalize_text(sub.name),
            ): sub
            for sub in SubCompany.objects.select_related("entity")
        }

        # ========================================================
        # Specialties Cache
        # ========================================================

        specialties_cache = {
            ImportHelpers.normalize_text(specialty.name): specialty
            for specialty in Specialty.objects.all()
        }

        # ========================================================
        # Patients Cache
        # ========================================================

        (
            patients_by_identity,
            patients_by_card,
            unique_patients_by_card,
            patients_by_medical,
        ) = PricingRequestImportService.build_patient_caches()

        patients_to_update = []
        patients_to_create = []

        # ========================================================
        # Existing Pricing Requests Cache
        # ========================================================

        existing_requests = {}

        for request in PricingRequest.objects.select_related(
            "patient"
        ):

            if request.approval_number:

                key = (
                    "approval",
                    ImportHelpers.normalize_text(
                        request.approval_number
                    ),
                )

            else:

                patient_name_key = (
                    ImportHelpers.normalize_text(
                        request.patient.full_name
                    )
                )

                patient_card_key = (
                    ImportHelpers.normalize_text(
                        request.patient.card_number
                    )
                )

                key = (
                    "patient",
                    patient_name_key,
                    patient_card_key,
                    request.request_date,
                    ImportHelpers.normalize_text(
                        request.procedure_name
                    ),
                )

            existing_requests[key] = request

        existing_keys = set(
            existing_requests.keys()
        )

        sheet_keys = set()

        requests_to_create = []
        requests_to_update = []

        notes_to_create = []

        # ========================================================
        # Processing
        # ========================================================

        print("⏳ Processing Pricing Requests...")

        for index, row in dataframe.iterrows():

            # ====================================================
            # Patient Data
            # ====================================================

            patient_name = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "patient_name",
                )
            )

            patient_name = (
                PricingRequestImportService.normalize_optional_text(
                    patient_name
                )
            )

            if not patient_name:
                continue

            medical_number = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "medical_number",
                )
            )

            medical_number = (
                PricingRequestImportService.clean_medical_number(
                    medical_number
                )
            )

            card_number = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "card_number",
                )
            )

            card_number = (
                PricingRequestImportService.normalize_card_number(
                    card_number
                )
            )

            phone = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "phone",
                )
            )

            phone = (
                PricingRequestImportService.normalize_optional_text(
                    phone
                )
            )

            # ====================================================
            # Patient Matching
            # ====================================================

            patient = PricingRequestImportService.find_patient(
                patient_name,
                card_number,
                medical_number,
                patients_by_identity,
                unique_patients_by_card,
                patients_by_medical,
            )

            # ----------------------------------------------------
            # Create / Update Patient
            # ----------------------------------------------------

            if patient is None:

                # ====================================================
                # Medical Number Conflict
                # ====================================================

                if medical_number:

                    existing_medical_patient = patients_by_medical.get(
                        medical_number
                    )

                    if existing_medical_patient is not None:

                        # الرقم الطبي موجود بالفعل لنفس المريض
                        if (
                            patient is not None
                            and existing_medical_patient.id == patient.id
                        ):
                            pass

                        # الرقم الطبي مستخدم بواسطة مريض آخر
                        else:
                            medical_number = None

                # ------------------------------------------------
                # Create Patient
                # ------------------------------------------------

                patient = Patient(
                    medical_number=medical_number,
                    full_name=patient_name,
                    card_number=card_number,
                    phone=phone,
                )

                patients_to_create.append(patient)

                # ------------------------------------------------
                # Update Identity Cache
                # ------------------------------------------------

                patient_identity = (
                    patient_name,
                    card_number,
                )

                patients_by_identity[
                    patient_identity
                ] = patient

                # ------------------------------------------------
                # Update Card Cache
                #
                # لا نعتبر الـ Card Unique إذا أصبح له أكثر
                # من Patient.
                # ------------------------------------------------

                if card_number:

                    existing_card_patient = (
                        unique_patients_by_card.get(
                            card_number
                        )
                    )

                    if existing_card_patient is None:

                        unique_patients_by_card[
                            card_number
                        ] = patient

                    elif (
                        existing_card_patient.id
                        != patient.id
                    ):

                        # أصبح الـ Card مكررًا
                        unique_patients_by_card.pop(
                            card_number,
                            None
                        )

                # ------------------------------------------------
                # Update Medical Cache
                # ------------------------------------------------

                if medical_number:

                    patients_by_medical[
                        medical_number
                    ] = patient

            else:

                # ------------------------------------------------
                # Existing Patient → Update
                # ------------------------------------------------

                changed = False

                # ------------------------------------------------
                # الاسم
                #
                # نثق بالاسم القادم من الشيت إذا وجدنا Patient
                # بنفس الـ Card / Medical Number.
                # ------------------------------------------------

                if patient.full_name != patient_name:

                    patient.full_name = patient_name
                    changed = True

                # ------------------------------------------------
                # Card Number
                #
                # لا نستبدل Card صالح بـ Card فارغ.
                # ------------------------------------------------

                if card_number:

                    if patient.card_number != card_number:

                        patient.card_number = card_number
                        changed = True

                # ------------------------------------------------
                # Phone
                # ------------------------------------------------

                if phone:

                    if patient.phone != phone:

                        patient.phone = phone
                        changed = True

                # ------------------------------------------------
                # Medical Number
                #
                # لا نأخذ رقمًا مستخدمًا لمريض آخر.
                # ------------------------------------------------

                # ====================================================
                # Medical Number Conflict
                # ====================================================

                if medical_number:

                    existing_medical_patient = patients_by_medical.get(
                        medical_number
                    )

                    if existing_medical_patient is not None:

                        # الرقم الطبي موجود بالفعل لنفس المريض
                        if (
                            patient is not None
                            and existing_medical_patient.id == patient.id
                        ):
                            pass

                        # الرقم الطبي مستخدم بواسطة مريض آخر
                        else:
                            medical_number = None

                # ------------------------------------------------
                # Add to Bulk Update
                # ------------------------------------------------

                if changed:

                    patients_to_update.append(
                        patient
                    )

                # ------------------------------------------------
                # Refresh Identity Cache
                # ------------------------------------------------

                updated_name_key = (
                    ImportHelpers.normalize_text(
                        patient.full_name
                    )
                )

                updated_card_key = (
                    PricingRequestImportService
                    .normalize_card_number(
                        patient.card_number
                    )
                )

                patients_by_identity[
                    (
                        updated_name_key,
                        updated_card_key,
                    )
                ] = patient

                # --------------------------------------------------------
                # Refresh Unique Card Cache
                # --------------------------------------------------------

                if updated_card_key:

                    # لا نعمل Query جديد على قاعدة البيانات.
                    # نعتمد على الـ cache الموجود في الذاكرة.

                    card_patients = patients_by_card.get(
                        updated_card_key,
                        []
                    )

                    # نضيف الـ Patient الحالي للـ cache إذا لم يكن موجودًا.
                    if not any(
                        existing_patient.id == patient.id
                        for existing_patient in card_patients
                    ):
                        card_patients.append(patient)

                    patients_by_card[
                        updated_card_key
                    ] = card_patients

                    # الـ Card يكون Unique فقط إذا كان مرتبطًا بمريض واحد.
                    if len(card_patients) == 1:

                        unique_patients_by_card[
                            updated_card_key
                        ] = card_patients[0]

                    else:

                        unique_patients_by_card.pop(
                            updated_card_key,
                            None
                        )

            # ====================================================
            # Entity
            # ====================================================

            entity_name = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "entity_name",
                )
            )

            entity_name = (
                PricingRequestImportService.normalize_optional_text(
                    entity_name
                )
            )

            entity = None

            if entity_name:

                entity = entities_cache.get(
                    entity_name
                )

                if entity is None:

                    entity = ContractEntity.objects.create(
                        name=entity_name,
                        is_active=True,
                    )

                    entities_cache[
                        entity_name
                    ] = entity

            # ====================================================
            # Sub Company
            # ====================================================

            sub_company_name = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "sub_company_name",
                )
            )

            sub_company_name = (
                PricingRequestImportService.normalize_optional_text(
                    sub_company_name
                )
            )

            sub_company = None

            if entity and sub_company_name:

                sub_company_key = (
                    entity.id,
                    sub_company_name,
                )

                sub_company = (
                    subcompanies_cache.get(
                        sub_company_key
                    )
                )

                if sub_company is None:

                    sub_company = SubCompany.objects.create(
                        entity=entity,
                        name=sub_company_name,
                        code=sub_company_name[:50],
                    )

                    subcompanies_cache[
                        sub_company_key
                    ] = sub_company

            # ====================================================
            # Specialty
            # ====================================================

            specialty_name = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "specialty_name",
                )
            )

            specialty_name = (
                PricingRequestImportService.normalize_optional_text(
                    specialty_name
                )
            )

            if not specialty_name:
                specialty_name = "غير محدد"

            specialty = specialties_cache.get(
                specialty_name
            )

            if specialty is None:

                specialty = Specialty.objects.create(
                    name=specialty_name,
                    is_active=True,
                )

                specialties_cache[
                    specialty_name
                ] = specialty

            # ====================================================
            # Agent 1
            # ====================================================

            agent_1_name = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "agent_1",
                )
            )

            agent_1_name = (
                PricingRequestImportService.normalize_optional_text(
                    agent_1_name
                )
            )

            agent_1 = None

            if agent_1_name:

                agent_1 = users_cache.get(
                    agent_1_name
                )

                if agent_1 is None:

                    agent_1 = User.objects.create(
                        username=agent_1_name,
                        full_name=agent_1_name,
                    )

                    users_cache[
                        agent_1_name
                    ] = agent_1

                    created_users += 1

            # ====================================================
            # Agent 2
            # ====================================================

            agent_2_name = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "agent_2",
                )
            )

            agent_2_name = (
                PricingRequestImportService.normalize_optional_text(
                    agent_2_name
                )
            )

            agent_2 = None

            if agent_2_name:

                agent_2 = users_cache.get(
                    agent_2_name
                )

                if agent_2 is None:

                    agent_2 = User.objects.create(
                        username=agent_2_name,
                        full_name=agent_2_name,
                    )

                    users_cache[
                        agent_2_name
                    ] = agent_2

                    created_users += 1

            # ====================================================
            # Pricing Request Data
            # ====================================================

            approval_number = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "approval_number",
                )
            )

            approval_number = (
                PricingRequestImportService.normalize_optional_text(
                    approval_number
                )
            )

            request_date = (
                PricingRequestImportService.clean_date(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "request_date",
                        default=None,
                    )
                )
            )

            procedure_name = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "procedure_name",
                )
            )

            procedure_name = (
                PricingRequestImportService.normalize_optional_text(
                    procedure_name
                )
            )

            doctor_name = (
                PricingRequestImportService.get_value(
                    row,
                    header_map,
                    "doctor_name",
                )
            )

            doctor_name = (
                PricingRequestImportService.normalize_optional_text(
                    doctor_name
                )
            )

            requested_cost = (
                PricingRequestImportService.clean_decimal(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "requested_cost",
                        default=None,
                    )
                )
            )

            received_cost = (
                PricingRequestImportService.clean_decimal(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "received_cost",
                        default=None,
                    )
                )
            )

            approval_date = (
                PricingRequestImportService.clean_date(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "approval_date",
                        default=None,
                    )
                )
            )

            approval_expiry_date = (
                PricingRequestImportService.clean_date(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "approval_expiry_date",
                        default=None,
                    )
                )
            )

            expected_admission_date = (
                PricingRequestImportService.clean_date(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "expected_admission_date",
                        default=None,
                    )
                )
            )

            service_date = (
                PricingRequestImportService.clean_date(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "service_date",
                        default=None,
                    )
                )
            )

            status = (
                PricingRequestImportService.get_status(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "status",
                    )
                )
            )

            main_status = (
                PricingRequestImportService.normalize_optional_text(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "main_status",
                    )
                )
            )

            billing_status = (
                PricingRequestImportService.normalize_optional_text(
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        "billing_status",
                    )
                )
            )

            # ====================================================
            # Pricing Request Key
            # ====================================================

            if approval_number:

                request_key = (
                    "approval",
                    approval_number,
                )

            else:

                request_key = (
                    "patient",
                    ImportHelpers.normalize_text(
                        patient.full_name
                    ),
                    ImportHelpers.normalize_text(
                        patient.card_number
                    ),
                    request_date,
                    procedure_name,
                )

            sheet_keys.add(request_key)

            existing_request = existing_requests.get(
                request_key
            )

            # ====================================================
            # Create Request
            # ====================================================

            if existing_request is None:

                pricing_request = PricingRequest(
                    patient=patient,
                    entity=entity,
                    sub_company=sub_company,
                    doctor_name=doctor_name,
                    specialty=specialty,
                    procedure_name=procedure_name,
                    requested_cost=requested_cost,
                    received_cost=received_cost,
                    approval_number=approval_number or None,
                    approval_date=approval_date,
                    approval_expiry_date=approval_expiry_date,
                    request_date=request_date,
                    expected_admission_date=expected_admission_date,
                    service_date=service_date,
                    status=status,
                    main_status=main_status,
                    billing_status=billing_status,
                    agent_1=agent_1,
                    agent_2=agent_2,
                )

                requests_to_create.append(
                    pricing_request
                )

                existing_requests[
                    request_key
                ] = pricing_request

                created_requests += 1

            # ====================================================
            # Update Request
            # ====================================================

            else:

                pricing_request = existing_request
                changed = False

                if pricing_request.patient_id != patient.id:

                    pricing_request.patient = patient
                    changed = True

                if pricing_request.entity_id != (
                    entity.id if entity else None
                ):

                    pricing_request.entity = entity
                    changed = True

                if pricing_request.sub_company_id != (
                    sub_company.id
                    if sub_company
                    else None
                ):

                    pricing_request.sub_company = sub_company
                    changed = True

                if pricing_request.doctor_name != doctor_name:

                    pricing_request.doctor_name = doctor_name
                    changed = True

                if pricing_request.specialty_id != specialty.id:

                    pricing_request.specialty = specialty
                    changed = True

                if pricing_request.procedure_name != procedure_name:

                    pricing_request.procedure_name = procedure_name
                    changed = True

                if pricing_request.requested_cost != requested_cost:

                    pricing_request.requested_cost = requested_cost
                    changed = True

                if pricing_request.received_cost != received_cost:

                    pricing_request.received_cost = received_cost
                    changed = True

                if pricing_request.approval_number != (
                    approval_number or None
                ):

                    pricing_request.approval_number = (
                        approval_number or None
                    )
                    changed = True

                if pricing_request.approval_date != approval_date:

                    pricing_request.approval_date = approval_date
                    changed = True

                if (
                    pricing_request.approval_expiry_date
                    != approval_expiry_date
                ):

                    pricing_request.approval_expiry_date = (
                        approval_expiry_date
                    )
                    changed = True

                if pricing_request.request_date != request_date:

                    pricing_request.request_date = request_date
                    changed = True

                if (
                    pricing_request.expected_admission_date
                    != expected_admission_date
                ):

                    pricing_request.expected_admission_date = (
                        expected_admission_date
                    )
                    changed = True

                if pricing_request.service_date != service_date:

                    pricing_request.service_date = service_date
                    changed = True

                if pricing_request.status != status:

                    pricing_request.status = status
                    changed = True

                if pricing_request.main_status != main_status:

                    pricing_request.main_status = main_status
                    changed = True

                if pricing_request.billing_status != billing_status:

                    pricing_request.billing_status = billing_status
                    changed = True

                if pricing_request.agent_1_id != (
                    agent_1.id
                    if agent_1
                    else None
                ):

                    pricing_request.agent_1 = agent_1
                    changed = True

                if pricing_request.agent_2_id != (
                    agent_2.id
                    if agent_2
                    else None
                ):

                    pricing_request.agent_2 = agent_2
                    changed = True

                if changed:

                    requests_to_update.append(
                        pricing_request
                    )

                    updated_requests += 1

            # ====================================================
            # Notes
            # ====================================================

            for field_name, department in {
                "notes": "approvals",
                "accounts_notes": "accounts",
                "or_coordinator_notes": "or_coordinator",
                "sales_notes": "sales",
            }.items():

                note_text = (
                    PricingRequestImportService.get_value(
                        row,
                        header_map,
                        field_name,
                        default="",
                    )
                )

                note_text = (
                    PricingRequestImportService.normalize_optional_text(
                        note_text
                    )
                )

                if not note_text:
                    continue

                notes_to_create.append(
                    (
                        pricing_request,
                        department,
                        note_text,
                    )
                )

        # ========================================================
        # Bulk Create Patients
        # ========================================================

        if patients_to_create:
            Patient.objects.bulk_create(
                patients_to_create,
                batch_size=500,
            )
            created_patients = len(patients_to_create)

        # ========================================================
        # Bulk Update Patients
        # ========================================================

        if patients_to_update:

            Patient.objects.bulk_update(
                patients_to_update,
                [
                    "full_name",
                    "card_number",
                    "phone",
                    "medical_number",
                ],
                batch_size=500,
            )

        # ========================================================
        # Bulk Create Requests
        # ========================================================

        if requests_to_create:

            PricingRequest.objects.bulk_create(
                requests_to_create,
                batch_size=500,
            )

            created_requests = len(
                requests_to_create
            )

        # ========================================================
        # Bulk Create Notes
        # ========================================================

        if notes_to_create:

            existing_notes = set(
                PricingRequestNote.objects.filter(
                    pricing_request_id__in=[
                        pricing_request.id
                        for pricing_request, _, _ in notes_to_create
                        if pricing_request.id
                    ]
                ).values_list(
                    "pricing_request_id",
                    "department",
                    "note",
                )
            )

            notes_to_bulk_create = []

            for (
                pricing_request,
                department,
                note_text,
            ) in notes_to_create:

                if not pricing_request.id:
                    continue

                note_key = (
                    pricing_request.id,
                    department,
                    note_text,
                )

                if note_key in existing_notes:
                    continue

                existing_notes.add(note_key)

                notes_to_bulk_create.append(
                    PricingRequestNote(
                        pricing_request=pricing_request,
                        department=department,
                        note=note_text,
                    )
                )

            if notes_to_bulk_create:

                PricingRequestNote.objects.bulk_create(
                    notes_to_bulk_create,
                    batch_size=500,
                )

                created_notes = len(
                    notes_to_bulk_create
                )

        # ========================================================
        # Bulk Update Requests
        # ========================================================

        if requests_to_update:

            update_fields = [
                "patient",
                "entity",
                "sub_company",
                "doctor_name",
                "specialty",
                "procedure_name",
                "requested_cost",
                "received_cost",
                "approval_number",
                "approval_date",
                "approval_expiry_date",
                "request_date",
                "expected_admission_date",
                "service_date",
                "status",
                "main_status",
                "billing_status",
                "agent_1",
                "agent_2",
            ]

            PricingRequest.objects.bulk_update(
                requests_to_update,
                update_fields,
                batch_size=500,
            )

            updated_requests = len(
                requests_to_update
            )

        # ========================================================
        # Delete Requests Removed From Sheet
        # ========================================================

        keys_to_delete = (
            existing_keys - sheet_keys
        )

        if keys_to_delete:

            ids_to_delete = [
                existing_requests[key].id
                for key in keys_to_delete
                if existing_requests[key].id
            ]

            if ids_to_delete:

                deleted_requests, _ = (
                    PricingRequest.objects
                    .filter(id__in=ids_to_delete)
                    .delete()
                )

        # ========================================================
        # Result
        # ========================================================

        return {
            "created_patients": created_patients,
            "created_requests": created_requests,
            "updated_requests": updated_requests,
            "deleted_requests": deleted_requests,
            "created_users": created_users,
            "created_notes": created_notes,
        }