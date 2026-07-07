
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
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name="المبلغ"
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