from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission

from accounts.models import Role


class Command(BaseCommand):
    help = "Create/update system roles and assign their permissions."

    ROLE_PERMISSIONS = {
        # ==========================================
        # Agent
        # ==========================================
        "Agent": [
            "packages_cash_full",
            "packages_credit_basic",
            "patients_search",
            "approvals_view",
        ],

        # ==========================================
        # Supervisor
        # ==========================================
        "Supervisor": [
            "packages_cash_full",
            "packages_credit_basic",
            "patients_search",
            "approvals_view",
            "approvals_statistics",
        ],

        # ==========================================
        # Manager
        # ==========================================
        "Manager": [
            "packages_cash_full",
            "packages_credit_basic",
            "patients_search",
            "approvals_view",
            "approvals_statistics",
            "doctors_view_all",
        ],

        # ==========================================
        # Doctor
        # ==========================================
        "Doctor": [
            "doctors_view_own",
        ],

        # ==========================================
        # Admission
        # ==========================================
        "Admission": [
            "approvals_view",
        ],

        # ==========================================
        # Accountant
        # ==========================================
        "Accountant": [
        # Packages
        "packages_cash_full",
        "packages_credit_full",

        # Financial / Contracts
        "financial_full",
        
         # Reports
        "reports_view",
    ],

        # ==========================================
        # Admin
        # ==========================================
        "Admin": [
            "system_manage",
            "users_manage",
            "roles_manage",

            "packages_cash_full",
            "packages_credit_basic",
            "packages_credit_full",

            "patients_search",
            "patients_view",

            "approvals_view",
            "approvals_statistics",
            "approvals_edit",

            "doctors_view_all",
            "doctors_view_own",
            "doctors_edit",

            "financial_full",
        ],
    }

    def handle(self, *args, **options):

        self.stdout.write(
            self.style.NOTICE(
                "Setting up hospital system roles..."
            )
        )

        for role_name, permission_codenames in self.ROLE_PERMISSIONS.items():

            role, created = Role.objects.get_or_create(
                name=role_name
            )

            permissions = Permission.objects.filter(
                content_type__app_label="accounts",
                codename__in=permission_codenames,
            )

            found_codenames = set(
                permissions.values_list(
                    "codename",
                    flat=True
                )
            )

            missing = set(permission_codenames) - found_codenames

            if missing:
                self.stdout.write(
                    self.style.WARNING(
                        f"[{role_name}] Missing permissions: "
                        f"{', '.join(sorted(missing))}"
                    )
                )

            # مهم:
            # set() يجعل الـRole تعكس الـConfiguration الحالية
            # بدل تراكم صلاحيات قديمة.
            role.permissions.set(permissions)

            action = "Created" if created else "Updated"

            self.stdout.write(
                self.style.SUCCESS(
                    f"{action}: {role_name} "
                    f"({permissions.count()} permissions)"
                )
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "Role setup completed successfully."
            )
        )