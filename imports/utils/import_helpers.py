# imports/utils/import_helpers.py

import re
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime


class ImportHelpers:

    @staticmethod
    def normalize_text(value):
        """
        تنظيف النصوص وإزالة المسافات الزائدة والأسطر الجديدة
        """
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
        """
        تنظيف قيمة التاريخ وتحويلها إلى كائن date أو None
        ✅ يدعم جميع الصيغ الممكنة
        ✅ يدعم الصيغة المصرية YYYY/MM/DD
        ✅ يدعم الأرقام (timestamps)
        """
        if pd.isna(value):
            return None

        if value in ("", None):
            return None

        # ✅ لو كانت القيمة رقم 0 أو قيمة فارغة
        if isinstance(value, (int, float)):
            if value == 0:
                return None
            # لو كانت قيمة رقمية كبيرة (timestamp)
            if value > 1000:
                try:
                    return pd.to_datetime(value, unit='d').date()
                except:
                    return None

        # ✅ لو كانت نصاً
        if isinstance(value, str):
            value = value.strip()
            if not value or value in ['0', 'NULL', 'null', 'None', '']:
                return None

        # ✅ محاولة الصيغ المختلفة (الأولوية للصيغة المصرية)
        for fmt in (
            "%Y/%m/%d",     # 2026/8/10 (الصيغة المصرية)
            "%Y-%m-%d",     # 2026-08-10
            "%m/%d/%Y",     # 8/10/2026
            "%d/%m/%Y",     # 10/8/2026
            "%Y%m%d",       # 20260810
            "%d-%m-%Y",     # 10-08-2026
            "%m-%d-%Y",     # 08-10-2026
            "%d.%m.%Y",     # 10.08.2026
            "%m.%d.%Y",     # 08.10.2026
        ):
            try:
                return datetime.strptime(str(value).strip(), fmt).date()
            except (ValueError, TypeError):
                continue

        # ✅ المحاولة الأخيرة: استخدام Pandas (يتعامل مع صيغ متعددة)
        try:
            result = pd.to_datetime(value, errors='coerce')
            if pd.isna(result):
                return None
            return result.date()
        except:
            return None

    @staticmethod
    def clean_decimal(value):
        """
        تحويل القيمة إلى Decimal مع دعم الفواصل الآلاف
        ✅ ترجع Decimal بدلاً من float
        ✅ تدعم الألف العربية والفواصل
        ✅ تدعم العلامة العشرية العربية
        ✅ تم إزالة الحد الأقصى للقيمة
        """
        if pd.isna(value):
            return Decimal('0.00')

        if value in ("", None):
            return Decimal('0.00')

        try:
            cleaned = str(value).strip()
            cleaned = cleaned.replace("%", "")
            cleaned = cleaned.replace(" ", "")
            cleaned = cleaned.replace(",", "")
            cleaned = cleaned.replace("٬", "")
            cleaned = cleaned.replace("٫", ".")
            
            decimal_value = Decimal(cleaned)
            decimal_value = decimal_value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
            return decimal_value
            
        except (ValueError, TypeError, InvalidOperation):
            return Decimal('0.00')

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

        if Decimal('0') < value <= Decimal('1'):
            value *= Decimal('100')

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
        """
        تنظيف وتوحيد اسم الشركة للمطابقة.
        """
        normalized = ImportHelpers.normalize_text(value)

        # توحيد الياء والألف المقصورة في أسماء الجهات
        normalized = normalized.replace("ى", "ي")

        return normalized

    @staticmethod
    def package_lookup_key(
        package_code,
        package_name,
    ):
        """
        بناء مفتاح فريد للبحث عن الباكدجات
        """
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
        """
        الحصول على أو إنشاء تخصص جديد
        """
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
            return Decimal('0.00')
        
        try:
            if isinstance(value, str):
                # إزالة الفواصل الآلاف
                cleaned = value.replace(",", "").strip()
                return Decimal(cleaned).quantize(Decimal('0.01'))
            return Decimal(str(value)).quantize(Decimal('0.01'))
        except Exception:
            return Decimal('0.00')

    # ============================================================
    # ✅ ✅ ✅ NEW: دالة توحيد التصنيفات
    # ============================================================
    @staticmethod
    def normalize_category(category):
        """
        توحيد التصنيفات لتطابق التصنيفات في جدول Procedure
        """
        if not category:
            return category
        
        # ✅ تنظيف النص
        cleaned = str(category).strip()
        
        # ✅ خريطة التحويل
        mapping = {
            'صغرى': 'صغـــرى',
            'كبرى': 'كــبرى',
            'طابع خاص': 'ذات طابع خاص',
            'صغرى ': 'صغـــرى',
            'كبرى ': 'كــبرى',
            'طابع خاص ': 'ذات طابع خاص',
            'صغرى\t': 'صغـــرى',
            'كبرى\t': 'كــبرى',
            'طابع خاص\t': 'ذات طابع خاص',
        }
        
        # ✅ التحويل
        return mapping.get(cleaned, cleaned)

    # ============================================================
    # ✅ ✅ ✅ NEW: دالة التحقق من وجود التصنيف
    # ============================================================
    @staticmethod
    def validate_category_exists(category):
        """
        التحقق من وجود التصنيف في جدول Procedure
        """
        if not category:
            return True
        
        try:
            from contracts.models import Procedure
            # ✅ توحيد التصنيف أولاً
            normalized = ImportHelpers.normalize_category(category)
            return Procedure.objects.filter(classification=normalized).exists()
        except Exception:
            return False

    # ============================================================
    # ✅ ✅ ✅ NEW: دالة الحصول على التصنيف الموحد من Procedure
    # ============================================================
    @staticmethod
    def get_procedure_category(procedure):
        """
        الحصول على التصنيف الموحد من كائن Procedure
        """
        if not procedure:
            return None
        
        if hasattr(procedure, 'classification'):
            return ImportHelpers.normalize_category(procedure.classification)
        
        return None