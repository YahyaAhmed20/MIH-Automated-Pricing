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
        # نعتمد على اسم المريض + رقم الكارنية كهوية أساسية
        # لأن الرقم الطبي قد يكون مؤقتًا مثل: سيلز / نرمين / وحيد
        patients_by_identity = {}
        patients_by_medical = {}

        for patient in Patient.objects.all():

            patient_name_key = ImportHelpers.normalize_text(
                patient.full_name
            )

            patient_card_key = ImportHelpers.normalize_text(
                patient.card_number
            )

            if patient_name_key:
                identity_key = (
                    patient_name_key,
                    patient_card_key,
                )

                patients_by_identity[identity_key] = patient

                # لو الكارنية فاضي، نخزن بالاسم فقط كـ fallback
                if not patient_card_key:
                    patients_by_identity[
                        (patient_name_key, "")
                    ] = patient

            medical_key = ImportHelpers.normalize_text(
                patient.medical_number
            )

            if medical_key:
                patients_by_medical[medical_key] = patient

        patients_to_update = []

        # ✅ Cache للـ Pricing Requests
        # لو فيه Approval Number نستخدمه كمفتاح ثابت.
        # لو مفيش Approval Number:
        # نستخدم هوية المريض + التاريخ + الإجراء.
        # لا نعتمد على medical_number لأنه قد يتغير لاحقًا.

        existing_requests = {}

        for request in PricingRequest.objects.select_related("patient"):

            if request.approval_number:
                key = (
                    "approval",
                    ImportHelpers.normalize_text(
                        request.approval_number
                    ),
                )
            else:
                patient_name_key = ImportHelpers.normalize_text(
                    request.patient.full_name
                )

                patient_card_key = ImportHelpers.normalize_text(
                    request.patient.card_number
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

        # ✅ Existing Keys + Sheet Keys
        existing_keys = set(existing_requests.keys())
        sheet_keys = set()

        requests_to_create = []
        requests_to_update = []

        # ✅ تخزين الـ Notes مؤقتًا لحين حفظ Pricing Requests
        notes_to_create = []

        # ✅ استخدام iterrows لأن أسماء الأعمدة في Sheet 12 عربية
        for _, row in dataframe.iterrows():
            
            # ✅ الحصول على البيانات من row
            patient_name = ImportHelpers.normalize_text(
                row.get("اسم المريض", "")
            )
            if not patient_name:
                continue

            # ------------------------
            # Patient
            # ------------------------
            medical_number = ImportHelpers.normalize_text(
                row.get("الرقم الطبي", "")
            )

            if not medical_number or medical_number.lower() == "nan":
                medical_number = None

            # القيم المؤقتة التي يستخدمها الشيت بدل الرقم الطبي الحقيقي
            TEMP_MEDICAL_NUMBERS = {
                "سيلز",
                "نرمين",
                "وحيد",
            }

            if medical_number in TEMP_MEDICAL_NUMBERS:
                medical_number = None

            card_number = ImportHelpers.normalize_text(
                row.get("رقم الــكـارنية", "")
            )

            phone = ImportHelpers.normalize_text(
                row.get("رقم التليفون", "")
            )

            # ✅ Patient Identity
            # اسم المريض + رقم الكارنية هو المفتاح الأساسي
            patient_identity = (
                patient_name,
                card_number,
            )

            patient = patients_by_identity.get(
                patient_identity
            )

            # لو الكارنية غير موجود، جرب الاسم فقط
            if patient is None and not card_number:
                patient = patients_by_identity.get(
                    (patient_name, "")
                )

            # ⚠️ لا نستخدم الرقم الطبي لتحديد هوية المريض.
            # الرقم الطبي قد يكون قيمة مؤقتة مثل:
            # سيلز / نرمين / وحيد
            #
            # هوية المريض تعتمد على:
            # اسم المريض + رقم الكارنية
            #
            # والرقم الطبي يتم تحديثه فقط بعد العثور على المريض.

            if patient is None:

                # ------------------------
                # Patient جديد
                # ------------------------
                patient = Patient(
                    medical_number=medical_number,
                    full_name=patient_name,
                    card_number=card_number,
                    phone=phone,
                )

                patient.save()

                created_patients += 1

                # تحديث الـ caches
                patients_by_identity[patient_identity] = patient

                if medical_number:
                    patients_by_medical[medical_number] = patient

            else:

                # ------------------------
                # Patient موجود → Update
                # ------------------------
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

                # ⭐ أهم جزء:
                # الرقم الطبي ممكن يتغير من قيمة مؤقتة
                # إلى الرقم الطبي الحقيقي
                if patient.medical_number != medical_number:

                    # لا نغيره إلى قيمة فارغة
                    # إلا لو الشيت فعلاً فارغ
                    if medical_number:
                        patient.medical_number = medical_number
                        changed = True

                if changed:
                    patients_to_update.append(patient)

                # تحديث الـ caches
                patients_by_identity[patient_identity] = patient

                if medical_number:
                    patients_by_medical[medical_number] = patient

            # ------------------------
            # Entity
            # ------------------------
            entity_name = ImportHelpers.normalize_text(row.get("الشــركــة", ""))
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
            sub_company_name = ImportHelpers.normalize_text(row.get("Sub Account", ""))
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
                row.get("التخصص", "")
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
                row.get("Agent 1", "")
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
                row.get("Agent 2", "")
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
                row.get("Request and Approval NO.", "")
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
                    ImportHelpers.normalize_text(
                        patient.full_name
                    ),
                    ImportHelpers.normalize_text(
                        patient.card_number
                    ),
                    ImportHelpers.clean_date(
                        row.get("التاريخ", None)
                    ),
                    ImportHelpers.normalize_text(
                        row.get("الاجراء", "")
                    ),
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
                    doctor_name=ImportHelpers.normalize_text(row.get("الطبيب", "")),
                    specialty=specialty,
                    procedure_name=ImportHelpers.normalize_text(row.get("الاجراء", "")),
                    requested_cost=ImportHelpers.clean_decimal(row.get("التكلفه المبدئية", None)),
                    received_cost=ImportHelpers.clean_decimal(row.get("التكلفة المستلمه", None)),
                    approval_number=approval_number or None,
                    approval_date=ImportHelpers.clean_date(row.get("Approval Date", None)),
                    approval_expiry_date=ImportHelpers.clean_date(row.get("Expiry Date", None)),
                    request_date=ImportHelpers.clean_date(row.get("التاريخ", None)),
                    expected_admission_date=ImportHelpers.clean_date(row.get("تاريخ الدخول", None)),
                    service_date=ImportHelpers.clean_date(row.get("تاريخ التسعير", None)),
                    status=PricingRequestImportService.get_status(row.get("Status", "")),
                    main_status=ImportHelpers.normalize_text(row.get("Main Status", "")),
                    billing_status=ImportHelpers.normalize_text(row.get("Billing Status", "")),
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

                if pricing_request.doctor_name != ImportHelpers.normalize_text(row.get("الطبيب", "")):
                    pricing_request.doctor_name = ImportHelpers.normalize_text(row.get("الطبيب", ""))
                    changed = True

                if pricing_request.specialty_id != specialty.id:
                    pricing_request.specialty = specialty
                    changed = True

                if pricing_request.procedure_name != ImportHelpers.normalize_text(row.get("الاجراء", "")):
                    pricing_request.procedure_name = ImportHelpers.normalize_text(row.get("الاجراء", ""))
                    changed = True

                if pricing_request.requested_cost != ImportHelpers.clean_decimal(row.get("التكلفه المبدئية", None)):
                    pricing_request.requested_cost = ImportHelpers.clean_decimal(row.get("التكلفه المبدئية", None))
                    changed = True

                if pricing_request.received_cost != ImportHelpers.clean_decimal(row.get("التكلفة المستلمه", None)):
                    pricing_request.received_cost = ImportHelpers.clean_decimal(row.get("التكلفة المستلمه", None))
                    changed = True

                if pricing_request.approval_number != (approval_number or None):
                    pricing_request.approval_number = approval_number or None
                    changed = True

                if pricing_request.approval_date != ImportHelpers.clean_date(row.get("Approval Date", None)):
                    pricing_request.approval_date = ImportHelpers.clean_date(row.get("Approval Date", None))
                    changed = True

                if pricing_request.approval_expiry_date != ImportHelpers.clean_date(row.get("Expiry Date", None)):
                    pricing_request.approval_expiry_date = ImportHelpers.clean_date(row.get("Expiry Date", None))
                    changed = True

                if pricing_request.request_date != ImportHelpers.clean_date(row.get("التاريخ", None)):
                    pricing_request.request_date = ImportHelpers.clean_date(row.get("التاريخ", None))
                    changed = True

                if pricing_request.expected_admission_date != ImportHelpers.clean_date(row.get("تاريخ الدخول", None)):
                    pricing_request.expected_admission_date = ImportHelpers.clean_date(row.get("تاريخ الدخول", None))
                    changed = True

                if pricing_request.service_date != ImportHelpers.clean_date(row.get("تاريخ التسعير", None)):
                    pricing_request.service_date = ImportHelpers.clean_date(row.get("تاريخ التسعير", None))
                    changed = True

                new_status = PricingRequestImportService.get_status(row.get("Status", ""))
                if pricing_request.status != new_status:
                    pricing_request.status = new_status
                    changed = True

                if pricing_request.main_status != ImportHelpers.normalize_text(row.get("Main Status", "")):
                    pricing_request.main_status = ImportHelpers.normalize_text(row.get("Main Status", ""))
                    changed = True

                if pricing_request.billing_status != ImportHelpers.normalize_text(row.get("Billing Status", "")):
                    pricing_request.billing_status = ImportHelpers.normalize_text(row.get("Billing Status", ""))
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
                    row.get(excel_column, "")
                )

                if not note_text:
                    continue

                # ✅ نؤجل إنشاء الـ Note حتى يتم حفظ PricingRequest
                notes_to_create.append(
                    (
                        pricing_request,
                        department,
                        note_text,
                    )
                )

        # ✅ تنفيذ عمليات Bulk للـ Patients
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

        # ✅ تنفيذ عمليات Bulk للـ Pricing Requests
        if requests_to_create:
            PricingRequest.objects.bulk_create(
                requests_to_create,
                batch_size=500,
            )
            created_requests = len(requests_to_create)

        # ✅ إنشاء الـ Notes بعد حفظ Pricing Requests
        for pricing_request, department, note_text in notes_to_create:

            note_obj, note_created = PricingRequestNote.objects.get_or_create(
                pricing_request=pricing_request,
                department=department,
                note=note_text,
            )

            if note_created:
                created_notes += 1

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