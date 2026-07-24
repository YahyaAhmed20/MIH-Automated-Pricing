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
    ("داخلي", "الاشعه التداخليه", 3, 4, None),
    ("داخلي", "خدمات الكلي", 5, 6, 7),
    ("داخلي", "العلاج الاشعاعي", 8, 9, 10),
    ("داخلي", "علاج الالم", 11, 12, None),
    ("داخلي", "خدمات بنك الدم", 13, 14, 15),
    ("داخلي", "المرافق", None, 16, None),
    ("داخلي", "الاسعاف", 18, 19, None),
    ("خارجي", "خدمات الكلي", 21, 22, 23),
    ("خارجي", "العلاج الاشعاعي", 24, 25, 26),
    ("خارجي", "الاسعاف", 27, 28, None),
]


class CompanyExceptionImportService:

    @staticmethod
    def _get_discount_value(val):
        if val is None or pd.isna(val):
            return None
        discount = ImportHelpers.clean_percentage(val)
        if discount is None:
            return None
        return round(discount)

    @staticmethod
    def _get_value(row, col):
        """استخراج قيمة من الصف"""
        if col is None:
            return None
        return row.get(col, None)

    @staticmethod
    def _has_data(row):
        """التحقق من وجود بيانات في الصف"""
        if not row:
            return False
        # ✅ التحقق من الأعمدة المهمة (3-28)
        for col in range(3, 29):
            val = row.get(col, None)
            if val is not None and pd.notna(val) and str(val).strip():
                return True
        return False

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

        # ✅ تحويل DataFrame إلى قائمة من Dictionaries
        all_rows = dataframe.to_dict("records")

        # ============================================================
        # ✅ Cache
        # ============================================================
        print("⏳ Loading existing profiles...")
        profiles_cache = {}
        for profile in CompanyExceptionProfile.objects.all():
            key = ImportHelpers.normalize_text(profile.entity_name)
            profiles_cache[key] = profile
        print(f"   ✅ {len(profiles_cache)} profiles loaded")

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
        # ✅ Loop
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(all_rows)
        processed = 0

        i = 0
        while i < len(all_rows):
            row = all_rows[i]

            # ✅ الجهة في العمود 0
            entity_name = ImportHelpers.normalize_text(row.get(0, ""))

            if entity_name:
                print(f"\n{'='*60}")
                print(f"🏢 معالجة: {entity_name}")

                financial_category = ImportHelpers.normalize_text(row.get(1, ""))
                price_list = ImportHelpers.normalize_text(row.get(2, ""))
                attachment = ImportHelpers.normalize_text(row.get(29, ""))

                print(f"   الفئة المالية: {financial_category}")
                print(f"   قائمة الأسعار: {price_list}")

                result["processed"] += 1
                processed += 1

                # ✅ Profile
                key = entity_name
                existing_profile = profiles_cache.get(key)

                if existing_profile:
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
                    current_profile = CompanyExceptionProfile.objects.create(
                        entity_name=entity_name,
                        financial_category=financial_category,
                        price_list=price_list,
                        attachment=attachment,
                    )
                    profiles_cache[key] = current_profile
                    result["profiles"] += 1
                    print(f"   ✅ تم إنشاء ملف جديد")

                # ✅ ✅ ✅ جمع التفاصيل
                detail_rows = []
                next_idx = i + 1
                while next_idx < len(all_rows):
                    next_row = all_rows[next_idx]
                    
                    # ✅ إذا لقينا جهة جديدة، نوقف
                    if ImportHelpers.normalize_text(next_row.get(0, "")):
                        break
                    
                    # ✅ نضيف الصف إذا كان فيه بيانات
                    if CompanyExceptionImportService._has_data(next_row):
                        detail_rows.append(next_row)
                    
                    next_idx += 1

                print(f"   📋 عدد صفوف التفاصيل: {len(detail_rows)}")

                # ✅ عرض أول صف تفاصيل للتحقق
                if detail_rows:
                    print(f"   📝 أول صف تفاصيل: {detail_rows[0].get(6, 'N/A')}")

                # ✅ حذف العناصر القديمة
                deleted_count = current_profile.items.all().delete()
                print(f"   🗑️ تم حذف {deleted_count[0]} عنصر قديم")

                # ✅ بناء العناصر
                all_rows_for_company = [row] + detail_rows
                display_order = 1
                items_count = 0
                items_to_create = []

                # ✅ المعالجة
                for current_row in all_rows_for_company:
                    for section, service_name, discount_col, details_col, price_col in COLUMN_MAP:
                        
                        # ✅ قراءة التفاصيل من الصف الحالي
                        details = ""
                        if details_col is not None:
                            val = current_row.get(details_col, "")
                            if val and pd.notna(val):
                                details = ImportHelpers.normalize_text(str(val))

                        # ✅ قراءة السعر من الصف الحالي
                        net_price = ""
                        if price_col is not None:
                            val = current_row.get(price_col, "")
                            if val and pd.notna(val):
                                net_price = ImportHelpers.normalize_text(str(val))

                        # ✅ لو مفيش تفاصيل ولا سعر، نستمر
                        if not details and not net_price:
                            continue

                        # ✅ قراءة الخصم من الصف الرئيسي
                        discount = None
                        if discount_col is not None:
                            val = row.get(discount_col, "")
                            if val and pd.notna(val):
                                discount = CompanyExceptionImportService._get_discount_value(val)

                        discount_rate = str(discount) if discount is not None else ""

                        # ✅ تشخيص
                        if service_name in ["خدمات الكلي", "العلاج الاشعاعي", "خدمات بنك الدم"] and entity_name == "الاهلى للخدمات الطبية":
                            print(f"      🔍 {section} - {service_name}: {details} | سعر: {net_price}")

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

                # ✅ Bulk Create
                if items_to_create:
                    CompanyExceptionItem.objects.bulk_create(items_to_create, batch_size=1000)
                    result["items"] += len(items_to_create)
                    print(f"   ✅ تم إنشاء {len(items_to_create)} عنصر جديد")

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