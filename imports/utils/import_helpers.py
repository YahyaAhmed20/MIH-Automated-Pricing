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