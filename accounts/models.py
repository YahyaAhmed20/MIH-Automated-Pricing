from django.contrib.auth.models import AbstractUser, Permission
from django.db import models


class Role(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="custom_roles",
        verbose_name="الصلاحيات"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "الدور"
        verbose_name_plural = "الأدوار"
        ordering = ["name"]

        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class User(AbstractUser):

    full_name = models.CharField(
        max_length=255,
        verbose_name="الاسم الكامل"
    )

    email = models.EmailField(
        unique=True,
        null=True,
        blank=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        default="",
        verbose_name="رقم الهاتف"
    )

    role = models.ForeignKey(
        Role,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        verbose_name="الدور"
    )
    doctor_name = models.CharField(
    max_length=255,
    blank=True,
    default="",
    verbose_name="الطبيب المرتبط بالحساب"
)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "المستخدم"
        verbose_name_plural = "المستخدمون"

        indexes = [
            models.Index(fields=["role"]),
        ]

        permissions = [
            # PACKAGES
            (
                "packages_cash_full",
                "صلاحية كاملة على الباكدجات النقدية",
            ),
            (
                "packages_credit_basic",
                "استعراض البيانات الأساسية للباكدجات الآجلة",
            ),
            (
                "packages_credit_full",
                "صلاحية كاملة على الباكدجات الآجلة",
            ),

            # PATIENTS
            (
                "patients_search",
                "البحث عن المرضى",
            ),
            (
                "patients_view",
                "استعراض بيانات المرضى",
            ),

            # EXTERNAL APPROVALS
            (
                "approvals_view",
                "استعراض ومتابعة الموافقات الخارجية",
            ),
            (
                "approvals_statistics",
                "استعراض إحصائيات الموافقات",
            ),
            (
                "approvals_edit",
                "تعديل بيانات الموافقات",
            ),

            # DOCTORS
            (
                "doctors_view_all",
                "استعراض جميع الأطباء",
            ),
            (
                "doctors_view_own",
                "استعراض حالات الطبيب الخاصة به",
            ),
            (
                "doctors_edit",
                "تعديل بيانات الأطباء",
            ),

            # FINANCIAL / CONTRACTS
            (
                "financial_full",
                "صلاحية كاملة على البيانات المالية والتعاقدية",
            ),
            (
                "reports_view",
                "استعراض التقارير والإحصائيات المالية والتشغيلية",
            ),

            # SYSTEM
            (
                "system_manage",
                "إدارة النظام",
            ),
            (
                "users_manage",
                "إدارة المستخدمين",
            ),
            (
                "roles_manage",
                "إدارة الأدوار والصلاحيات",
            ),
        ]

    @property
    def authorization(self):
        from .authorization import Authorization
        return Authorization(self)

    def __str__(self):
        return self.full_name or self.username