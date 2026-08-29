from .authorization import Authorization
from .permissions import Permissions


def authorization(request):
    authz = Authorization(request.user)

    return {
        "authz": authz,

        # Packages
        "can_packages_cash_full": authz.can(
            Permissions.PACKAGES_CASH_FULL
        ),

        "can_packages_credit_basic": authz.can(
            Permissions.PACKAGES_CREDIT_BASIC
        ),

        "can_packages_credit_full": authz.can(
            Permissions.PACKAGES_CREDIT_FULL
        ),

        # 👇 أضف هذا السطر الجديد
        "can_packages_credit_attachments": authz.can(
            Permissions.PACKAGES_CREDIT_ATTACHMENTS
        ),

        # Patients
        "can_patients_search": authz.can(
            Permissions.PATIENTS_SEARCH
        ),
        # Services
        "can_service_search": authz.can(
            Permissions.SERVICE_SEARCH
        ),

        # Approvals
        "can_approvals_view": authz.can(
            Permissions.APPROVALS_VIEW
        ),

        "can_approvals_statistics": authz.can(
            Permissions.APPROVALS_STATISTICS
        ),

        # Doctors
        "can_doctors_view_all": authz.can(
            Permissions.DOCTORS_VIEW_ALL
        ),

        "can_doctors_view_own": authz.can(
            Permissions.DOCTORS_VIEW_OWN
        ),

        # Financial
        "can_financial_full": authz.can(
            Permissions.FINANCIAL_FULL
        ),

        # System
        "is_admin": authz.is_admin,
        "can_users_manage": authz.can(
            Permissions.USERS_MANAGE
        ),
        "can_roles_manage": authz.can(
            Permissions.ROLES_MANAGE
        ),

        # Credit package pricing
        "has_credit_full": authz.can(
            Permissions.PACKAGES_CREDIT_FULL
        ),
        # Admission
        "is_admission": authz.role_name == "Admission",
        "is_accountant": authz.role_name == "Accountant",
    }