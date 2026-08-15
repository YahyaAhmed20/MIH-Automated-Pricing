from django.contrib import admin
from django import forms

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserCreationForm

from .models import User, Role
from pricing_requests.models import ExternalApproval


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )

    search_fields = (
        "name",
    )

    filter_horizontal = (
        "permissions",
    )


# =========================================================
# Doctor choices
# =========================================================

def get_doctor_choices():
    doctors = (
        ExternalApproval.objects
        .exclude(doctor_name__isnull=True)
        .exclude(doctor_name="")
        .values_list("doctor_name", flat=True)
        .distinct()
        .order_by("doctor_name")
    )

    return [
        ("", "---------"),
        *[(doctor, doctor) for doctor in doctors],
    ]


# =========================================================
# User Form
# =========================================================

class CustomUserForm(forms.ModelForm):

    doctor_name = forms.ChoiceField(
        label="الطبيب المرتبط بالحساب",
        required=False,
        choices=(),
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["doctor_name"].choices = get_doctor_choices()

    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get("role")

        if not role or role.name != "Doctor":
            cleaned_data["doctor_name"] = ""

        return cleaned_data

    class Media:
        js = ("admin/js/user_role_doctor.js",)


# =========================================================
# User Creation Form
# =========================================================

class CustomUserCreationForm(UserCreationForm):

    doctor_name = forms.ChoiceField(
        label="الطبيب المرتبط بالحساب",
        required=False,
        choices=(),
    )

    class Meta:
        model = User
        fields = (
            "username",
            "password1",
            "password2",
            "full_name",
            "email",
            "phone",
            "role",
            "doctor_name",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["doctor_name"].choices = get_doctor_choices()

    def clean(self):
        cleaned_data = super().clean()

        role = cleaned_data.get("role")

        if not role or role.name != "Doctor":
            cleaned_data["doctor_name"] = ""

        return cleaned_data

    class Media:
        js = ("admin/js/user_role_doctor.js",)


# =========================================================
# User Admin
# =========================================================

@admin.register(User)
class CustomUserAdmin(UserAdmin):

    form = CustomUserForm
    add_form = CustomUserCreationForm

    list_display = (
        "username",
        "full_name",
        "email",
        "phone",
        "role",
        "doctor_name",
        "is_active",
    )

    search_fields = (
        "username",
        "full_name",
        "email",
        "phone",
        "doctor_name",
    )

    list_filter = (
        "role",
        "is_active",
        "is_staff",
    )

    fieldsets = (
        (
            "تسجيل الدخول",
            {
                "fields": (
                    "username",
                    "password",
                )
            },
        ),
        (
            "معلومات إضافية",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "role",
                    "doctor_name",
                )
            },
        ),
        (
            "الصلاحيات",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (
            "التواريخ",
            {
                "fields": (
                    "last_login",
                    "date_joined",
                )
            },
        ),
    )

    add_fieldsets = (
        (
            "بيانات تسجيل الدخول",
            {
                "fields": (
                    "username",
                    "password1",
                    "password2",
                )
            },
        ),
        (
            "معلومات إضافية",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "role",
                    "doctor_name",
                )
            },
        ),
    )