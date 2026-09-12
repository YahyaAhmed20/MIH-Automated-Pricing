from django.db import models
from django.shortcuts import render
# Create your models here.

# frontend/models.py

class ReportStatisticSheet15(models.Model):
    """التقارير والإحصائيات - شيت 15"""
    
    # ✅ الأعمدة الأساسية (مطابقة لشيت 11)
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
    
    service_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="سعر الخدمه"
    )
    package_price = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        verbose_name="سعر الباكدج"
    )
    
    # ✅ حقول جديدة في شيت 15
    invoice_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        blank=True,
        null=True,
        default=0,
        verbose_name="قيمة الفاتوره"
    )
    
    code = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        db_index=True,
        verbose_name="الكود"
    )
    
    doctor_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="اسم الطبيب"
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
        ordering = ["-admission_date", "-id"]
        verbose_name = "تقرير وإحصائية - شيت 15"
        verbose_name_plural = "التقارير والإحصائيات - شيت 15"
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
            models.Index(fields=["code"]),
            models.Index(fields=["doctor_name"]),
        ]
    
    def __str__(self):
        return f"{self.patient_name} - {self.package_name} ({self.service_price})"