from django.db import models

# Create your models here.


class Specialty(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="اسم التخصص"
    )

    color = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name="اللون"
    )

    icon = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="الأيقونة"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "التخصص"
        verbose_name_plural = "التخصصات"
        ordering = ["name"]

    def __str__(self):
        return self.name
    
    
class Procedure(models.Model):

    CLASSIFICATION_CHOICES = [
        ("صغرى", "صغرى"),
        ("متوسطة", "متوسطة"),
        ("كبرى", "كبرى"),
        ("مهارة", "مهارة"),
        ("طابع خاص", "طابع خاص"),
        ("متقدمة", "متقدمة"),
    ]

    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name="procedures"
    )

    code = models.CharField(
    max_length=100,
    unique=True,
    db_index=True
    )

    name_ar = models.CharField(
        max_length=500
    )

    name_en = models.CharField(
        max_length=500,
        blank=True,
        null=True
    )

    classification = models.CharField(
        max_length=50,
        choices=CLASSIFICATION_CHOICES,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "الإجراء"
        verbose_name_plural = "الإجراءات"
        ordering = ["code"]
        indexes = [
        models.Index(fields=["specialty"]),
    ]

    def __str__(self):
        return f"{self.code} - {self.name_ar}"
    
    
class Package(models.Model):

    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name="packages"
    )

    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="packages"
    )

    name = models.CharField(
        max_length=500
    )

    code = models.CharField(
    max_length=100,
    blank=True,
    null=True,
    db_index=True
    )
    
    base_price = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    blank=True,
    null=True
    )

    stay_duration = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    effective_from = models.DateField(
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    is_cash_package = models.BooleanField(
        default=False
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "الباكدج"
        verbose_name_plural = "الباكدجات"
        ordering = ["name"]
        indexes = [
        models.Index(fields=["specialty"]),
    ]

    def __str__(self):
        return self.name
    
    
class PackageAttachment(models.Model):

    package = models.OneToOneField(
        Package,
        on_delete=models.CASCADE,
        related_name="attachment"
    )

    package_pdf = models.FileField(
        upload_to="packages/includes/",
        blank=True,
        null=True
    )

    operation_instruction_pdf = models.FileField(
        upload_to="packages/instructions/",
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "مرفق الباكدج"
        verbose_name_plural = "مرفقات الباكدجات"

    def __str__(self):
        return self.package.name
    
    
    
