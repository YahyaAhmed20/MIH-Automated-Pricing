# imports/services/company_exception_import_service.py

import pandas as pd
import time
from django.db import transaction
from pricing_requests.models import (
    CompanyExceptionProfile,
    CompanyExceptionItem,
)
from imports.utils.import_helpers import ImportHelpers


# ✅ تعريف أعمدة الشيت 9
COLUMN_MAP = [
    # (section, service_name, discount_col, details_col, price_col)
    # ------------------ داخلي ------------------
    ("داخلي", "الاشعه التداخليه", 3, 4, None),
    ("داخلي", "خدمات الكلي", 5, 6, 7),
    ("داخلي", "العلاج الاشعاعي", 8, 9, 10),
    ("داخلي", "علاج الالم", 11, 12, None),
    ("داخلي", "خدمات بنك الدم", 13, 14, 15),
    ("داخلي", "المرافق", None, 16, None),
    ("داخلي", "الاسعاف", 18, 19, None),
    
    # ------------------ خارجي ------------------
    ("خارجي", "خدمات الكلي", 21, 22, 23),
    ("خارجي", "العلاج الاشعاعي", 24, 25, 26),
    ("خارجي", "الاسعاف", 27, 28, None),
]


class CompanyExceptionImportService:

    @staticmethod
    def _get_discount_value(val):
        """استخراج قيمة الخصم وتحويلها لنسبة مئوية صحيحة"""
        if val is None or pd.isna(val):
            return None
        
        discount = ImportHelpers.clean_percentage(val)
        
        if discount is None:
            return None
        
        return round(discount)

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Company Exceptions import from Sheet 9...")

        result = {
            "processed": 0,
            "profiles": 0,
            "items": 0,
            "updated": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ Cache للـ Profiles
        # ============================================================
        print("⏳ Loading existing profiles...")
        profiles_cache = {}
        for profile in CompanyExceptionProfile.objects.all():
            key = ImportHelpers.normalize_text(profile.entity_name)
            profiles_cache[key] = profile
        print(f"   ✅ {len(profiles_cache)} profiles loaded")

        # ============================================================
        # ✅ Cache للـ Items (للتحديث بدلاً من الحذف)
        # ============================================================
        print("⏳ Loading existing items...")
        items_cache = {}
        for item in CompanyExceptionItem.objects.all():
            key = (
                item.profile_id,
                item.section,
                item.service_name,
                item.details,
            )
            items_cache[key] = item
        print(f"   ✅ {len(items_cache)} items loaded")

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        i = 0
        while i < len(dataframe):
            row = dataframe.iloc[i]

            # ✅ الجهة في العمود 0
            entity_name = None
            if len(row) > 0 and pd.notna(row.iloc[0]):
                entity_name = ImportHelpers.normalize_text(row.iloc[0])

            # ✅ إذا وجدنا جهة جديدة
            if entity_name:
                print(f"\n{'='*60}")
                print(f"🏢 معالجة: {entity_name}")

                # ✅ الفئة المالية (العمود 1)
                financial_category = ""
                if len(row) > 1 and pd.notna(row.iloc[1]):
                    financial_category = ImportHelpers.normalize_text(row.iloc[1])

                # ✅ قائمة الأسعار (العمود 2)
                price_list = ""
                if len(row) > 2 and pd.notna(row.iloc[2]):
                    price_list = ImportHelpers.normalize_text(row.iloc[2])

                # ✅ المرفقات (العمود 29)
                attachment = ""
                if len(row) > 29 and pd.notna(row.iloc[29]):
                    attachment = ImportHelpers.normalize_text(row.iloc[29])

                print(f"   الفئة المالية: {financial_category}")
                print(f"   قائمة الأسعار: {price_list}")

                result["processed"] += 1
                processed += 1

                # ✅ البحث في Cache
                key = entity_name
                existing_profile = profiles_cache.get(key)

                if existing_profile:
                    # ✅ تحديث الملف الموجود
                    changed = False
                    
                    if existing_profile.financial_category != financial_category:
                        existing_profile.financial_category = financial_category
                        changed = True
                        
                    if existing_profile.price_list != price_list:
                        existing_profile.price_list = price_list
                        changed = True
                        
                    if existing_profile.attachment != attachment:
                        existing_profile.attachment = attachment
                        changed = True

                    if changed:
                        existing_profile.save()
                        result["updated"] += 1
                        print(f"   ✅ تم تحديث الملف")
                    else:
                        print(f"   ✅ الملف موجود بدون تغييرات")
                    
                    current_profile = existing_profile

                else:
                    # ✅ إنشاء ملف جديد
                    current_profile = CompanyExceptionProfile.objects.create(
                        entity_name=entity_name,
                        financial_category=financial_category,
                        price_list=price_list,
                        attachment=attachment,
                    )
                    profiles_cache[key] = current_profile
                    result["profiles"] += 1
                    print(f"   ✅ تم إنشاء ملف جديد")

                # ✅ جمع التفاصيل المتعددة من الصفوف التالية
                detail_rows = []
                next_idx = i + 1
                while next_idx < len(dataframe):
                    next_row = dataframe.iloc[next_idx]
                    # إذا وجدنا جهة جديدة نوقف
                    if pd.notna(next_row.iloc[0]):
                        break
                    # إذا كان الصف فارغاً تماماً نستمر
                    if next_row.isna().all():
                        next_idx += 1
                        continue
                    detail_rows.append(next_row)
                    next_idx += 1

                print(f"   📋 عدد صفوف التفاصيل: {len(detail_rows)}")

                # ✅ بناء العناصر
                display_order = 1
                items_count = 0
                items_to_create = []
                items_to_update = []

                # ✅ أولاً: الخدمات الأساسية من الصف الرئيسي
                for section, service_name, discount_col, details_col, price_col in COLUMN_MAP:
                    # قراءة الخصم
                    discount = None
                    if discount_col is not None and len(row) > discount_col:
                        val = row.iloc[discount_col]
                        if pd.notna(val):
                            discount = CompanyExceptionImportService._get_discount_value(val)

                    # قراءة التفاصيل الأساسية
                    base_details = ""
                    if details_col is not None and len(row) > details_col:
                        val = row.iloc[details_col]
                        if pd.notna(val):
                            base_details = ImportHelpers.normalize_text(val)

                    base_price = ""
                    if price_col is not None and len(row) > price_col:
                        val = row.iloc[price_col]
                        if pd.notna(val):
                            base_price = ImportHelpers.normalize_text(val)

                    # نضيف الخدمة الأساسية إذا فيها بيانات
                    if discount is not None or base_details or base_price:
                        discount_rate = str(discount) if discount is not None else ""
                        
                        # ✅ البحث في Cache للتحديث
                        item_key = (
                            current_profile.id,
                            section,
                            service_name,
                            base_details,
                        )
                        existing_item = items_cache.get(item_key)

                        if existing_item:
                            # ✅ تحديث العنصر الموجود
                            changed = False
                            if existing_item.discount_rate != discount_rate:
                                existing_item.discount_rate = discount_rate
                                changed = True
                            if existing_item.net_price != base_price:
                                existing_item.net_price = base_price
                                changed = True
                            if existing_item.display_order != display_order:
                                existing_item.display_order = display_order
                                changed = True
                            
                            if changed:
                                items_to_update.append(existing_item)
                        else:
                            # ✅ إنشاء عنصر جديد
                            items_to_create.append(
                                CompanyExceptionItem(
                                    profile=current_profile,
                                    section=section,
                                    service_name=service_name,
                                    discount_rate=discount_rate,
                                    details=base_details,
                                    net_price=base_price,
                                    display_order=display_order,
                                )
                            )
                        
                        display_order += 1
                        items_count += 1

                        discount_display = f"{discount}%" if discount is not None else "0%"
                        price_display = base_price or "-"
                        print(f"   📊 {section} - {service_name}: خصم {discount_display}, سعر: {price_display}")

                # ✅ ثانياً: التفاصيل الإضافية من الصفوف التالية
                for detail_row in detail_rows:
                    for section, service_name, discount_col, details_col, price_col in COLUMN_MAP:
                        details = ""
                        if details_col is not None and len(detail_row) > details_col:
                            val = detail_row.iloc[details_col]
                            if pd.notna(val):
                                details = ImportHelpers.normalize_text(val)

                        net_price = ""
                        if price_col is not None and len(detail_row) > price_col:
                            val = detail_row.iloc[price_col]
                            if pd.notna(val):
                                net_price = ImportHelpers.normalize_text(val)

                        if not details and not net_price:
                            continue

                        discount = None
                        if discount_col is not None and len(row) > discount_col:
                            val = row.iloc[discount_col]
                            if pd.notna(val):
                                discount = CompanyExceptionImportService._get_discount_value(val)

                        discount_rate = str(discount) if discount is not None else ""
                        
                        # ✅ البحث في Cache للتحديث
                        item_key = (
                            current_profile.id,
                            section,
                            service_name,
                            details,
                        )
                        existing_item = items_cache.get(item_key)

                        if existing_item:
                            # ✅ تحديث العنصر الموجود
                            changed = False
                            if existing_item.discount_rate != discount_rate:
                                existing_item.discount_rate = discount_rate
                                changed = True
                            if existing_item.net_price != net_price:
                                existing_item.net_price = net_price
                                changed = True
                            if existing_item.display_order != display_order:
                                existing_item.display_order = display_order
                                changed = True
                            
                            if changed:
                                items_to_update.append(existing_item)
                        else:
                            # ✅ إنشاء عنصر جديد
                            items_to_create.append(
                                CompanyExceptionItem(
                                    profile=current_profile,
                                    section=section,
                                    service_name=service_name,
                                    discount_rate=discount_rate,
                                    details=details,
                                    net_price=net_price,
                                    display_order=display_order,
                                )
                            )

                        display_order += 1
                        items_count += 1
                        print(f"      ➕ {section} - {service_name}: تفاصيل: {details[:30]}, سعر: {net_price}")

                # ✅ Bulk Create للعناصر الجديدة
                if items_to_create:
                    CompanyExceptionItem.objects.bulk_create(items_to_create, batch_size=1000)
                    result["items"] += len(items_to_create)
                    print(f"   ✅ تم إنشاء {len(items_to_create)} عنصر جديد")

                # ✅ Bulk Update للعناصر المحدثة
                if items_to_update:
                    CompanyExceptionItem.objects.bulk_update(
                        items_to_update,
                        fields=["discount_rate", "net_price", "display_order"],
                        batch_size=1000,
                    )
                    result["items"] += len(items_to_update)
                    print(f"   ✅ تم تحديث {len(items_to_update)} عنصر")

                print(f"   ✅ تمت معالجة {items_count} خدمة")
                i = next_idx

            else:
                i += 1

            if processed % 100 == 0 and processed > 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        # ============================================================
        # ✅ النتائج النهائية
        # ============================================================
        print("\n" + "="*80)
        print("✅ انتهى الاستيراد بنجاح!")
        print(f"📊 الملفات: {result['profiles']}, العناصر: {result['items']}")
        print(f"📊 Updated: {result['updated']}, Skipped: {result['skipped']}")
        print("="*80)

        elapsed = time.perf_counter() - start_time
        print(f"⏱️ Completed in {elapsed:.2f} seconds")

        return result