# imports/services/company_discount_rank_import_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from pricing_requests.models import CompanyDiscountRank
from imports.utils.import_helpers import ImportHelpers


class CompanyDiscountRankImportService:

    @staticmethod
    def parse_discount(value):
        """
        تحويل الخصم من صيغ مختلفة إلى نسبة مئوية
        
        أمثلة:
        - 0.65 -> 65.0
        - 65% -> 65.0
        - 65 -> 65.0
        - "65%" -> 65.0
        - "" -> 0
        """
        if value is None or pd.isna(value):
            return Decimal('0.00')
        
        try:
            # تحويل إلى نص
            value_str = str(value).strip()
            
            if not value_str:
                return Decimal('0.00')
            
            # إزالة علامة النسبة المئوية
            value_str = value_str.replace('%', '')
            
            # تحويل إلى رقم
            num = float(value_str)
            
            # إذا كان الرقم بين 0 و 1، نضربه في 100 (لأنه نسبة مئوية)
            if 0 < num <= 1:
                num = num * 100
            
            return Decimal(str(num)).quantize(Decimal('0.01'))
            
        except (ValueError, TypeError):
            return Decimal('0.00')

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Company Discount Rank import from Sheet 8...")

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "deleted": 0,
            "skipped": 0,
        }

        # ============================================================
        # ✅ Cache للـ Company Discount Rank
        # ============================================================
        print("⏳ Loading existing company discount ranks...")
        ranks_cache = {}
        for rank in CompanyDiscountRank.objects.all():
            key = ImportHelpers.normalize_text(rank.company_name)
            ranks_cache[key] = rank
        print(f"   ✅ {len(ranks_cache)} ranks loaded")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        to_create = []
        to_update = []
        sheet_records = set()

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة (بدون Header)
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ أرقام الأعمدة في شيت 8
            # العمود 0: اسم الشركة
            company_name = ImportHelpers.normalize_text(row.get(0, ""))
            
            # العمود 1: الفئة المالية
            financial_category = ImportHelpers.normalize_text(row.get(1, ""))
            
            # العمود 2: قائمة الأسعار (السنة)
            price_list = ImportHelpers.normalize_text(row.get(2, ""))
            
            # العمود 3: الخصم الداخلي
            internal_discount_raw = row.get(3, None)
            internal_discount = CompanyDiscountRankImportService.parse_discount(internal_discount_raw)
            
            # العمود 4: فارغ (لا نستخدمه)
            # العمود 5: الخصم الخارجي
            external_discount_raw = row.get(5, None)
            external_discount = CompanyDiscountRankImportService.parse_discount(external_discount_raw)
            
            # العمود 6: صورة العقد (رابط)
            attachment = ImportHelpers.normalize_text(row.get(6, ""))

            # ✅ تخطي الصفوف الفارغة (عناوين)
            if not company_name:
                result["skipped"] += 1
                continue

            # ✅ تخطي الصفوف التي تحتوي على عناوين (مثل "البنود الخاضعه للخصم")
            if company_name in ["البنود الخاضعه للخصم", "معدل الخصم", ""]:
                result["skipped"] += 1
                continue

            result["processed"] += 1
            processed = result["processed"]

            # ✅ طباعة أول 5 صفوف للتحقق
            if processed <= 5:
                print(f"   🔍 Row {index}: {company_name} - Internal: {internal_discount}%, External: {external_discount}%")

            # ✅ البحث في Cache
            key = company_name
            sheet_records.add(key)
            existing_rank = ranks_cache.get(key)

            if existing_rank:
                # ✅ تحديث البيانات
                changed = False
                
                if existing_rank.financial_category != financial_category:
                    existing_rank.financial_category = financial_category
                    changed = True
                    
                if existing_rank.price_list != price_list:
                    existing_rank.price_list = price_list
                    changed = True
                    
                if existing_rank.internal_discount != internal_discount:
                    existing_rank.internal_discount = internal_discount
                    changed = True
                    
                if existing_rank.external_discount != external_discount:
                    existing_rank.external_discount = external_discount
                    changed = True
                    
                if existing_rank.attachment != attachment:
                    existing_rank.attachment = attachment
                    changed = True

                if changed:
                    to_update.append(existing_rank)
                    result["updated"] += 1

            else:
                # ✅ إنشاء جديد
                rank = CompanyDiscountRank(
                    company_name=company_name,
                    financial_category=financial_category,
                    price_list=price_list,
                    internal_discount=internal_discount,
                    external_discount=external_discount,
                    attachment=attachment,
                )
                to_create.append(rank)
                ranks_cache[key] = rank
                result["created"] += 1

            if processed % 1000 == 0 and processed > 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(to_create)} ranks...")
        print(f"💾 Updating {len(to_update)} ranks...")

        BATCH_SIZE = 500

        if to_create:
            CompanyDiscountRank.objects.bulk_create(
                to_create,
                batch_size=BATCH_SIZE,
            )

        if to_update:
            total_updated = 0

            for i in range(0, len(to_update), BATCH_SIZE):
                batch = to_update[i:i + BATCH_SIZE]

                CompanyDiscountRank.objects.bulk_update(
                    batch,
                    fields=[
                        "financial_category",
                        "price_list",
                        "internal_discount",
                        "external_discount",
                        "attachment",
                    ],
                    batch_size=100,
                )

                total_updated += len(batch)

                print(
                    f"   ✅ Updated batch {i // BATCH_SIZE + 1} "
                    f"({total_updated}/{len(to_update)})"
                )

        # ============================================================
        # ✅ Reload Cache بعد الـ Bulk Operations
        # ============================================================
        ranks_cache = {}
        for rank in CompanyDiscountRank.objects.all():
            key = ImportHelpers.normalize_text(rank.company_name)
            ranks_cache[key] = rank

        # ============================================================
        # ✅ Delete Ranks not found in Sheet
        # ============================================================
        ranks_to_delete = []

        for key, rank in ranks_cache.items():
            if key not in sheet_records:
                ranks_to_delete.append(rank.id)

        if ranks_to_delete:
            deleted, _ = CompanyDiscountRank.objects.filter(
                id__in=ranks_to_delete
            ).delete()

            result["deleted"] = deleted
            print(f"🗑️ Deleted {deleted} ranks")

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result