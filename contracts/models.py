from django.db import models
from django.core.exceptions import ValidationError
from medical_catalog.models import (
    Specialty,
    Package,
)
# Create your models here.
class ContractEntity(models.Model):
    name = models.CharField(
        max_length=255,
        unique=True
    )

    contract_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    notes = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        verbose_name = "الجهة"
        verbose_name_plural = "الجهات المتعاقدة"
        ordering = ["name"]

    def __str__(self):
        return self.name
    
class SubCompany(models.Model):

    entity = models.ForeignKey(
        ContractEntity,
        on_delete=models.CASCADE,
        related_name="sub_companies"
    )

    name = models.CharField(
        max_length=255
    )

    code = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "شركة فرعية"
        verbose_name_plural = "الشركات الفرعية"
        ordering = ["name"]
        constraints = [
        models.UniqueConstraint(
            fields=["entity", "name"],
            name="unique_subcompany_per_entity"
        )
    ]

    def __str__(self):
        return self.name
    
    
class FinancialCategory(models.Model):

    entity = models.ForeignKey(
        ContractEntity,
        on_delete=models.CASCADE,
        related_name="financial_categories"
    )

    code = models.CharField(
        max_length=100
    )

    description = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "الفئة المالية"
        verbose_name_plural = "الفئات المالية"
        ordering = ["code"]
        
        constraints = [
        models.UniqueConstraint(
            fields=["entity", "code"],
            name="unique_financial_category_per_entity"
        )
    ]

    def __str__(self):
        return self.code
    
    
class PriceList(models.Model):

    name = models.CharField(
        max_length=255
    )

    effective_from = models.DateField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "قائمة أسعار"
        verbose_name_plural = "قوائم الأسعار"
        ordering = ["name"]

    def __str__(self):
        return self.name
    
    
    
class Contract(models.Model):

    entity = models.ForeignKey(
        ContractEntity,
        on_delete=models.CASCADE,
        related_name="contracts"
    )

    financial_category = models.ForeignKey(
        FinancialCategory,
        on_delete=models.PROTECT,
        related_name="contracts"
    )

    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.PROTECT,
        related_name="contracts"
    )

    contract_type = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    medical_service_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
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

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )
    medical_service = models.CharField(
    max_length=255,
    blank=True,
    null=True,
    verbose_name="الخدمة الطبية"
    )

    operating_instructions = models.TextField(
    blank=True,
    null=True,
    verbose_name="تعليمات التشغيل"
    )
    operating_pdf = models.URLField(
    blank=True,
    null=True
)

    class Meta:
        verbose_name = "عقد"
        verbose_name_plural = "العقود"
        
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "entity",
                    "financial_category",
                    "price_list"
                ],
                name="unique_contract_configuration"
            )
        ]

    def __str__(self):
        return f"{self.entity} - {self.financial_category}"
    
    def clean(self):
        if (
            self.entity
            and self.financial_category
            and self.financial_category.entity != self.entity
        ):
            raise ValidationError(
                "الفئة المالية لا تنتمي لهذه الجهة."
            )
    
    
    
    
class CoverageCategory(models.Model):

    SECTION_CHOICES = [
        ("internal", "داخلي"),
        ("external", "خارجي"),
    ]

    name = models.CharField(
        max_length=255,
        unique=True
    )

    section = models.CharField(
        max_length=20,
        choices=SECTION_CHOICES
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        verbose_name = "فئة تغطية"
        verbose_name_plural = "فئات التغطية"
        ordering = ["name"]

    def __str__(self):
        return self.name
    
    
class CoverageRule(models.Model):

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="coverage_rules"
    )

    category = models.ForeignKey(
        CoverageCategory,
        on_delete=models.PROTECT,
        related_name="coverage_rules"
    )

    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True
    )

    details = models.TextField(
        blank=True,
        null=True
    )

    net_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True
    )

    exceptions = models.TextField(
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "قاعدة خصم"
        verbose_name_plural = "قواعد الخصومات"

        constraints = [
            models.UniqueConstraint(
                fields=["contract", "category"],
                name="unique_coverage_rule_per_contract"
            )
        ]

        indexes = [
            models.Index(fields=["contract"]),
        ]

    def __str__(self):
        return f"{self.contract} - {self.category}"
    


    
class ProfessionalFeeRule(models.Model):


    CLASSIFICATION_CHOICES = [
    ("صغرى", "صغرى"),
    ("متوسطة", "متوسطة"),
    ("كبرى", "كبرى"),
    ("مهارة", "مهارة"),
    ("طابع خاص", "طابع خاص"),
    ("متقدمة", "متقدمة"),
]



    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="professional_fee_rules"
    )

    classification = models.CharField(
    max_length=50,
    choices=CLASSIFICATION_CHOICES
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

    discount_note = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = "أتعاب الأطباء"
        verbose_name_plural = "أتعاب الأطباء"

        constraints = [
            models.UniqueConstraint(
                fields=["contract", "classification"],
                name="unique_professional_fee_per_contract"
            )
        ]
        indexes = [
        models.Index(fields=["contract"]),
    ]

    def __str__(self):
        return f"{self.contract} - {self.classification}"
    
    
class SpecialOffer(models.Model):

    entity = models.ForeignKey(
        ContractEntity,
        on_delete=models.CASCADE,
        related_name="special_offers"
    )

    offer_for = models.CharField(
        max_length=255
    )

    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name="special_offers"
    )

    procedure_name = models.CharField(
        max_length=500
    )

    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
    )

    valid_from = models.DateField()

    valid_to = models.DateField()

    notes = models.TextField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "عرض خاص"
        verbose_name_plural = "العروض الخاصة"
        
        indexes = [
            models.Index(fields=["entity"]),
            models.Index(fields=["specialty"]),
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "entity",
                    "offer_for",
                    "specialty",
                    "procedure_name",
                ],
                name="unique_special_offer",
            ),
        ]

    def __str__(self):
        return f"{self.entity} - {self.procedure_name}"
    
class ContractPackage(models.Model):

    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name="contract_packages"
    )

    package = models.ForeignKey(
        Package,
        on_delete=models.CASCADE,
        related_name="contract_packages"
    )

    package_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="سعر الباكدج"
    )

    total_before_discount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="الإجمالي قبل الخصم"
    )

    current_discount_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="نسبة الخصم الحالية"
    )

    cash_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="السعر النقدي"
    )

    special_offer_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="سعر العرض الخاص"
    )
    current_discount_text = models.CharField(
    max_length=100,
    blank=True,
    null=True,
    verbose_name="نص الخصم الحالي"
)

    # ✅ الحقول الجديدة (مضافة)
    special_offer_company = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="شركة العرض الخاص"
    )

    price_list_applied = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="قائمة الأسعار المطبقة"
    )

    effective_from = models.DateField(
        blank=True,
        null=True,
        verbose_name="ساري من"
    )
    approval_pdf = models.TextField(
    blank=True,
    null=True
)


    valid_until = models.DateField(
        blank=True,
        null=True
    )
    
    suggested_price = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    null=True,
    blank=True,
)

    suggested_discount_rate = models.DecimalField(
    max_digits=5,
    decimal_places=2,
    null=True,
    blank=True,
)

    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="ملاحظات"
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name="نشط"
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
        verbose_name = "تسعير الباكدج"
        verbose_name_plural = "تسعير الباكدجات"

        constraints = [
            models.UniqueConstraint(
                fields=["contract", "package"],
                name="unique_package_per_contract"
            )
        ]

        indexes = [
            models.Index(fields=["contract"]),
            models.Index(fields=["package"]),
            models.Index(fields=["contract", "package"]),  # ✅ فهرس مركب للاستعلامات السريعة
        ]

    def __str__(self):
        return f"{self.contract} - {self.package}"
    
    
    
    
class CompanyDiscountProfile(models.Model):
    
    
    company_name = models.CharField(
    max_length=255
    )

    contract_type = models.CharField(
        max_length=100,
        blank=True
    )

    financial_category = models.CharField(
        max_length=100,
        blank=True
    )

    price_list = models.CharField(
        max_length=100,
        blank=True
    )

    operating_pdf = models.URLField(
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Company Discount Profile"
        verbose_name_plural = "Company Discount Profiles"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "company_name",
                    "financial_category",
                ],
                name="unique_company_discount_profile",
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "company_name",
                    "financial_category",
                ]
            ),
        ]

    def __str__(self):
        return f"{self.company_name} - {self.financial_category}"


class CompanyDiscount(models.Model):
    
    profile = models.ForeignKey(
        CompanyDiscountProfile,
        on_delete=models.CASCADE,
        related_name="discounts",
        null=True,  # ✅ مؤقتاً
        blank=True,  # ✅ مؤقتاً
    )

    section = models.CharField(
        max_length=20
    )

    item_name = models.CharField(
        max_length=200
    )

    discount = models.CharField(
        max_length=100,
        blank=True
    )

    details = models.TextField(
        blank=True
    )

    net_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    display_order = models.PositiveIntegerField(
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        verbose_name = "Company Discount"
        verbose_name_plural = "Company Discounts"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "profile",
                    "section",
                    "item_name",
                ],
                name="unique_company_discount",
            )
        ]

        indexes = [
            models.Index(
                fields=[
                    "profile",
                    "section",
                ]
            ),
        ]

    def __str__(self):
        return f"{self.profile} - {self.section} - {self.item_name}"