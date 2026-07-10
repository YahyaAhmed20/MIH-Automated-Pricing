# imports/services/company_exception_import_service.py

from django.db import transaction
import pandas as pd

from pricing_requests.models import (
    CompanyExceptionProfile,
    CompanyExceptionItem,
)

from imports.utils.import_helpers import ImportHelpers


# ✅ أعمدة الشيت 9 - تم التعديل
COLUMN_MAP = [
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
        result = {
            "processed": 0,
            "profiles": 0,
            "items": 0,
            "skipped": 0,
        }

        i = 0
        while i < len(dataframe):
            row = dataframe.iloc[i]

            # الجهة في العمود 0
            entity_name = None
            if len(row) > 0 and pd.notna(row.iloc[0]):
                entity_name = ImportHelpers.normalize_text(row.iloc[0])

            # لو لقينا جهة جديدة
            if entity_name:
                print(f"\n{'='*60}")
                print(f"🏢 معالجة: {entity_name}")

                # الفئة المالية (العمود 1)
                financial_category = ""
                if len(row) > 1 and pd.notna(row.iloc[1]):
                    financial_category = ImportHelpers.normalize_text(row.iloc[1])

                # قائمة الأسعار (العمود 2)
                price_list = ""
                if len(row) > 2 and pd.notna(row.iloc[2]):
                    price_list = ImportHelpers.normalize_text(row.iloc[2])

                # المرفقات (العمود 29)
                attachment = ""
                if len(row) > 29 and pd.notna(row.iloc[29]):
                    attachment = ImportHelpers.normalize_text(row.iloc[29])

                print(f"   الفئة المالية: {financial_category}")
                print(f"   قائمة الأسعار: {price_list}")

                # ✅ إنشاء الـ Profile
                current_profile, created = (
                    CompanyExceptionProfile.objects.update_or_create(
                        entity_name=entity_name,
                        defaults={
                            "financial_category": financial_category,
                            "price_list": price_list,
                            "attachment": attachment,
                        }
                    )
                )

                # ✅ حذف العناصر القديمة
                deleted_count = current_profile.items.all().delete()
                print(f"   🗑️ تم حذف {deleted_count[0]} عنصر قديم")

                result["processed"] += 1

                if created:
                    result["profiles"] += 1
                    print(f"   ✅ تم إنشاء ملف جديد")
                else:
                    print(f"   ✅ تم تحديث الملف")

                # ✅ جمع التفاصيل المتعددة من الصفوف التالية
                detail_rows = []
                next_idx = i + 1
                while next_idx < len(dataframe):
                    next_row = dataframe.iloc[next_idx]
                    # لو لقينا جهة جديدة نوقف
                    if pd.notna(next_row.iloc[0]):
                        break
                    # لو الصف فارغ تماماً نستمر
                    if next_row.isna().all():
                        next_idx += 1
                        continue
                    detail_rows.append(next_row)
                    next_idx += 1

                print(f"   📋 عدد صفوف التفاصيل: {len(detail_rows)}")

                # ✅ بناء الـ Items
                display_order = 1
                items_count = 0

                # ✅ أولاً: نضيف الخدمات الأساسية من الصف الرئيسي
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

                    # نضيف الخدمة الأساسية لو فيها بيانات
                    if discount is not None or base_details or base_price:
                        CompanyExceptionItem.objects.create(
                            profile=current_profile,
                            section=section,
                            service_name=service_name,
                            discount_rate=str(discount) if discount is not None else "",
                            details=base_details,
                            net_price=base_price,
                            display_order=display_order,
                        )
                        display_order += 1
                        items_count += 1
                        result["items"] += 1

                        discount_display = f"{discount}%" if discount is not None else "0%"
                        price_display = base_price or "-"
                        print(f"   📊 {section} - {service_name}: خصم {discount_display}, تفاصيل: {base_details[:30]}, سعر: {price_display}")

                # ✅ ثانياً: نضيف التفاصيل الإضافية من الصفوف التالية
                for detail_row in detail_rows:
                    # ✅ نمر على كل خدمة في COLUMN_MAP
                    for section, service_name, discount_col, details_col, price_col in COLUMN_MAP:
                        # ✅ نقرأ التفاصيل من الصف الحالي (detail_row) مش من الصف الرئيسي
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

                        # ✅ لو مفيش بيانات في هذا العمود، نستمر
                        if not details and not net_price:
                            continue

                        # ✅ نبحث عن الخصم من الصف الرئيسي
                        discount = None
                        if discount_col is not None and len(row) > discount_col:
                            val = row.iloc[discount_col]
                            if pd.notna(val):
                                discount = CompanyExceptionImportService._get_discount_value(val)

                        # ✅ إنشاء الـ Item مع التفاصيل الإضافية
                        CompanyExceptionItem.objects.create(
                            profile=current_profile,
                            section=section,
                            service_name=service_name,
                            discount_rate=str(discount) if discount is not None else "",
                            details=details,
                            net_price=net_price,
                            display_order=display_order,
                        )

                        display_order += 1
                        items_count += 1
                        result["items"] += 1

                        discount_display = f"{discount}%" if discount is not None else "0%"
                        price_display = net_price or "-"
                        print(f"      ➕ {section} - {service_name}: خصم {discount_display}, تفاصيل: {details}, سعر: {price_display}")

                print(f"   ✅ تمت معالجة {items_count} خدمة")
                i = next_idx
            else:
                i += 1

        print("\n" + "="*80)
        print("✅ انتهى الاستيراد بنجاح!")
        print(f"📊 الملفات: {result['profiles']}, العناصر: {result['items']}, المتخطي: {result['skipped']}")
        print("="*80)

        return result