# imports/services/company_discount_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from contracts.models import CompanyDiscountProfile, CompanyDiscount
from imports.utils.import_helpers import ImportHelpers
from imports.services.google_sheets_service import GoogleSheetsService

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
        {"name": "اتعاب الاطباء", "discount_col": 13, "details_col": None, "net_price_col": None, "is_percentage": True},
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
    def extract_details_from_group(group, details_col, price_col, discount_col=None):
        """
        استخراج التفاصيل من مجموعة الصفوف التابعة لنفس الشركة
        """
        lines = []
        
        # ✅ تخطي الصف الأول (الرئيسي)
        for row in group[1:]:
            # ✅ استخراج التفاصيل من العمود المحدد
            detail = ""
            if details_col is not None and len(row) > details_col:
                val = row.get(details_col, "")
                if pd.notna(val) and val:
                    detail = ImportHelpers.normalize_text(str(val))
            
            # ✅ استخراج السعر من العمود المحدد
            price = ""
            if price_col is not None and len(row) > price_col:
                val = row.get(price_col, "")
                if pd.notna(val) and val:
                    price = ImportHelpers.normalize_text(str(val))
            
            # ✅ لو في تفاصيل، نضيفها
            if detail:
                line = detail
                if price:
                    line += f" : {price}"
                lines.append(line)
        
        return "\n".join(lines)

    @staticmethod
    def extract_doctors_fees(group):
        """
        استخراج جدول أتعاب الأطباء بالكامل
        """

        lines = []

        for row in group[1:]:

            level = ImportHelpers.normalize_text(row.get(14, ""))

            if not level:
                continue

            surgeon = ImportHelpers.normalize_text(row.get(15, ""))
            anesthesia = ImportHelpers.normalize_text(row.get(16, ""))
            assistant = ImportHelpers.normalize_text(row.get(17, ""))
            total = ImportHelpers.normalize_text(row.get(18, ""))

            lines.append(level)

            if surgeon:
                lines.append(f"جراح : {surgeon}")

            if anesthesia:
                lines.append(f"تخدير : {anesthesia}")

            if assistant:
                lines.append(f"مساعد : {assistant}")

            if total:
                lines.append(f"الإجمالي : {total}")

            lines.append("")

        return "\n".join(lines).strip()

    @staticmethod
    @transaction.atomic
    def import_data(dataframe, company=None):

        start_time = time.perf_counter()
        print("⏳ Starting Company Discounts import from Sheet 4...")

        result = {
            "processed": 0,
            "created_profiles": 0,
            "updated_profiles": 0,
            "created_discounts": 0,
            "existing_profiles": 0,
            "deleted_profiles": 0,
            "deleted_discounts": 0,
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

        # ✅ تتبع البيانات الموجودة في الشيت
        sheet_profiles = set()
        sheet_discounts = set()

        # ============================================================
        # ✅ تحميل Drive Smart Chips من Sheet 4
        # ============================================================
        print("📎 Loading Drive Smart Chips from Sheet 4...")

        drive_links = GoogleSheetsService.get_drive_links(
            sheet_name="4",
            start_row=1,
            end_row=20,
            end_column="AT",
        )

        print(f"✅ Loaded {len(drive_links)} Drive links")

        # ============================================================
        # ✅ ربط Smart Chips بالشركة + الفئة المالية
        # ============================================================

        spreadsheet = GoogleSheetsService.get_spreadsheet()
        worksheet = spreadsheet.worksheet("4")
        raw_sheet_data = worksheet.get_all_values()

        drive_links_by_company = {}

        for (row_index, column_index), drive_data in drive_links.items():

            if column_index != 45:
                continue

            if row_index >= len(raw_sheet_data):
                continue

            raw_row = raw_sheet_data[row_index]

            raw_company = (
                raw_row[0].strip()
                if len(raw_row) > 0
                else ""
            )

            raw_financial_code = (
                raw_row[2].strip()
                if len(raw_row) > 2
                else ""
            )

            if not raw_company:
                continue

            key = (
                ImportHelpers.normalize_text(raw_company),
                ImportHelpers.normalize_text(raw_financial_code),
            )

            drive_links_by_company[key] = drive_data

        print(
            f"✅ Drive links mapped to companies: "
            f"{len(drive_links_by_company)}"
        )

        # ============================================================
        # ✅ تجهيز الصفوف
        # ============================================================
        rows = dataframe.to_dict("records")

        # ============================================================
        # ✅ Loop - تجميع البيانات في Groups
        # ============================================================
        print("⏳ Processing rows...")

        groups = []
        current_group = None

        for row in rows:
            company_name = ImportHelpers.normalize_text(row.get(0, ""))

            # بداية شركة جديدة
            if company_name:
                current_group = [row]
                groups.append(current_group)

            # صف تابع لنفس الشركة
            elif current_group:
                current_group.append(row)

        # ✅ فلترة الشركات إذا تم تحديد company
        if company:
            normalized_company = ImportHelpers.normalize_text(company)
            groups = [
                g for g in groups
                if ImportHelpers.normalize_text(g[0].get(0, "")) == normalized_company
            ]
            print(f"   ✅ Filtered to {len(groups)} companies matching: {company}")

        total_rows = len(groups)
        processed = 0

        for index, group in enumerate(groups, start=1):

            row = group[0]

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

            # ============================================================
            # ✅ المرفقات - Drive Smart Chip من Sheet 4
            # ============================================================

            drive_key = (
                company_name,
                financial_code,
            )

            drive_data = drive_links_by_company.get(drive_key)

            if drive_data:
                operating_pdf = ImportHelpers.normalize_text(
                    drive_data.get("url", "")
                )

                print(
                    f"📎 {company_name}: "
                    f"{drive_data.get('name', '')}"
                )
                print(f"🔗 {operating_pdf}")

            else:
                # لو مفيش Smart Chip للشركة
                operating_pdf = ""

            operating_pdf = CompanyDiscountImportService.truncate_text(
                operating_pdf,
                500
            )

            processed += 1
            result["processed"] = processed

            # ✅ البحث في Cache
            profile_key = (company_name, financial_code)
            sheet_profiles.add(profile_key)

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

            # ✅ تحديد المفتاح المناسب للـ Cache
            profile_cache_id = profile.id if profile.id else profile_key

            # ==========================================
            # ✅ تجميع الخصومات - القسم الداخلي
            # ==========================================
            order = 1

            for item in CompanyDiscountImportService.INTERNAL_ITEMS:
                discount = CompanyDiscountImportService.get_discount_value(row, item["discount_col"], item["is_percentage"])
                
                # ✅ استخراج التفاصيل الأساسية من الصف الرئيسي
                base_details = CompanyDiscountImportService.get_details(row, item["details_col"])
                net_price = CompanyDiscountImportService.get_net_price(row, item["net_price_col"])
                
                # ✅ استخراج التفاصيل الإضافية من الصفوف التابعة
                extra_details = ""

                if item["name"] == "اتعاب الاطباء":
                    extra_details = CompanyDiscountImportService.extract_doctors_fees(group)
                elif (
                    item["details_col"] is not None
                    and item["net_price_col"] is not None
                ):
                    extra_details = CompanyDiscountImportService.extract_details_from_group(
                        group,
                        item["details_col"],
                        item["net_price_col"],
                        item["discount_col"],
                    )
                
                # ✅ دمج التفاصيل الأساسية والإضافية
                if base_details and extra_details:
                    details = base_details + "\n" + extra_details
                elif extra_details:
                    details = extra_details
                else:
                    details = base_details

                # ✅ البحث في Cache
                discount_key = (profile_cache_id, "داخلي", item["name"])
                
                # ✅ تتبع الخصومات في الشيت
                sheet_discounts.add(
                    (
                        company_name,
                        financial_code,
                        "داخلي",
                        item["name"],
                    )
                )

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
                    discount_obj = CompanyDiscount(
                        profile=profile,
                        section="داخلي",
                        item_name=item["name"],
                        discount=discount,
                        details=details,
                        net_price=net_price,
                        display_order=order,
                        is_active=True,
                    )
                    discounts_to_create.append(discount_obj)
                    result["created_discounts"] += 1
                    discounts_cache[discount_key] = discount_obj

                order += 1

            # ✅ الاستثناءات الداخلية
            internal_exception = ImportHelpers.normalize_text(row.get(28, ""))
            internal_exception = CompanyDiscountImportService.truncate_text(internal_exception, 1000)

            discount_key = (profile_cache_id, "داخلي", "الاستثناءات")
            
            # ✅ تتبع الاستثناءات الداخلية في الشيت
            sheet_discounts.add(
                (
                    company_name,
                    financial_code,
                    "داخلي",
                    "الاستثناءات",
                )
            )

            if discount_key in discounts_cache:
                existing_discount = discounts_cache[discount_key]
                if existing_discount.details != internal_exception:
                    existing_discount.details = internal_exception
                    discounts_to_update.append(existing_discount)
            else:
                discount_obj = CompanyDiscount(
                    profile=profile,
                    section="داخلي",
                    item_name="الاستثناءات",
                    details=internal_exception,
                    display_order=100,
                    is_active=True,
                )
                discounts_to_create.append(discount_obj)
                result["created_discounts"] += 1
                discounts_cache[discount_key] = discount_obj

            # ==========================================
            # ✅ القسم الخارجي
            # ==========================================
            order = 1

            for item in CompanyDiscountImportService.EXTERNAL_ITEMS:
                discount = CompanyDiscountImportService.get_discount_value(row, item["discount_col"], item["is_percentage"])
                base_details = CompanyDiscountImportService.get_details(row, item["details_col"])
                net_price = CompanyDiscountImportService.get_net_price(row, item["net_price_col"])
                
                # ✅ استخراج التفاصيل الإضافية من الصفوف التابعة
                extra_details = ""
                if item["details_col"] is not None and item["net_price_col"] is not None:
                    extra_details = CompanyDiscountImportService.extract_details_from_group(
                        group,
                        item["details_col"],
                        item["net_price_col"],
                        item["discount_col"]
                    )
                
                # ✅ دمج التفاصيل
                if base_details and extra_details:
                    details = base_details + "\n" + extra_details
                elif extra_details:
                    details = extra_details
                else:
                    details = base_details

                discount_key = (profile_cache_id, "خارجي", item["name"])
                
                # ✅ تتبع الخصومات الخارجية في الشيت
                sheet_discounts.add(
                    (
                        company_name,
                        financial_code,
                        "خارجي",
                        item["name"],
                    )
                )

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
                    discount_obj = CompanyDiscount(
                        profile=profile,
                        section="خارجي",
                        item_name=item["name"],
                        discount=discount,
                        details=details,
                        net_price=net_price,
                        display_order=order,
                        is_active=True,
                    )
                    discounts_to_create.append(discount_obj)
                    result["created_discounts"] += 1
                    discounts_cache[discount_key] = discount_obj

                order += 1

            # ✅ الاستثناءات الخارجية
            external_exception = ImportHelpers.normalize_text(row.get(44, ""))
            external_exception = CompanyDiscountImportService.truncate_text(external_exception, 1000)

            discount_key = (profile_cache_id, "خارجي", "الاستثناءات")
            
            # ✅ تتبع الاستثناءات الخارجية في الشيت
            sheet_discounts.add(
                (
                    company_name,
                    financial_code,
                    "خارجي",
                    "الاستثناءات",
                )
            )

            if discount_key in discounts_cache:
                existing_discount = discounts_cache[discount_key]
                if existing_discount.details != external_exception:
                    existing_discount.details = external_exception
                    discounts_to_update.append(existing_discount)
            else:
                discount_obj = CompanyDiscount(
                    profile=profile,
                    section="خارجي",
                    item_name="الاستثناءات",
                    details=external_exception,
                    display_order=100,
                    is_active=True,
                )
                discounts_to_create.append(discount_obj)
                result["created_discounts"] += 1
                discounts_cache[discount_key] = discount_obj

            if processed % 10 == 0:
                print(f"   📊 Processed {processed}/{total_rows} companies...")

        print(f"   ✅ Processed {processed}/{total_rows} companies")

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

        # ============================================================
        # ✅ Reload Profiles بعد الـ bulk_create
        # ============================================================
        profiles_cache = {}
        for profile in CompanyDiscountProfile.objects.all():
            key = (
                ImportHelpers.normalize_text(profile.company_name),
                ImportHelpers.normalize_text(profile.financial_category),
            )
            profiles_cache[key] = profile

        # ============================================================
        # ✅ Reload Discounts
        # ============================================================
        discounts_cache = {}
        for discount in CompanyDiscount.objects.select_related("profile"):
            profile_key = (
                ImportHelpers.normalize_text(discount.profile.company_name),
                ImportHelpers.normalize_text(discount.profile.financial_category),
                discount.section,
                discount.item_name,
            )
            discounts_cache[profile_key] = discount

        # ============================================================
        # ✅ Delete Discounts not found in Sheet
        # ============================================================
        discounts_to_delete = []

        for key, discount in discounts_cache.items():
            if key not in sheet_discounts:
                discounts_to_delete.append(discount.id)

        if discounts_to_delete:
            deleted, _ = CompanyDiscount.objects.filter(
                id__in=discounts_to_delete
            ).delete()

            result["deleted_discounts"] = deleted
            print(f"🗑️ Deleted {deleted} discounts")

        # ============================================================
        # ✅ Delete Profiles not found in Sheet
        # ============================================================
        profiles_to_delete = []

        for key, profile in profiles_cache.items():
            if key not in sheet_profiles:
                profiles_to_delete.append(profile.id)

        if profiles_to_delete:
            deleted, _ = CompanyDiscountProfile.objects.filter(
                id__in=profiles_to_delete
            ).delete()

            result["deleted_profiles"] = deleted
            print(f"🗑️ Deleted {deleted} profiles")

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result