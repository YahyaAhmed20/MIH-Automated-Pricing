# imports/services/company_discount_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from contracts.models import CompanyDiscountProfile, CompanyDiscount
from imports.utils.import_helpers import ImportHelpers


class CompanyDiscountImportService:

    @staticmethod
    def truncate_text(value, max_length=255):
        """تقليص النص إذا تجاوز الحد الأقصى"""
        if not value:
            return value
        cleaned = ImportHelpers.normalize_text(value)
        if len(cleaned) > max_length:
            print(f"⚠️ تم تقليص نص طويل من {len(cleaned)} إلى {max_length} حرف")
            return cleaned[:max_length]
        return cleaned

    @staticmethod
    def format_price(value):
        """تنسيق السعر"""
        if value is None:
            return "-"
        try:
            if isinstance(value, Decimal):
                return f"{value:,.0f}"
            return f"{float(value):,.0f}"
        except:
            return str(value)

    INTERNAL_ITEMS = [
        {"name": "البنود الخاضعه للخصم", "discount_col": 4, "details_col": None, "net_price_col": None, "is_percentage": True},
        {"name": "الاقامه", "discount_col": 6, "details_col": 7, "net_price_col": 8, "is_percentage": True},
        {"name": "المعمل", "discount_col": 9, "details_col": 10, "net_price_col": None, "is_percentage": True},
        {"name": "الاشعه", "discount_col": 11, "details_col": 12, "net_price_col": None, "is_percentage": True},
        {"name": "اتعاب الاطباء", "discount_col": 13, "details_col": 14, "net_price_col": None, "is_percentage": True},
        {"name": "الاشراف الطبي", "discount_col": 19, "details_col": 20, "net_price_col": None, "is_percentage": True},
        {"name": "فتح غرفة العمليات", "discount_col": 21, "details_col": 22, "net_price_col": 23, "is_percentage": True},
        {"name": "اجهزة العمليات", "discount_col": 24, "details_col": 25, "net_price_col": None, "is_percentage": True},
        {"name": "خدمات الرعاية المركزة", "discount_col": 26, "details_col": 27, "net_price_col": None, "is_percentage": True},
    ]

    EXTERNAL_ITEMS = [
        {"name": "البنود الخاضعه للخصم", "discount_col": 30, "details_col": None, "net_price_col": None, "is_percentage": True},
        {"name": "كشف العيادة الخارجية", "discount_col": 32, "details_col": 33, "net_price_col": None, "is_percentage": False},
        {"name": "خدمات القسم الخارجي", "discount_col": 34, "details_col": 35, "net_price_col": None, "is_percentage": True},
        {"name": "كشف الطوارئ", "discount_col": 36, "details_col": 37, "net_price_col": None, "is_percentage": False},
        {"name": "خدمات الطوارئ", "discount_col": 38, "details_col": 39, "net_price_col": None, "is_percentage": True},
        {"name": "المعمل", "discount_col": 40, "details_col": 41, "net_price_col": None, "is_percentage": True},
        {"name": "الاشعه", "discount_col": 42, "details_col": 43, "net_price_col": None, "is_percentage": True},
    ]

    @staticmethod
    def get_discount_value(row, col, is_percentage):
        """استخراج قيمة الخصم من dict"""
        if col is None:
            return ""
        raw = row.get(col, "")
        if raw is None or raw == "":
            return ""
        if is_percentage:
            return ImportHelpers.clean_discount(raw)
        return ImportHelpers.normalize_text(raw)

    @staticmethod
    def get_details(row, col):
        """استخراج التفاصيل من dict"""
        if col is None:
            return ""
        raw = row.get(col, "")
        if raw is None or raw == "":
            return ""
        return ImportHelpers.normalize_text(str(raw))

    @staticmethod
    def get_net_price(row, col):
        """استخراج السعر الصافي من dict"""
        if col is None:
            return None
        raw = row.get(col, None)
        if raw is None or raw == "":
            return None
        return ImportHelpers.clean_decimal(raw)

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Company Discounts import from Sheet 4...")

        result = {
            "processed": 0,
            "created_profiles": 0,
            "updated_profiles": 0,
            "created_discounts": 0,
            "existing_profiles": 0,
        }

        # ============================================================
        # ✅ Cache للـ Profiles
        # ============================================================
        print("⏳ Loading existing profiles...")
        profiles_cache = {}
        for p in CompanyDiscountProfile.objects.all():
            key = (
                ImportHelpers.normalize_text(p.company_name),
                ImportHelpers.normalize_text(p.financial_category),
            )
            profiles_cache[key] = p
        print(f"   ✅ {len(profiles_cache)} profiles loaded")

        # ============================================================
        # ✅ Cache للـ Discounts
        # ============================================================
        print("⏳ Loading existing discounts...")
        discounts_cache = {}
        for d in CompanyDiscount.objects.select_related('profile').all():
            key = (
                d.profile_id,
                d.section,
                d.item_name,
            )
            discounts_cache[key] = d
        print(f"   ✅ {len(discounts_cache)} discounts loaded")

        # ============================================================
        # ✅ قوائم التجميع
        # ============================================================
        profiles_to_create = []
        profiles_to_update = []
        discounts_to_create = []
        discounts_to_update = []

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ العمود 0: اسم الجهة
            company_name = ImportHelpers.normalize_text(row.get(0, ""))
            company_name = CompanyDiscountImportService.truncate_text(company_name, 255)

            if not company_name:
                continue

            # ✅ العمود 2: الفئة المالية
            financial_code = ImportHelpers.normalize_text(row.get(2, ""))
            financial_code = CompanyDiscountImportService.truncate_text(financial_code, 50)

            # ✅ العمود 1: نوع التعاقد
            contract_type = ImportHelpers.normalize_text(row.get(1, ""))
            contract_type = CompanyDiscountImportService.truncate_text(contract_type, 255)

            # ✅ العمود 3: قائمة الاسعار
            price_list = ImportHelpers.normalize_text(row.get(3, ""))
            price_list = CompanyDiscountImportService.truncate_text(price_list, 255)

            # ✅ العمود 6: المرفقات (PDF)
            operating_pdf = ImportHelpers.normalize_text(row.get(6, ""))
            operating_pdf = CompanyDiscountImportService.truncate_text(operating_pdf, 500)

            processed += 1
            result["processed"] = processed

            # ✅ البحث في Cache
            profile_key = (company_name, financial_code)
            profile = profiles_cache.get(profile_key)

            if profile:
                # ✅ تحديث البيانات
                changed = False
                if profile.contract_type != contract_type:
                    profile.contract_type = contract_type
                    changed = True
                if profile.price_list != price_list:
                    profile.price_list = price_list
                    changed = True
                if profile.operating_pdf != operating_pdf:
                    profile.operating_pdf = operating_pdf
                    changed = True
                if profile.is_active is not True:
                    profile.is_active = True
                    changed = True

                if changed:
                    profiles_to_update.append(profile)
                    result["updated_profiles"] += 1
                else:
                    result["existing_profiles"] += 1

            else:
                # ✅ إنشاء جديد
                profile = CompanyDiscountProfile(
                    company_name=company_name,
                    financial_category=financial_code,
                    contract_type=contract_type,
                    price_list=price_list,
                    operating_pdf=operating_pdf,
                    is_active=True,
                )
                profiles_to_create.append(profile)
                profiles_cache[profile_key] = profile
                result["created_profiles"] += 1

            # ==========================================
            # ✅ تجميع الخصومات - القسم الداخلي
            # ==========================================
            order = 1

            for item in CompanyDiscountImportService.INTERNAL_ITEMS:
                discount = CompanyDiscountImportService.get_discount_value(row, item["discount_col"], item["is_percentage"])
                details = CompanyDiscountImportService.get_details(row, item["details_col"])
                net_price = CompanyDiscountImportService.get_net_price(row, item["net_price_col"])

                discount_key = (profile.id if profile.id else -1, "داخلي", item["name"])

                if discount_key in discounts_cache:
                    existing_discount = discounts_cache[discount_key]
                    # تحديث
                    changed = False
                    if existing_discount.discount != discount:
                        existing_discount.discount = discount
                        changed = True
                    if existing_discount.details != details:
                        existing_discount.details = details
                        changed = True
                    if existing_discount.net_price != net_price:
                        existing_discount.net_price = net_price
                        changed = True
                    if changed:
                        discounts_to_update.append(existing_discount)
                else:
                    # إنشاء جديد
                    discounts_to_create.append(
                        CompanyDiscount(
                            profile=profile,
                            section="داخلي",
                            item_name=item["name"],
                            discount=discount,
                            details=details,
                            net_price=net_price,
                            display_order=order,
                            is_active=True,
                        )
                    )
                    result["created_discounts"] += 1

                order += 1

            # ✅ الاستثناءات الداخلية
            internal_exception = ImportHelpers.normalize_text(row.get(28, ""))
            internal_exception = CompanyDiscountImportService.truncate_text(internal_exception, 1000)

            discount_key = (profile.id if profile.id else -1, "داخلي", "الاستثناءات")
            if discount_key in discounts_cache:
                existing_discount = discounts_cache[discount_key]
                if existing_discount.details != internal_exception:
                    existing_discount.details = internal_exception
                    discounts_to_update.append(existing_discount)
            else:
                discounts_to_create.append(
                    CompanyDiscount(
                        profile=profile,
                        section="داخلي",
                        item_name="الاستثناءات",
                        details=internal_exception,
                        display_order=100,
                        is_active=True,
                    )
                )
                result["created_discounts"] += 1

            # ==========================================
            # ✅ القسم الخارجي
            # ==========================================
            order = 1

            for item in CompanyDiscountImportService.EXTERNAL_ITEMS:
                discount = CompanyDiscountImportService.get_discount_value(row, item["discount_col"], item["is_percentage"])
                details = CompanyDiscountImportService.get_details(row, item["details_col"])
                net_price = CompanyDiscountImportService.get_net_price(row, item["net_price_col"])

                discount_key = (profile.id if profile.id else -1, "خارجي", item["name"])

                if discount_key in discounts_cache:
                    existing_discount = discounts_cache[discount_key]
                    changed = False
                    if existing_discount.discount != discount:
                        existing_discount.discount = discount
                        changed = True
                    if existing_discount.details != details:
                        existing_discount.details = details
                        changed = True
                    if existing_discount.net_price != net_price:
                        existing_discount.net_price = net_price
                        changed = True
                    if changed:
                        discounts_to_update.append(existing_discount)
                else:
                    discounts_to_create.append(
                        CompanyDiscount(
                            profile=profile,
                            section="خارجي",
                            item_name=item["name"],
                            discount=discount,
                            details=details,
                            net_price=net_price,
                            display_order=order,
                            is_active=True,
                        )
                    )
                    result["created_discounts"] += 1

                order += 1

            # ✅ الاستثناءات الخارجية
            external_exception = ImportHelpers.normalize_text(row.get(44, ""))
            external_exception = CompanyDiscountImportService.truncate_text(external_exception, 1000)

            discount_key = (profile.id if profile.id else -1, "خارجي", "الاستثناءات")
            if discount_key in discounts_cache:
                existing_discount = discounts_cache[discount_key]
                if existing_discount.details != external_exception:
                    existing_discount.details = external_exception
                    discounts_to_update.append(existing_discount)
            else:
                discounts_to_create.append(
                    CompanyDiscount(
                        profile=profile,
                        section="خارجي",
                        item_name="الاستثناءات",
                        details=external_exception,
                        display_order=100,
                        is_active=True,
                    )
                )
                result["created_discounts"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(profiles_to_create)} profiles...")
        print(f"💾 Updating {len(profiles_to_update)} profiles...")
        print(f"💾 Creating {len(discounts_to_create)} discounts...")
        print(f"💾 Updating {len(discounts_to_update)} discounts...")

        if profiles_to_create:
            CompanyDiscountProfile.objects.bulk_create(profiles_to_create, batch_size=1000)

        if profiles_to_update:
            CompanyDiscountProfile.objects.bulk_update(
                profiles_to_update,
                fields=["contract_type", "price_list", "operating_pdf", "is_active"],
                batch_size=1000,
            )

        if discounts_to_create:
            CompanyDiscount.objects.bulk_create(discounts_to_create, batch_size=1000)

        if discounts_to_update:
            CompanyDiscount.objects.bulk_update(
                discounts_to_update,
                fields=["discount", "details", "net_price"],
                batch_size=1000,
            )

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result