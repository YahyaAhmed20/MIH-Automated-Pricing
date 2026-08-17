from .permissions import Permissions


class Authorization:
    """
    Central authorization service.

    مسؤول عن معرفة:
    - هل المستخدم لديه صلاحية معينة؟
    - هل المستخدم Admin؟
    """

    def __init__(self, user):
        self.user = user

    @property
    def is_authenticated(self):
        return (
            self.user is not None
            and self.user.is_authenticated
        )

    @property
    def role_name(self):
        if not self.is_authenticated:
            return None

        if self.user.is_superuser:
            return "Admin"

        if not self.user.role:
            return None

        return self.user.role.name

    @property
    def is_admin(self):
        if not self.is_authenticated:
            return False

        return (
            self.user.is_superuser
            or self.can(Permissions.SYSTEM_MANAGE)
        )

    def can(self, permission):
        """
        التحقق من صلاحية المستخدم.

        مثال:
            authz.can(Permissions.PACKAGES_CASH_FULL)
        """

        if not self.is_authenticated:
            return False

        # Superuser له كل الصلاحيات
        if self.user.is_superuser:
            return True

        # المستخدم بدون Role
        if not self.user.role:
            return False

        return self.user.role.permissions.filter(
            codename=permission
        ).exists()

    def allowed_doctors(self):
        """
        إرجاع قائمة الأطباء الذين يسمح لهذا المستخدم بمتابعة حالاتهم.

        Doctor:
        - الطبيب المرتبط بالحساب
        - الأطباء الإضافيين المحددين من الـ Admin

        باقي المستخدمين:
        - لا يتم تطبيق هذا القيد هنا.
        """

        if not self.is_authenticated:
            return []

        # Admin / Superuser ليس عليه قيد الأطباء
        if self.is_admin:
            return None

        # القيد يخص حسابات Doctor فقط
        if self.role_name != "Doctor":
            return None

        doctors = []

        # الطبيب الأساسي
        if self.user.doctor_name:
            doctors.append(
                self.user.doctor_name.strip()
            )

        # الأطباء الإضافيين
        if self.user.allowed_doctors:
            doctors.extend(
                doctor.strip()
                for doctor in self.user.allowed_doctors
                if doctor and doctor.strip()
            )

        # إزالة التكرار
        return list(dict.fromkeys(doctors))