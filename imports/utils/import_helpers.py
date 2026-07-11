import re

import pandas as pd

class ImportHelpers:

    @staticmethod
    def normalize_text(value):

        if pd.isna(value):
            return ""

        return " ".join(
            str(value)
            .replace("\r", " ")
            .replace("\n", " ")
            .split()
        )

    @staticmethod
    def clean_date(value):

        if pd.isna(value):
            return None

        try:
            return pd.to_datetime(value).date()
        except Exception:
            return None

    @staticmethod
    def clean_decimal(value):
        """
        تحويل القيمة إلى float مع دعم الفواصل الآلاف
        مثال: 1,250.50 -> 1250.50
        """
        if pd.isna(value):
            return None

        try:
            # إزالة الفواصل الآلاف قبل التحويل
            cleaned = str(value).replace(",", "")
            return float(cleaned)
        except Exception:
            return None

    # ============================================================
    # ✅ Helper: معالجة النسب المئوية
    # ============================================================
    @staticmethod
    def clean_percentage(value):
        """
        يحول نسب Excel إلى نسبة مئوية فعلية.

        أمثلة:
        0.05 -> 5
        0.15 -> 15
        5 -> 5
        15 -> 15
        """
        value = ImportHelpers.clean_decimal(value)

        if value is None:
            return None

        if 0 < value <= 1:
            value *= 100

        return value

    @staticmethod
    def normalize_package_codes(value):
        """
        تنظيف أكواد الباكدجات ودعم الأكواد المتعددة

        مثال:
        NPH0004
        NPH0005

        ↓

        ["NPH0004", "NPH0005"]

        يدعم الفواصل: , و ؛ و / و \n
        """
        if pd.isna(value):
            return []

        value = str(value).strip()

        if not value:
            return []

        # تقسيم الأكواد على الفواصل المختلفة
        codes = re.split(
            r"[\n\r,،;/]+",
            value
        )

        # تنظيف النتائج وإزالة القيم الفارغة
        return [
            code.strip()
            for code in codes
            if code.strip()
        ]
        
    
    
    # ============================================================
    # ✅ Normalize Company Name
    # ============================================================
    @staticmethod
    def normalize_company_name(value):

        return ImportHelpers.normalize_text(value)

  
    @staticmethod
    def package_lookup_key(
        package_code,
        package_name,
    ):
        return (
            ImportHelpers.normalize_text(package_code),
            ImportHelpers.normalize_text(package_name),
        )
        
        
    # ============================================================
    # ✅ Get Or Create Specialty
    # ============================================================
    @staticmethod
    def get_or_create_specialty(
        specialty_name,
        specialties_cache,
        result=None,
    ):

        from medical_catalog.models import Specialty

        specialty_name = (
            ImportHelpers.normalize_text(
                specialty_name
            )
        )

        if not specialty_name:
            if result:
                result["missing_specialty"] += 1
            return None

        specialty = specialties_cache.get(
            specialty_name
        )

        if specialty:
            return specialty

        specialty = Specialty.objects.create(
            name=specialty_name,
            is_active=True,
        )

        specialties_cache[specialty_name] = specialty

        if result:
            result["created_specialties"] += 1

        return specialty

    # ============================================================
    # ✅ Helper: تنظيف قيمة الخصم
    # ============================================================
    @staticmethod
    def clean_discount(value):
        """
        تنظيف قيمة الخصم وتحويلها من رقم عشري إلى نسبة مئوية

        أمثلة:
        0.1 -> "10%"
        0.15 -> "15%"
        0.05 -> "5%"
        "10%" -> "10%"
        "عرض خاص" -> "عرض خاص"
        """
        if pd.isna(value):
            return ""

        if isinstance(value, (int, float)):
            return f"{value * 100:.0f}%"

        return ImportHelpers.normalize_text(value)

    # ============================================================
    # ✅ Helper: معالجة المبلغ
    # ============================================================
    @staticmethod
    def clean_amount(value):
        """
        تنظيف قيمة المبلغ
        مثال: 1,250.50 -> 1250.50
        """
        if pd.isna(value):
            return 0
        
        try:
            if isinstance(value, str):
                # إزالة الفواصل الآلاف
                cleaned = value.replace(",", "").strip()
                return float(cleaned)
            return float(value)
        except Exception:
            return 0