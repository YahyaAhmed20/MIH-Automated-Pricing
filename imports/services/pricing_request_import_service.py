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
    def clean_text(value):
        if pd.isna(value):
            return ""
        return str(value).strip()
    
    @staticmethod
    def parse_decimal(value):
        if pd.isna(value):
            return None
        try:
            value = str(value).replace(",", "")
            return Decimal(value)
        except Exception:
            return None
        
    @staticmethod
    def parse_date(value):

        if pd.isna(value):
            return None

        try:

            parsed_date = pd.to_datetime(
                value,
                errors="coerce"
            )

            if pd.isna(parsed_date):
                return None

            return parsed_date.date()

        except Exception:
            return None

    @staticmethod
    def get_status(value):
        value = PricingRequestImportService.clean_text(value)
        return PricingRequestImportService.STATUS_MAPPING.get(value, "unknown")

    @staticmethod
    def get_or_create_user(name):
        name = PricingRequestImportService.clean_text(name)
        if not name:
            return None, False

        user, created = User.objects.get_or_create(
            username=name,
            defaults={"full_name": name}
        )
        return user, created

    @staticmethod
    def import_data(dataframe):
        created_patients = 0
        created_requests = 0
        updated_requests = 0
        created_users = 0
        created_notes = 0

        # استخدام itertuples بدلاً من iterrows للأداء الأفضل
        for _, row in dataframe.iterrows():
            
            patient_name = PricingRequestImportService.clean_text(
                row.get("اسم المريض")
            )
            if not patient_name:
                continue

            # ------------------------
            # Patient
            # ------------------------
            medical_number = PricingRequestImportService.clean_text(
                row.get("الرقم الطبي")
            )

            if medical_number and medical_number.lower() != "nan":

                patient, patient_created = Patient.objects.update_or_create(
                    medical_number=medical_number,
                    defaults={
                        "full_name": patient_name,
                        "card_number": PricingRequestImportService.clean_text(
                            row.get("رقم الــكـارنية")
                        ),
                        "phone": PricingRequestImportService.clean_text(
                            row.get("رقم التليفون")
                        ),
                    }
                )

            else:

                patient, patient_created = Patient.objects.update_or_create(
                    full_name=patient_name,
                    defaults={
                        "card_number": PricingRequestImportService.clean_text(
                            row.get("رقم الــكـارنية")
                        ),
                        "phone": PricingRequestImportService.clean_text(
                            row.get("رقم التليفون")
                        ),
                    }
                )

            if patient_created:
                created_patients += 1

            # ------------------------
            # Entity
            # ------------------------
            entity_name = PricingRequestImportService.clean_text(row.get("الشــركــة"))
            entity = None
            if entity_name:
                entity, _ = ContractEntity.objects.get_or_create(
                    name=entity_name, defaults={"is_active": True}
                )

            # ------------------------
            # Sub Company
            # ------------------------
            sub_company_name = PricingRequestImportService.clean_text(row.get("Sub Account"))
            sub_company = None
            if entity and sub_company_name:
                sub_company, _ = SubCompany.objects.get_or_create(
                    entity=entity,
                    name=sub_company_name,
                    defaults={"code": sub_company_name[:50]}
                )

            # ------------------------
            # Specialty
            # ------------------------
            specialty_name = PricingRequestImportService.clean_text(
                row.get("التخصص")
            )

            if not specialty_name:
                specialty_name = "غير محدد"

            specialty, _ = Specialty.objects.get_or_create(
                name=specialty_name,
                defaults={
                    "is_active": True
                }
            )

            # ------------------------
            # Users (تم تصحيح الخطأ المنطقي هنا)
            # ------------------------
            agent_1, agent_1_created = PricingRequestImportService.get_or_create_user(row.get("Agent 1"))
            if agent_1_created:
                created_users += 1

            agent_2, agent_2_created = PricingRequestImportService.get_or_create_user(row.get("Agent 2"))
            if agent_2_created:
                created_users += 1

            # ------------------------
            # Request Number (تم تصحيح الـ Syntax Error هنا)
            # ------------------------
            approval_number = PricingRequestImportService.clean_text(
                row.get("Request and Approval NO.")
            )
            if approval_number.lower() == "nan":
                approval_number = ""

            lookup = {}
            if approval_number:
                lookup["approval_number"] = approval_number
            else:
                lookup["patient"] = patient
                lookup["request_date"] = PricingRequestImportService.parse_date(row.get("التاريخ"))
                lookup["procedure_name"] = PricingRequestImportService.clean_text(row.get("الاجراء"))

            # ------------------------
            # Pricing Request
            # ------------------------
            pricing_request, created = PricingRequest.objects.update_or_create(
                **lookup,
                defaults={
                    "patient": patient,
                    "entity": entity,
                    "sub_company": sub_company,
                    "doctor_name": PricingRequestImportService.clean_text(row.get("الطبيب")),
                    "specialty": specialty,
                    "procedure_name": PricingRequestImportService.clean_text(row.get("الاجراء")),
                    "requested_cost": PricingRequestImportService.parse_decimal(row.get("التكلفه المبدئية")),
                    "received_cost": PricingRequestImportService.parse_decimal(row.get("التكلفة المستلمه")),
                    "approval_number": approval_number or None,
                    "approval_date": PricingRequestImportService.parse_date(row.get("Approval Date")),
                    "approval_expiry_date": PricingRequestImportService.parse_date(row.get("Expiry Date")),
                    "request_date": PricingRequestImportService.parse_date(row.get("التاريخ")),
                    "expected_admission_date": PricingRequestImportService.parse_date(row.get("تاريخ الدخول")),
                    "service_date": PricingRequestImportService.parse_date(row.get("تاريخ التسعير")),
                    "status": PricingRequestImportService.get_status(row.get("Status")),
                    "main_status": PricingRequestImportService.clean_text(row.get("Main Status")),
                    "billing_status": PricingRequestImportService.clean_text(row.get("Billing Status")),
                    "agent_1": agent_1,
                    "agent_2": agent_2,
                }
            )

            if created:
                created_requests += 1
            else:
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

                note_text = PricingRequestImportService.clean_text(
                    row.get(excel_column)
                )

                if not note_text:
                    continue

                note_obj, note_created = (
                    PricingRequestNote.objects.get_or_create(
                        pricing_request=pricing_request,
                        department=department,
                        note=note_text,
                    )
                )

                if note_created:
                    created_notes += 1

        return {
            "created_patients": created_patients,
            "created_requests": created_requests,
            "updated_requests": updated_requests,
            "created_users": created_users,
            "created_notes": created_notes,
        }