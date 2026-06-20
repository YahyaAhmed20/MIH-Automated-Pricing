from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "full_name",
        "email",
        "phone",
        "role",
        "is_active",
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            "معلومات إضافية",
            {
                "fields": (
                    "full_name",
                    "phone",
                    "role",
                )
            },
        ),
    )