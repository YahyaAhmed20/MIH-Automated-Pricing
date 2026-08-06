from decimal import Decimal
import pandas as pd

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

    @staticmethod
    def get_status(value):
        value = ImportHelpers.normalize_text(value)
        return PricingRequestImportService.STATUS_MAPPING.get(value, "unknown")

    @staticmethod
    def import_data(dataframe):
        created_patients = 0
        created_requests = 0
        updated_requests = 0
        created_users = 0
        created_notes = 0
        deleted_requests = 0

        # ✅ Cache للـ Users
        users_cache = {
            user.username: user
            for user in User.objects.all()
        }

        # ✅ Cache للـ Entities
        entities_cache = {
            entity.name: entity
            for entity in ContractEntity.objects.all()
        }

        # ✅ Cache للـ SubCompanies
        subcompanies_cache = {
            (sub.entity_id, sub.name): sub
            for sub in SubCompany.objects.select_related("entity")
        }

        # ✅ Cache للـ Specialties
        specialties_cache = {
            specialty.name: specialty
            for specialty in Specialty.objects.all()
        }

        # ✅ Cache للـ Patients
        patients_cache = {}
        for patient in Patient.objects.all():
            key = patient.medical_number or patient.full_name
            patients_cache[key] = patient

        patients_to_update = []

        # ✅ Cache للـ Pricing Requests
        existing_requests = {}
        for request in PricingRequest.objects.select_related("patient"):
            if request.approval_number:
                key = (
                    "approval",
                    request.approval_number,
                )
            else:
                key = (
                    "patient",
                    request.patient.medical_number
                        or request.patient.full_name,
                    request.request_date,
                    request.procedure_name,
                )
            existing_requests[key] = request

        # ✅ Existing Keys + Sheet Keys
        existing_keys = set(existing_requests.keys())
        sheet_keys = set()

        requests_to_create = []
        requests_to_update = []

        # ✅ استخدم itertuples بدلاً من iterrows
        for row in dataframe.itertuples(index=False):
            
            # ✅ الحصول على البيانات من row
            patient_name = ImportHelpers.normalize_text(
                getattr(row, "اسم المريض", "")
            )
            if not patient_name:
                continue

            # ------------------------
            # Patient
            # ------------------------
            medical_number = ImportHelpers.normalize_text(
                getattr(row, "الرقم الطبي", "")
            )

            if medical_number and medical_number.lower() == "nan":
                medical_number = ""

            card_number = ImportHelpers.normalize_text(
                getattr(row, "رقم الــكـارنية", "")
            )

            phone = ImportHelpers.normalize_text(
                getattr(row, "رقم التليفون", "")
            )

            # ✅ استخدام Cache للـ Patients
            key = medical_number or patient_name
            patient = patients_cache.get(key)

            if patient is None:
                patient = Patient(
                    medical_number=medical_number or "",
                    full_name=patient_name,
                    card_number=card_number,
                    phone=phone,
                )
                patients_cache[key] = patient
                patient.save()
                created_patients += 1
            else:
                changed = False

                if patient.full_name != patient_name:
                    patient.full_name = patient_name
                    changed = True

                if patient.card_number != card_number:
                    patient.card_number = card_number
                    changed = True

                if patient.phone != phone:
                    patient.phone = phone
                    changed = True

                if changed:
                    patients_to_update.append(patient)

            # ------------------------
            # Entity
            # ------------------------
            entity_name = ImportHelpers.normalize_text(getattr(row, "الشــركــة", ""))
            entity = None

            if entity_name:
                entity = entities_cache.get(entity_name)

                if entity is None:
                    entity = ContractEntity.objects.create(
                        name=entity_name,
                        is_active=True,
                    )
                    entities_cache[entity_name] = entity

            # ------------------------
            # Sub Company
            # ------------------------
            sub_company_name = ImportHelpers.normalize_text(getattr(row, "Sub Account", ""))
            sub_company = None

            if entity and sub_company_name:
                key = (entity.id, sub_company_name)
                sub_company = subcompanies_cache.get(key)

                if sub_company is None:
                    sub_company = SubCompany.objects.create(
                        entity=entity,
                        name=sub_company_name,
                        code=sub_company_name[:50],
                    )
                    subcompanies_cache[key] = sub_company

            # ------------------------
            # Specialty
            # ------------------------
            specialty_name = ImportHelpers.normalize_text(
                getattr(row, "التخصص", "")
            )

            if not specialty_name:
                specialty_name = "غير محدد"

            specialty = specialties_cache.get(specialty_name)

            if specialty is None:
                specialty = Specialty.objects.create(
                    name=specialty_name,
                    is_active=True,
                )
                specialties_cache[specialty_name] = specialty

            # ------------------------
            # Agent 1
            # ------------------------
            agent_1_name = ImportHelpers.normalize_text(
                getattr(row, "Agent 1", "")
            )

            agent_1 = None

            if agent_1_name:
                agent_1 = users_cache.get(agent_1_name)

                if agent_1 is None:
                    agent_1 = User.objects.create(
                        username=agent_1_name,
                        full_name=agent_1_name,
                    )
                    users_cache[agent_1_name] = agent_1
                    created_users += 1

            # ------------------------
            # Agent 2
            # ------------------------
            agent_2_name = ImportHelpers.normalize_text(
                getattr(row, "Agent 2", "")
            )

            agent_2 = None

            if agent_2_name:
                agent_2 = users_cache.get(agent_2_name)

                if agent_2 is None:
                    agent_2 = User.objects.create(
                        username=agent_2_name,
                        full_name=agent_2_name,
                    )
                    users_cache[agent_2_name] = agent_2
                    created_users += 1

            # ------------------------
            # Request Number
            # ------------------------
            approval_number = ImportHelpers.normalize_text(
                getattr(row, "Request and Approval NO.", "")
            )
            if approval_number.lower() == "nan":
                approval_number = ""

            # ------------------------
            # Pricing Request - Build Key
            # ------------------------
            if approval_number:
                request_key = (
                    "approval",
                    approval_number,
                )
            else:
                request_key = (
                    "patient",
                    patient.medical_number or patient.full_name,
                    ImportHelpers.clean_date(getattr(row, "التاريخ", None)),
                    ImportHelpers.normalize_text(getattr(row, "الاجراء", "")),
                )

            # ✅ إضافة المفتاح إلى sheet_keys
            sheet_keys.add(request_key)

            existing_request = existing_requests.get(request_key)

            if existing_request is None:
                # ✅ إنشاء جديد
                pricing_request = PricingRequest(
                    patient=patient,
                    entity=entity,
                    sub_company=sub_company,
                    doctor_name=ImportHelpers.normalize_text(getattr(row, "الطبيب", "")),
                    specialty=specialty,
                    procedure_name=ImportHelpers.normalize_text(getattr(row, "الاجراء", "")),
                    requested_cost=ImportHelpers.clean_decimal(getattr(row, "التكلفه المبدئية", None)),
                    received_cost=ImportHelpers.clean_decimal(getattr(row, "التكلفة المستلمه", None)),
                    approval_number=approval_number or None,
                    approval_date=ImportHelpers.clean_date(getattr(row, "Approval Date", None)),
                    approval_expiry_date=ImportHelpers.clean_date(getattr(row, "Expiry Date", None)),
                    request_date=ImportHelpers.clean_date(getattr(row, "التاريخ", None)),
                    expected_admission_date=ImportHelpers.clean_date(getattr(row, "تاريخ الدخول", None)),
                    service_date=ImportHelpers.clean_date(getattr(row, "تاريخ التسعير", None)),
                    status=PricingRequestImportService.get_status(getattr(row, "Status", "")),
                    main_status=ImportHelpers.normalize_text(getattr(row, "Main Status", "")),
                    billing_status=ImportHelpers.normalize_text(getattr(row, "Billing Status", "")),
                    agent_1=agent_1,
                    agent_2=agent_2,
                )
                requests_to_create.append(pricing_request)
                existing_requests[request_key] = pricing_request
                created_requests += 1
            else:
                # ✅ تحديث موجود
                pricing_request = existing_request
                changed = False

                if pricing_request.patient_id != patient.id:
                    pricing_request.patient = patient
                    changed = True

                if pricing_request.entity_id != (entity.id if entity else None):
                    pricing_request.entity = entity
                    changed = True

                if pricing_request.sub_company_id != (sub_company.id if sub_company else None):
                    pricing_request.sub_company = sub_company
                    changed = True

                if pricing_request.doctor_name != ImportHelpers.normalize_text(getattr(row, "الطبيب", "")):
                    pricing_request.doctor_name = ImportHelpers.normalize_text(getattr(row, "الطبيب", ""))
                    changed = True

                if pricing_request.specialty_id != specialty.id:
                    pricing_request.specialty = specialty
                    changed = True

                if pricing_request.procedure_name != ImportHelpers.normalize_text(getattr(row, "الاجراء", "")):
                    pricing_request.procedure_name = ImportHelpers.normalize_text(getattr(row, "الاجراء", ""))
                    changed = True

                if pricing_request.requested_cost != ImportHelpers.clean_decimal(getattr(row, "التكلفه المبدئية", None)):
                    pricing_request.requested_cost = ImportHelpers.clean_decimal(getattr(row, "التكلفه المبدئية", None))
                    changed = True

                if pricing_request.received_cost != ImportHelpers.clean_decimal(getattr(row, "التكلفة المستلمه", None)):
                    pricing_request.received_cost = ImportHelpers.clean_decimal(getattr(row, "التكلفة المستلمه", None))
                    changed = True

                if pricing_request.approval_number != (approval_number or None):
                    pricing_request.approval_number = approval_number or None
                    changed = True

                if pricing_request.approval_date != ImportHelpers.clean_date(getattr(row, "Approval Date", None)):
                    pricing_request.approval_date = ImportHelpers.clean_date(getattr(row, "Approval Date", None))
                    changed = True

                if pricing_request.approval_expiry_date != ImportHelpers.clean_date(getattr(row, "Expiry Date", None)):
                    pricing_request.approval_expiry_date = ImportHelpers.clean_date(getattr(row, "Expiry Date", None))
                    changed = True

                if pricing_request.request_date != ImportHelpers.clean_date(getattr(row, "التاريخ", None)):
                    pricing_request.request_date = ImportHelpers.clean_date(getattr(row, "التاريخ", None))
                    changed = True

                if pricing_request.expected_admission_date != ImportHelpers.clean_date(getattr(row, "تاريخ الدخول", None)):
                    pricing_request.expected_admission_date = ImportHelpers.clean_date(getattr(row, "تاريخ الدخول", None))
                    changed = True

                if pricing_request.service_date != ImportHelpers.clean_date(getattr(row, "تاريخ التسعير", None)):
                    pricing_request.service_date = ImportHelpers.clean_date(getattr(row, "تاريخ التسعير", None))
                    changed = True

                new_status = PricingRequestImportService.get_status(getattr(row, "Status", ""))
                if pricing_request.status != new_status:
                    pricing_request.status = new_status
                    changed = True

                if pricing_request.main_status != ImportHelpers.normalize_text(getattr(row, "Main Status", "")):
                    pricing_request.main_status = ImportHelpers.normalize_text(getattr(row, "Main Status", ""))
                    changed = True

                if pricing_request.billing_status != ImportHelpers.normalize_text(getattr(row, "Billing Status", "")):
                    pricing_request.billing_status = ImportHelpers.normalize_text(getattr(row, "Billing Status", ""))
                    changed = True

                if pricing_request.agent_1_id != (agent_1.id if agent_1 else None):
                    pricing_request.agent_1 = agent_1
                    changed = True

                if pricing_request.agent_2_id != (agent_2.id if agent_2 else None):
                    pricing_request.agent_2 = agent_2
                    changed = True

                if changed:
                    requests_to_update.append(pricing_request)
                    updated_requests += 1

            # ------------------------
            # Notes Import
            # ------------------------
            notes_map = [
                ("الملاحظات", "approvals"),
                ("ملاحظات الحسابات", "accounts"),
                ("ملاحظات الـ OR Coordinator", "or_coordinator"),
                ("ملاحظات السيلز", "sales"),
            ]

            for excel_column, department in notes_map:
                note_text = ImportHelpers.normalize_text(
                    getattr(row, excel_column, "")
                )

                if not note_text:
                    continue

                note_obj, note_created = PricingRequestNote.objects.get_or_create(
                    pricing_request=pricing_request,
                    department=department,
                    note=note_text,
                )

                if note_created:
                    created_notes += 1

        # ✅ تنفيذ عمليات Bulk للـ Patients
        if patients_to_update:
            Patient.objects.bulk_update(
                patients_to_update,
                ["full_name", "card_number", "phone"],
                batch_size=500,
            )

        # ✅ تنفيذ عمليات Bulk للـ Pricing Requests
        if requests_to_create:
            PricingRequest.objects.bulk_create(
                requests_to_create,
                batch_size=500,
            )
            created_requests = len(requests_to_create)

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
            updated_requests = len(requests_to_update)

        # ✅ Delete Removed Requests
        keys_to_delete = existing_keys - sheet_keys

        if keys_to_delete:
            ids_to_delete = [
                existing_requests[key].id
                for key in keys_to_delete
            ]

            deleted_requests, _ = PricingRequest.objects.filter(
                id__in=ids_to_delete
            ).delete()

        return {
            "created_patients": created_patients,
            "created_requests": created_requests,
            "updated_requests": updated_requests,
            "deleted_requests": deleted_requests,
            "created_users": created_users,
            "created_notes": created_notes,
        }