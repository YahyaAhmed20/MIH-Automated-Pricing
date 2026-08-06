# pricing_requests/services/procedure_fees_import_service.py

import time
from django.db import transaction
from decimal import Decimal

from pricing_requests.models import ProcedureFee
from medical_catalog.models import Procedure
from imports.utils.import_helpers import ImportHelpers


class ProcedureFeesImportService:

    # ✅ ✅ ✅ دالة توحيد التصنيفات
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

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Procedure Fees import from Sheet 14...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ Cache للـ Procedure Fees
        # ============================================================
        print("⏳ Loading existing procedure fees...")
        fees_cache = {}
        for fee in ProcedureFee.objects.all():
            key = (
                ImportHelpers.normalize_text(fee.entity_name),
                ImportHelpers.normalize_text(fee.financial_category),
                ImportHelpers.normalize_text(fee.category),
            )
            fees_cache[key] = fee
        print(f"   ✅ {len(fees_cache)} fees loaded")

        # ============================================================
        # ✅ Existing Keys + Sheet Keys
        # ============================================================
        existing_keys = set(fees_cache.keys())
        sheet_keys = set()

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        to_create = []
        to_update = []

        # ============================================================
        # ✅ متغيرات لتتبع الجهة الحالية
        # ============================================================
        current_entity = None
        current_financial = None
        current_price_list = None
        current_discount = None

        # ✅ ✅ ✅ متغير لتتبع التصنيفات غير المتطابقة
        mismatched_categories = set()

        # ============================================================
        # ✅ Loop - استخدام itertuples
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.itertuples(index=False), start=1):

            # ✅ أرقام الأعمدة حسب ترتيب شيت 14
            # العمود 0: الجهه (اسم الشركة)
            entity_name = ImportHelpers.normalize_text(row[0])
            
            # العمود 1: الفئه الماليه (كود الشركة)
            financial_category = ImportHelpers.normalize_text(row[1])
            
            # العمود 2: قائمة الاسعار (السنة)
            price_list = ImportHelpers.normalize_text(row[2])
            
            # العمود 3: التصنيف (نوع الخدمة)
            category_raw = row[3]
            category = ImportHelpers.normalize_text(category_raw)
            
            # ✅ ✅ ✅ توحيد التصنيف فوراً
            category = ProcedureFeesImportService.normalize_category(category)
            
            # ✅ العمود 4: اتعاب (أتعاب الجراح)
            surgeon_raw = row[4]
            surgeon_fee = ImportHelpers.clean_decimal(surgeon_raw)
            if surgeon_fee is None:
                surgeon_fee = Decimal('0.00')
            
            # ✅ العمود 5: اتعاب.1 (أتعاب التخدير)
            anesthesia_raw = row[5]
            anesthesia_fee = ImportHelpers.clean_decimal(anesthesia_raw)
            if anesthesia_fee is None:
                anesthesia_fee = Decimal('0.00')
            
            # ✅ العمود 6: اتعاب.2 (أتعاب المساعد)
            assistant_raw = row[6]
            assistant_fee = ImportHelpers.clean_decimal(assistant_raw)
            if assistant_fee is None:
                assistant_fee = Decimal('0.00')
            
            # ✅ العمود 7: اجمالي الاتعاب
            total_raw = row[7]
            total_fee = ImportHelpers.clean_decimal(total_raw)
            if total_fee is None:
                total_fee = Decimal('0.00')
            
            # ✅ العمود 8: معدل الخصم
            discount_raw = row[8]
            if discount_raw and str(discount_raw).strip():
                discount_rate = str(discount_raw).strip()
            else:
                discount_rate = ""

            # ✅ ✅ ✅ التحقق من تطابق التصنيف مع التصنيفات الموجودة في جدول Procedure
            if category and not entity_name:
                exists_in_procedure = Procedure.objects.filter(classification=category).exists()
                if not exists_in_procedure:
                    mismatched_categories.add(category)

            # ✅ إذا كان الصف يحتوي على معلومات جهة جديدة
            if entity_name:
                current_entity = entity_name
                current_financial = financial_category
                current_price_list = price_list
                current_discount = discount_rate
                result["skipped"] += 1
                continue

           
            # ✅ إذا كان الصف يحتوي على تصنيف وأتعاب
            if category and current_entity:
                result["processed"] += 1
                processed = result["processed"]

                # ✅ بناء مفتاح البحث
                key = (
                    current_entity,
                    current_financial,
                    category,
                )
                
                # ✅ إضافة المفتاح إلى sheet_keys
                sheet_keys.add(key)
                
                existing_fee = fees_cache.get(key)

                if existing_fee:
                    # ✅ تحديث البيانات
                    changed = False
                    
                    if existing_fee.price_list != current_price_list:
                        existing_fee.price_list = current_price_list
                        changed = True
                        
                    if existing_fee.surgeon_fee != surgeon_fee:
                        existing_fee.surgeon_fee = surgeon_fee
                        changed = True
                        
                    if existing_fee.anesthesia_fee != anesthesia_fee:
                        existing_fee.anesthesia_fee = anesthesia_fee
                        changed = True
                        
                    if existing_fee.assistant_fee != assistant_fee:
                        existing_fee.assistant_fee = assistant_fee
                        changed = True
                        
                    if existing_fee.total_fee != total_fee:
                        existing_fee.total_fee = total_fee
                        changed = True
                        
                    if existing_fee.discount_rate != current_discount:
                        existing_fee.discount_rate = current_discount
                        changed = True

                    if changed:
                        to_update.append(existing_fee)
                        result["updated"] += 1

                else:
                    # ✅ إنشاء جديد
                    fee = ProcedureFee(
                        entity_name=current_entity,
                        financial_category=current_financial,
                        price_list=current_price_list,
                        category=category,
                        surgeon_fee=surgeon_fee,
                        anesthesia_fee=anesthesia_fee,
                        assistant_fee=assistant_fee,
                        total_fee=total_fee,
                        discount_rate=current_discount,
                    )
                    to_create.append(fee)
                    fees_cache[key] = fee
                    result["created"] += 1

            else:
                # ✅ الصف فارغ أو غير مكتمل
                if not category and not entity_name:
                    result["skipped"] += 1

            # ✅ ✅ ✅ تم التعديل: أصبحت الطباعة كل 100 صف بدلاً من 1000
            if processed % 100 == 0 and processed > 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ عرض التصنيفات غير المتطابقة
        # ============================================================
        if mismatched_categories:
            print("\n" + "="*80)
            print("⚠️ تحذير: التصنيفات التالية غير موجودة في جدول Procedure:")
            print("="*80)
            for cat in sorted(mismatched_categories):
                print(f"   ❌ {cat}")
            print("\n💡 نصيحة: أضف هذه التصنيفات إلى جدول Procedure")
            print("   أو قم بتحديث التصنيفات في ملف Excel لتطابق")
            print("="*80 + "\n")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(to_create)} fees...")
        print(f"💾 Updating {len(to_update)} fees...")

        if to_create:
            ProcedureFee.objects.bulk_create(to_create, batch_size=1000)

        if to_update:
            ProcedureFee.objects.bulk_update(
                to_update,
                fields=[
                    "price_list",
                    "surgeon_fee",
                    "anesthesia_fee",
                    "assistant_fee",
                    "total_fee",
                    "discount_rate",
                ],
                batch_size=1000,
            )

        # ============================================================
        # ✅ Delete Removed Fees
        # ============================================================
        keys_to_delete = existing_keys - sheet_keys

        if keys_to_delete:
            ids_to_delete = [
                fees_cache[key].id
                for key in keys_to_delete
            ]

            deleted, _ = ProcedureFee.objects.filter(
                id__in=ids_to_delete
            ).delete()

            result["deleted"] = deleted

        elapsed = time.perf_counter() - start_time

        # عرض النتائج النهائية
        print("=" * 60)
        print("✅ انتهى الاستيراد بنجاح!")
        print(
            f"📊 Processed: {result['processed']}, "
            f"Created: {result['created']}, "
            f"Updated: {result['updated']}, "
            f"Deleted: {result['deleted']}, "
            f"Skipped: {result['skipped']}"
        )
        print("=" * 60)
        print(f"⏱️ Completed in {elapsed:.2f} seconds")

        return result