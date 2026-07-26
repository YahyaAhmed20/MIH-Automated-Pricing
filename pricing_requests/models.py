
from django.db import models
from django.core.exceptions import ValidationError
from accounts.models import User
from contracts.models import ContractEntity, SubCompany
from medical_catalog.models import Specialty
# Create your models here.

class Patient(models.Model):

    full_name = models.CharField(
        max_length=255
    )

    card_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    medical_number = models.CharField(
    max_length=100,
    unique=True,
    blank=True,
    null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "مريض"
        verbose_name_plural = "المرضى"

    def __str__(self):
        return self.full_name
    
    
class PricingRequest(models.Model):

    STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("service_done", "Service Done"),
    ("patient_refused", "Patient Refused"),
    ("unknown", "Unknown"),
]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="pricing_requests"
    )

    entity = models.ForeignKey(
        ContractEntity,
        on_delete=models.PROTECT,
        related_name="pricing_requests"
    )

    sub_company = models.ForeignKey(
        SubCompany,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pricing_requests"
    )

    doctor_name = models.CharField(
        max_length=255
    )

    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name="pricing_requests"
    )

    procedure_name = models.CharField(
        max_length=500
    )

    requested_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    received_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    main_status = models.CharField(
    max_length=100,
    blank=True,
    null=True
    )

    billing_status = models.CharField(
    max_length=100,
    blank=True,
    null=True
    )
    
    approval_number = models.CharField(
    max_length=100,
    blank=True,
    null=True
)

    approval_date = models.DateField(
        blank=True,
        null=True
    )

    approval_expiry_date = models.DateField(
        blank=True,
        null=True
    )

    account_number = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    expected_admission_date = models.DateField(
        blank=True,
        null=True
    )
    service_date = models.DateField(
    blank=True,
    null=True
)

    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="pending"
    )

    created_by = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="created_pricing_requests"
)
    agent_1 = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="agent1_requests"
)

    agent_2 = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name="agent2_requests"
)

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    request_date = models.DateField(
    blank=True,
    null=True
)

    class Meta:
        verbose_name = "طلب تسعير"
        verbose_name_plural = "طلبات التسعير"
        indexes = [
        models.Index(fields=["status"]),
        models.Index(fields=["entity"]),
        models.Index(fields=["specialty"]),
        models.Index(fields=["expected_admission_date"]),
    ]

    def __str__(self):
        return f"{self.patient} - {self.procedure_name}"
    
    def clean(self):
        if (
            self.sub_company
            and self.sub_company.entity != self.entity
        ):
            raise ValidationError(
                "الشركة الفرعية لا تنتمي لهذه الجهة."
            )
    
    
class PricingRequestFile(models.Model):

    FILE_TYPES = [
        ("report", "Report"),
        ("approval", "Approval"),
        ("other", "Other"),
    ]

    pricing_request = models.ForeignKey(
        PricingRequest,
        on_delete=models.CASCADE,
        related_name="files"
    )

    file_type = models.CharField(
        max_length=20,
        choices=FILE_TYPES
    )

    file = models.FileField(
        upload_to="pricing_requests/"
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.pricing_request_id} - {self.file_type}"
    
    

class PricingRequestNote(models.Model):

    DEPARTMENTS = [
    ("sales", "Sales"),
    ("accounts", "Accounts"),
    ("or_coordinator", "OR Coordinator"),
    ("approvals", "Approvals"),
]

    pricing_request = models.ForeignKey(
        PricingRequest,
        on_delete=models.CASCADE,
        related_name="notes"
    )

    department = models.CharField(
        max_length=20,
        choices=DEPARTMENTS
    )

    note = models.TextField()

    created_by = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    related_name="pricing_request_notes"
)

    created_at = models.DateTimeField(
        auto_now_add=True
    )
    source = models.CharField(
    max_length=100,
    blank=True,
    null=True
)

    def __str__(self):
        return f"{self.department}"
    
    
class PricingStatusHistory(models.Model):

    pricing_request = models.ForeignKey(
        PricingRequest,
        on_delete=models.CASCADE,
        related_name="status_history"
    )

    old_status = models.CharField(
        max_length=30
    )

    new_status = models.CharField(
        max_length=30
    )

    changed_by = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    related_name="pricing_status_changes"
)

    changed_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.old_status} -> {self.new_status}"
    
    class Meta:
        ordering = ["-changed_at"]

        indexes = [
            models.Index(fields=["pricing_request"]),
    ]
        
        
class ServiceRecord(models.Model):

    account_number = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="الرقم الحسابى"
    )

    patient_type = models.CharField(
        max_length=50,
        db_index=True,
        verbose_name="نوع المريض"
    )

    patient_name = models.CharField(
        max_length=255,
        verbose_name="اسم المريض"
    )

    admission_date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name="تاريخ الدخول"
    )

    discharge_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ الخروج"
    )

    stay_duration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="مدة الإقامة"
    )

    department_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="اسم القسم"
    )

    service_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="اسم الخدمة"
    )

    service_code = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="الكود"
    )

    service_date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name="التاريخ"
    )

    insurance_company = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="شركة التأمين"
    )

    sub_company = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="الشركة الفرعية"
    )

    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0,
        verbose_name="المبلغ"
    )
    total_invoice = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="اجمالي الفاتورة"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        verbose_name = "سجل خدمة"

        verbose_name_plural = "سجلات الخدمات"

        ordering = [
            "-service_date",
            "service_name",
        ]

        indexes = [
            models.Index(fields=["service_name"]),
            models.Index(fields=["service_code"]),
            models.Index(fields=["department_name"]),
            models.Index(fields=["patient_type"]),
            models.Index(fields=["service_date"]),
            models.Index(fields=["insurance_company"]),
        ]
        
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "account_number",
                    "service_code",
                ],
                name="unique_service_record"
            )
        ]
        
class PricingDetail(models.Model):

    pricing_date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name="تاريخ التسعير"
    )

    group_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الجروب"
    )

    patient_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="اسم المريض"
    )

    company_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الشركة"
    )

    doctor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="اسم الطبيب"
    )

    report_name = models.TextField(
        blank=True,
        null=True,
        verbose_name="التقرير"
    )

    procedure_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الإجراء"
    )

    specialty_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="التخصص"
    )

    pricing_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="نوع التسعير"
    )

    card_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="رقم الكارنية"
    )

    accountant_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="اسم المحاسب"
    )

    cost_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات خاصة بالتكلفة"
    )

    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="التكلفة"
    )

    details = models.TextField(
        blank=True,
        null=True,
        verbose_name="التفاصيل"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        verbose_name = "تفصيل تسعير"

        verbose_name_plural = "تفاصيل التسعير"

        ordering = [
        "-pricing_date",
        "-cost",
    ]

        indexes = [
            models.Index(fields=["patient_name"]),
            models.Index(fields=["company_name"]),
            models.Index(fields=["doctor_name"]),
            models.Index(fields=["specialty_name"]),
            models.Index(fields=["group_name"]),
            models.Index(fields=["pricing_date"]),
        ]

    def __str__(self):
        return f"{self.patient_name} - {self.procedure_name}"
    
    


class SimilarInvoice(models.Model):

    account_number = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="الرقم الحسابي"
    )

    medical_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الرقم الطبي"
    )

    patient_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="اسم المريض"
    )

    admission_date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name="تاريخ الدخول"
    )

    discharge_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ الخروج"
    )

    stay_duration = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="مدة الاقامة"
    )

    specialty_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="التخصص"
    )

    doctor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="اسم الطبيب"
    )

    operation_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="اسم العملية"
    )

    entity_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الجهة"
    )

    sub_company = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="الشركة الفرعية"
    )

    building = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="الدور / المبنى"
    )

    total_invoice = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    discount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    net_invoice = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    company_share = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    patient_share = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    payments = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    invoice_status = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="حالة الفاتورة"
    )

    invoice_closed_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ إنهاء الفاتورة"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        verbose_name = "فاتورة مماثلة"

        verbose_name_plural = "فواتير مماثلة"

        ordering = [
            "-admission_date",
            "-id",
        ]

        indexes = [
            models.Index(fields=["patient_name"]),
            models.Index(fields=["operation_name"]),
            models.Index(fields=["entity_name"]),
            models.Index(fields=["doctor_name"]),
            models.Index(fields=["specialty_name"]),
            models.Index(fields=["admission_date"]),
        ]

    def __str__(self):
        return f"{self.patient_name} - {self.operation_name}"
    
class Procedure(models.Model):

    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        verbose_name="الكود"
    )

    operation_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="اسم العملية"
    )

    specialty_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="التخصص"
    )

    category = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="التصنيف"
    )

    english_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="المسمى باللغة الإنجليزية"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        verbose_name = "توصيف عملية"

        verbose_name_plural = "توصيف العمليات"

        ordering = [
            "operation_name",
        ]

        indexes = [
            models.Index(fields=["operation_name"]),
            models.Index(fields=["specialty_name"]),
        ]

    def __str__(self):
        return f"{self.code} - {self.operation_name}" 
    
    


# ✅ ✅ ✅ دالة التحقق من صحة التصنيف
def validate_category(value):
    """
    التحقق من صحة التصنيف ومنع إدخال تصنيفات خاطئة
    """
    if not value:
        return
    
    # ✅ التصنيفات الصحيحة (من جدول Procedure)
    valid_categories = ['صغـــرى', 'كــبرى', 'متوسطة', 'متقدمة', 'مهارة', 'ذات طابع خاص']
    
    # ✅ توحيد التصنيف قبل التحقق
    mapping = {
        'صغرى': 'صغـــرى',
        'كبرى': 'كــبرى',
        'طابع خاص': 'ذات طابع خاص',
        'صغرى ': 'صغـــرى',
        'كبرى ': 'كــبرى',
        'طابع خاص ': 'ذات طابع خاص',
    }
    normalized = mapping.get(value.strip(), value.strip())
    
    if normalized not in valid_categories:
        raise ValidationError(
            f"التصنيف '{value}' غير صالح. "
            f"التصنيفات المسموحة: {', '.join(valid_categories)}"
        )

from django.db import models
from django.core.exceptions import ValidationError
from django.db.models.signals import pre_save
from django.dispatch import receiver
class ProcedureFee(models.Model):

    entity_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="الجهة"
    )

    financial_category = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="الفئة المالية"
    )

    price_list = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="قائمة الأسعار"
    )

    category = models.CharField(
        max_length=100,
        db_index=True,
        verbose_name="التصنيف",
        validators=[validate_category]  # ✅ إضافة الـ Validator
    )

    surgeon_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    anesthesia_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    assistant_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    total_fee = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    discount_rate = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="معدل الخصم"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:

        verbose_name = "أتعاب عملية"

        verbose_name_plural = "احتساب أتعاب العمليات"

        ordering = [
            "entity_name",
            "category",
        ]

        indexes = [
            models.Index(fields=["entity_name"]),
            models.Index(fields=["financial_category"]),
            models.Index(fields=["category"]),
        ]

    def __str__(self):
        return f"{self.entity_name} - {self.category}"


# ✅ ✅ ✅ Signal لتوحيد التصنيف تلقائياً قبل الحفظ
@receiver(pre_save, sender=ProcedureFee)
def normalize_procedure_fee_category(sender, instance, **kwargs):
    """
    توحيد التصنيف تلقائياً قبل حفظ أي سجل جديد أو تحديث
    """
    if instance.category:
        mapping = {
            'صغرى': 'صغـــرى',
            'كبرى': 'كــبرى',
            'طابع خاص': 'ذات طابع خاص',
            'صغرى ': 'صغـــرى',
            'كبرى ': 'كــبرى',
            'طابع خاص ': 'ذات طابع خاص',
        }
        instance.category = mapping.get(instance.category.strip(), instance.category.strip())
class CompanyDiscountRank(models.Model):

    company_name = models.CharField(
        max_length=255,
        db_index=True
    )

    financial_category = models.CharField(
        max_length=100
    )

    price_list = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    internal_discount = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0
    )

    external_discount = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        default=0
    )

    attachment = models.TextField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = [
            "-internal_discount",
            "-external_discount",
            "company_name",
        ]

    def __str__(self):
        return self.company_name
    
    
class CompanyException(models.Model):

    entity_name = models.CharField(
        max_length=255,
        db_index=True
    )

    financial_category = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    price_list = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # ✅ القسم الداخلي
    internal_discount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="معدل الخصم الداخلي"
    )

    internal_details = models.TextField(
        blank=True,
        null=True,
        help_text="تفاصيل الخصم الداخلي"
    )

    # ✅ القسم الخارجي
    external_discount = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="معدل الخصم الخارجي"
    )

    external_details = models.TextField(
        blank=True,
        null=True,
        help_text="تفاصيل الخصم الخارجي"
    )

    attachment = models.TextField(
        blank=True,
        null=True,
        help_text="رابط المرفقات"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["entity_name"]
        verbose_name = "استثناءات الشركة"
        verbose_name_plural = "استثناءات الشركات"

    def __str__(self):
        return self.entity_name
    
    
    
# ============================================
# ✅ Company Exception Models (جديد - بدون تعديل القديم)
# ============================================

class CompanyExceptionProfile(models.Model):
    """ملف استثناءات الشركة"""
    
    entity_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="اسم الجهة"
    )
    
    financial_category = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="الفئة المالية"
    )
    
    price_list = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="قائمة الأسعار"
    )
    
    attachment = models.TextField(
        blank=True,
        null=True,
        verbose_name="المرفقات"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        ordering = ["entity_name"]
        verbose_name = "ملف استثناءات شركة"
        verbose_name_plural = "ملفات استثناءات الشركات"
    
    def __str__(self):
        return self.entity_name


class CompanyExceptionItem(models.Model):
    """عنصر استثناء (خدمة داخلية/خارجية)"""
    
    SECTION_CHOICES = [
        ("داخلي", "داخلي"),
        ("خارجي", "خارجي"),
    ]
    
    profile = models.ForeignKey(
        CompanyExceptionProfile,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="ملف الاستثناءات"
    )
    
    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES,
        verbose_name="القسم"
    )
    
    service_name = models.CharField(
        max_length=255,
        verbose_name="اسم الخدمة"
    )
    
    discount_rate = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="نسبة الخصم"
    )
    
    details = models.TextField(
        blank=True,
        null=True,
        verbose_name="التفاصيل"
    )
    
    net_price = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="السعر الصافي"
    )
    
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name="ترتيب العرض"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        ordering = ["section", "display_order"]
        verbose_name = "عنصر استثناء"
        verbose_name_plural = "عناصر الاستثناءات"
    
    def __str__(self):
        return f"{self.profile.entity_name} - {self.service_name}"
    
    
# ============================================
# ✅ Report / Statistics - Sheet 11
# ============================================

class ReportStatistic(models.Model):
    """التقارير والإحصائيات - شيت 11"""
    
    # ✅ الأعمدة الأساسية
    medical_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الرقم الطبي"
    )
    
    account_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الرقم الحسابى"
    )
    
    patient_name = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="اسم المريض"
    )
    
    admission_date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name="تاريخ الدخول"
    )
    
    discharge_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ الخروج"
    )
    
    month = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الشهر"
    )
    
    specialty = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="التخصص"
    )
    
    package_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="اسم الباكدج"
    )
    
    entity_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الجهه"
    )
    
    sector = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="القطاع"
    )
    
    payment_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="نوع الدفع"
    )
    
    sub_company = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الشركه الفرعيه"
    )
    
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="المبلغ"
    )
    
    # ✅ حقول جديدة من شيت 11
    invoice_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="قيمة الفاتوره"
    )
    
    code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="الكود"
    )
    
    patient_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="نوع المريض"
    )
    
    stay_duration = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="مدة الاقامه"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات"
    )
    
    # ✅ اسم الطبيب (العمود الأخير)
    doctor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="اسم الطبيب"
    )
    
    # ✅ حقول إضافية للتحكم
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        ordering = ["-admission_date", "-id"]
        verbose_name = "تقرير وإحصائية"
        verbose_name_plural = "التقارير والإحصائيات"
        indexes = [
            models.Index(fields=["patient_name"]),
            models.Index(fields=["entity_name"]),
            models.Index(fields=["specialty"]),
            models.Index(fields=["package_name"]),
            models.Index(fields=["admission_date"]),
            models.Index(fields=["sector"]),
            models.Index(fields=["account_number"]),
            models.Index(fields=["month"]),
            models.Index(fields=["payment_type"]),
            models.Index(fields=["doctor_name"]),  # ✅ إضافة فهرس للطبيب
        ]
    
    def __str__(self):
        return f"{self.patient_name} - {self.package_name} ({self.amount})"
    
# ============================================
# ✅ External Approvals Follow-up - Sheet 12
# ============================================

class ExternalApproval(models.Model):
    """متابعة موافقات الخارجي - شيت 12"""
    
    # ✅ الأعمدة الأساسية
    attachment_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="ملحق او رئيسى"
    )
    
    patient_name = models.CharField(
    max_length=255,
    blank=True,
    null=True,
    db_index=True,
    verbose_name="اسم المريض"
    )
    
    card_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="رقم الكارنية"
    )
    
    company = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الشركة"
    )
    
    sub_account = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Sub Account"
    )
    
    date = models.DateField(
        blank=True,
        null=True,
        db_index=True,
        verbose_name="التاريخ"
    )
    
    medical_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الرقم الطبي"
    )
    
    doctor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الطبيب"
    )
    
    specialty = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="التخصص"
    )
    
    required = models.TextField(
        blank=True,
        null=True,
        verbose_name="المطلوب"
    )
    
    procedure = models.TextField(
        blank=True,
        null=True,
        verbose_name="الاجراء"
    )
    
    phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="رقم التليفون"
    )
    
    agent_1 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Agent 1"
    )
    
    status = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Status"
    )
    
    main_status = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Main Status"
    )
    
    initial_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="التكلفه المبدئية"
    )
    
    pricing_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ التسعير"
    )
    
    pricing_responsible = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="مسئول التسعير"
    )
    
    billing_status = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="Billing Status"
    )
    
    approval_review_responsible = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="مسئول مراجعة الموافقة و التسعير"
    )
    
    accounts_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات الحسابات"
    )
    
    account_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الرقم الحسابى"
    )
    
    received_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="التكلفة المستلمه"
    )
    
    report = models.TextField(
        blank=True,
        null=True,
        verbose_name="Report"
    )
    
    approval = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Approval"
    )
    
    request_approval_no = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Request and Approval NO."
    )
    
    approval_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Approval Date"
    )
    
    expiry_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Expiry Date"
    )
    
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="الملاحظات"
    )
    
    last_update = models.DateField(
        blank=True,
        null=True,
        verbose_name="Last Update"
    )
    
    agent_2 = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Agent 2"
    )
    
    opd_sales_cs = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="OPD ,Sales or CS"
    )
    
    admission_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="تاريخ الدخول"
    )
    
    or_coordinator_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات الـ OR Coordinator"
    )
    
    sales_account = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="sales account"
    )
    
    head = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Head"
    )
    
    user = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="USER"
    )
    
    sales_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات السيلز"
    )
    
    # ✅ حقول التحكم
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="تاريخ الإنشاء"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="تاريخ التحديث"
    )
    
    class Meta:
        ordering = ["-date", "-id"]
        verbose_name = "متابعة موافقة خارجي"
        verbose_name_plural = "متابعة موافقات الخارجي"
        indexes = [
            models.Index(fields=["patient_name"]),
            models.Index(fields=["company"]),
            models.Index(fields=["specialty"]),
            models.Index(fields=["status"]),
            models.Index(fields=["main_status"]),
            models.Index(fields=["date"]),
            models.Index(fields=["account_number"]),
        ]
    
    def __str__(self):
        return f"{self.patient_name} - {self.company} ({self.date})"