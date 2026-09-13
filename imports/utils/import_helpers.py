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
    def arabic_search_variants(value):
        """
        توحيد النص العربي لأغراض البحث.

        لا يتم تغيير القيمة الأصلية المخزنة في قاعدة البيانات.

        أمثلة:
            أحمد   -> احمد
            إيمان  -> ايمان
            آمال   -> امال
            مدرسة  -> مدرسه
            مصطفى  -> مصطفي
        """

        if value is None or pd.isna(value):
            return [""]

        import unicodedata

        value = str(value)

        # Unicode normalization
        value = unicodedata.normalize("NFKC", value)

        # إزالة التشكيل
        value = "".join(
            char
            for char in value
            if not unicodedata.combining(char)
        )

        # توحيد المسافات
        value = (
            value
            .replace("\r", " ")
            .replace("\n", " ")
            .replace("\t", " ")
        )

        value = " ".join(value.split())

        # إزالة التطويل
        value = value.replace("ـ", "")

        # توحيد الألف والهمزات
        value = (
            value
            .replace("أ", "ا")
            .replace("إ", "ا")
            .replace("آ", "ا")
            .replace("ٱ", "ا")
        )

        # توحيد التاء المربوطة والهاء
        value = value.replace("ة", "ه")

        # توحيد الألف المقصورة والياء
        value = value.replace("ى", "ي")

        # الهمزة على الياء
        value = value.replace("ئ", "ي")

        # الهمزة على الواو
        value = value.replace("ؤ", "و")

        value = value.strip()

        return [value]

    @staticmethod
    def clean_date(value):
        """
        تنظيف قيمة التاريخ وتحويلها إلى date أو None.

        يدعم:
        - YYYY/MM/DD
        - YYYY-MM-DD
        - DD/MM/YYYY
        - DD-MM-YYYY
        - MM/DD/YYYY
        - YYYYMMDD
        - Excel serial dates
        - datetime / pandas Timestamp

        ملاحظة:
        يتم استخدام parsing صريح قبل Pandas لمنع اختلاف تفسير
        التواريخ بين التشغيلات.
        """

        if pd.isna(value):
            return None

        if value in ("", None):
            return None

        # ------------------------------------------------------------
        # datetime / pandas Timestamp
        # ------------------------------------------------------------
        if isinstance(value, (datetime, pd.Timestamp)):
            return value.date()

        # ------------------------------------------------------------
        # Excel serial date / numeric timestamp
        # ------------------------------------------------------------
        if isinstance(value, (int, float)):
            if value == 0:
                return None

            try:
                return pd.to_datetime(
                    value,
                    unit="D",
                    origin="1899-12-30",
                ).date()
            except (ValueError, TypeError, OverflowError):
                return None

        # ------------------------------------------------------------
        # String
        # ------------------------------------------------------------
        if isinstance(value, str):
            value = value.strip()

            if value in ("", "0", "NULL", "null", "None"):
                return None

            # ترتيب مهم:
            # نضع DD/MM/YYYY قبل MM/DD/YYYY
            # لأن بيانات المستشفى غالبًا مصرية.
            formats = (
                "%Y/%m/%d",
                "%Y-%m-%d",
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%d.%m.%Y",
                "%m/%d/%Y",
                "%m-%d-%Y",
                "%m.%d.%Y",
                "%Y%m%d",

                # في حالة وجود وقت
                "%Y/%m/%d %H:%M",
                "%Y-%m-%d %H:%M",
                "%d/%m/%Y %H:%M",
                "%d-%m-%Y %H:%M",
                "%m/%d/%Y %H:%M",
                "%m-%d-%Y %H:%M",

                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
                "%d-%m-%Y %H:%M:%S",
                "%m/%d/%Y %H:%M:%S",
                "%m-%d-%Y %H:%M:%S",
            )

            for fmt in formats:
                try:
                    return datetime.strptime(
                        value,
                        fmt,
                    ).date()
                except (ValueError, TypeError):
                    continue

        # ------------------------------------------------------------
        # Final fallback
        # ------------------------------------------------------------
        try:
            result = pd.to_datetime(
                value,
                errors="coerce",
                dayfirst=True,
            )

            if pd.isna(result):
                return None

            return result.date()

        except (ValueError, TypeError, OverflowError):
            return None

    @staticmethod
    def clean_datetime(value):
        """
        تنظيف التاريخ والوقت وتحويله إلى datetime timezone-aware أو None.

        يدعم صيغ Sheet 11 مثل:
        26/01/2025 17:17
        01/01/2025 18:01
        """

        if pd.isna(value):
            return None

        if value in ("", None):
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value or value in ["0", "NULL", "null", "None"]:
                return None

        # Excel / pandas datetime
        if isinstance(value, pd.Timestamp):
            result = value.to_pydatetime()

        elif isinstance(value, datetime):
            result = value

        # Excel serial number
        elif isinstance(value, (int, float)):
            if value == 0:
                return None

            try:
                result = pd.to_datetime(
                    value,
                    unit="d",
                    origin="1899-12-30",
                ).to_pydatetime()
            except Exception:
                return None

        else:
            # Sheet 11 datetime formats
            result = None

            for fmt in (
                "%d/%m/%Y %H:%M",
                "%d/%m/%Y %H:%M:%S",
                "%Y/%m/%d %H:%M",
                "%Y/%m/%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%m/%d/%Y %H:%M",
                "%m/%d/%Y %H:%M:%S",
            ):
                try:
                    result = datetime.strptime(
                        str(value).strip(),
                        fmt,
                    )
                    break
                except (ValueError, TypeError):
                    continue

            # Fallback
            if result is None:
                try:
                    parsed = pd.to_datetime(
                        value,
                        errors="coerce",
                        dayfirst=True,
                    )

                    if pd.isna(parsed):
                        return None

                    result = parsed.to_pydatetime()

                except Exception:
                    return None

        # ============================================================
        # Convert naive datetime -> timezone-aware
        # ============================================================
        from django.utils import timezone

        if timezone.is_naive(result):
            result = timezone.make_aware(
                result,
                timezone.get_current_timezone(),
            )

        return result

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
        بناء مفتاح موحد وآمن لمطابقة أسماء الشركات.

        الهدف:
        - توحيد اختلافات Unicode.
        - توحيد الهمزات والألف.
        - توحيد الياء والألف المقصورة.
        - إزالة التشكيل والتطويل.
        - تنظيف المسافات والرموز.
        - التعامل مع صيغ الكتابة الشائعة مثل:
            الشركة المصرية للاتصالات
            المصرية للاتصالات

        ملاحظة:
        هذه الدالة تستخدم للمطابقة فقط.
        لا تغيّر الاسم الأصلي المخزن في قاعدة البيانات.
        """
        if value is None or pd.isna(value):
            return ""

        normalized = str(value)

        # ============================================================
        # 1) Unicode normalization
        # ============================================================
        import unicodedata

        normalized = unicodedata.normalize("NFKC", normalized)

        # ============================================================
        # 2) إزالة التشكيل والعلامات الصوتية العربية
        # ============================================================
        normalized = "".join(
            char
            for char in normalized
            if not unicodedata.combining(char)
        )

        # ============================================================
        # 3) توحيد المسافات والأسطر
        # ============================================================
        normalized = (
            normalized
            .replace("\r", " ")
            .replace("\n", " ")
            .replace("\t", " ")
        )

        normalized = " ".join(normalized.split())

        # ============================================================
        # 4) إزالة التطويل العربي
        # ============================================================
        normalized = normalized.replace("ـ", "")

        # ============================================================
        # 5 + 6) توحيد الحروف العربية الشائعة في أسماء الشركات
        # ============================================================
        normalized = (
            normalized
            # الألف والهمزات
            .replace("أ", "ا")
            .replace("إ", "ا")
            .replace("آ", "ا")
            .replace("ٱ", "ا")

            # الياء والألف المقصورة
            .replace("ى", "ي")
            .replace("ئ", "ي")

            # التاء المربوطة والهاء
            .replace("ة", "ه")
        )

        # ============================================================
        # 7) توحيد الواو مع الهمزة
        # ============================================================
        normalized = normalized.replace("ؤ", "و")

        # ============================================================
        # 8) إزالة علامات الترقيم والرموز غير المهمة
        #
        # نُبقي الحروف والأرقام والمسافات.
        # ============================================================
        normalized = "".join(
            char
            for char in normalized
            if char.isalnum() or char.isspace()
        )

        # ============================================================
        # 9) توحيد المسافات مرة أخيرة
        # ============================================================
        normalized = " ".join(normalized.split())

        # ============================================================
        # 10) إزالة Prefix عام من اسم الشركة
        #
        # مثال:
        # الشركة المصرية للاتصالات
        # المصرية للاتصالات
        #
        # يصبحان:
        # المصرية للاتصالات
        #
        # مهم:
        # لا نغيّر الاسم الأصلي، فقط مفتاح المقارنة.
        # ============================================================
        generic_prefixes = (
            "الشركه ",
            "شركه ",
        )

        for prefix in generic_prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break

        return normalized.strip()

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
    
    @staticmethod
    def clean_date_dmy(value):
        """
        تنظيف تاريخ Sheet 7 بصيغة DD/MM/YYYY
        """
        if pd.isna(value):
            return None

        if value in ("", None):
            return None

        if isinstance(value, str):
            value = value.strip()

            if not value or value in ["0", "NULL", "null", "None"]:
                return None

            for fmt in (
                "%d/%m/%Y",
                "%d-%m-%Y",
                "%d.%m.%Y",
                "%Y/%m/%d",
                "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(value, fmt).date()
                except (ValueError, TypeError):
                    continue

        if isinstance(value, (int, float)):
            if value == 0:
                return None

            try:
                return pd.to_datetime(value, unit="d").date()
            except:
                return None

        return None

    @staticmethod
    def clean_date_mdy(value):
        """
        تنظيف تاريخ Sheet 6 بصيغة MM/DD/YYYY
        """
        if pd.isna(value):
            return None

        if value in ("", None):
            return None

        if isinstance(value, (datetime, pd.Timestamp)):
            return value.date()

        if isinstance(value, str):
            value = value.strip()

            if not value or value in ["0", "NULL", "null", "None"]:
                return None

            for fmt in (
                "%m/%d/%Y",
                "%m-%d-%Y",
                "%m.%d.%Y",
                "%Y/%m/%d",
                "%Y-%m-%d",
            ):
                try:
                    return datetime.strptime(
                        value,
                        fmt,
                    ).date()
                except (ValueError, TypeError):
                    continue

        if isinstance(value, (int, float)):
            if value == 0:
                return None

            try:
                return pd.to_datetime(
                    value,
                    unit="D",
                    origin="1899-12-30",
                ).date()
            except Exception:
                return None

        return None

    # ============================================================
    # Header Utilities
    # ============================================================

    @staticmethod
    def normalize_header(value):
        """
        توحيد أسماء الأعمدة للمطابقة.

        لا نغيّر اسم العمود الأصلي في الـ DataFrame،
        وإنما نستخدم القيمة الموحدة للمقارنة فقط.
        """
        if value is None or pd.isna(value):
            return ""

        value = str(value)

        # إزالة المسافات والأسطر الزائدة
        value = " ".join(
            value
            .replace("\r", " ")
            .replace("\n", " ")
            .split()
        )

        # توحيد بعض الاختلافات العربية الشائعة
        value = (
            value
            .replace("أ", "ا")
            .replace("إ", "ا")
            .replace("آ", "ا")
            
        )

        return value.strip()

    @staticmethod
    def make_unique_headers(headers):
        """
        جعل أسماء الأعمدة فريدة مع الحفاظ على أسماء الـ Headers الأصلية.

        مثال:
            ["اسم المريض", "", "", ""]
        
        تصبح:
            ["اسم المريض", "unnamed", "unnamed_2", "unnamed_3"]
        """

        result = []
        counters = {}

        for header in headers:

            # تنظيف الـ Header
            normalized = ImportHelpers.normalize_header(header)

            # Header فارغ
            if not normalized:
                base_name = "unnamed"
            else:
                base_name = str(header)

            # أول ظهور
            if base_name not in counters:
                counters[base_name] = 1
                result.append(base_name)
                continue

            # ظهور مكرر
            counters[base_name] += 1
            result.append(
                f"{base_name}_{counters[base_name]}"
            )

        return result

    @staticmethod
    def build_header_map(dataframe):
        """
        بناء خريطة للـ Headers بعد التطبيع.

        Returns:
            {
                normalized_header: actual_dataframe_column
            }

        Raises:
            ValueError إذا وُجد Header مكرر بعد التطبيع.
        """
        header_map = {}
        duplicates = {}

        for column in dataframe.columns:
            actual_column = column
            normalized_column = ImportHelpers.normalize_header(
                actual_column
            )

            if not normalized_column:
                continue

            if normalized_column in header_map:
                duplicates.setdefault(
                    normalized_column,
                    [
                        header_map[normalized_column]
                    ]
                ).append(actual_column)
                continue

            header_map[normalized_column] = actual_column

        if duplicates:
            duplicate_details = ", ".join(
                f"'{normalized}': {columns}"
                for normalized, columns in duplicates.items()
            )

            raise ValueError(
                "Duplicate sheet headers detected after normalization: "
                f"{duplicate_details}"
            )

        return header_map

    @staticmethod
    def validate_required_columns(
        dataframe,
        required_columns,
    ):
        """
        التأكد من وجود كل الأعمدة المطلوبة في الشيت.

        required_columns:
            أسماء Headers كما تظهر في الـ Sheet.

        Returns:
            header_map
        """
        header_map = ImportHelpers.build_header_map(
            dataframe
        )

        normalized_required = {
            ImportHelpers.normalize_header(column): column
            for column in required_columns
        }

        missing_columns = [
            original_name
            for normalized_name, original_name
            in normalized_required.items()
            if normalized_name not in header_map
        ]

        if missing_columns:
            raise ValueError(
                "Missing required sheet columns: "
                + ", ".join(missing_columns)
            )

        return header_map
    
    
    @staticmethod
    def get_mapped_value(
        row,
        header_map,
        field_name,
        column_mapping,
        default="",
    ):
        """
        الحصول على قيمة من الصف اعتمادًا على اسم الحقل
        وليس ترتيب العمود.

        field_name:
            اسم الحقل في الـ Model / Mapping.

        column_mapping:
            خريطة الحقول إلى أسماء أعمدة الـ Sheet.

        header_map:
            الخريطة التي تم بناؤها من Headers الـ DataFrame.
        """
        column_name = column_mapping.get(field_name)

        if not column_name:
            return default

        normalized_column = ImportHelpers.normalize_header(
            column_name
        )

        actual_column = header_map.get(
            normalized_column
        )

        if actual_column is None:
            return default

        value = row.get(
            actual_column,
            default,
        )

        if pd.isna(value):
            return default

        return value