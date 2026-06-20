from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "المستخدم"
        verbose_name_plural = "المستخدمون"
        indexes = [
            models.Index(fields=["role"]),
        ]

    def __str__(self):
        return self.full_name or self.username