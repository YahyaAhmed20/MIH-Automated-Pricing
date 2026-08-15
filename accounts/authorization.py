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