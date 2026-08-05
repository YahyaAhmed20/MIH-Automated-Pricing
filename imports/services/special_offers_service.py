# imports/services/special_offers_service.py

import pandas as pd
import time
from django.db import transaction
from decimal import Decimal
from contracts.models import ContractEntity, Specialty, SpecialOffer
from imports.utils.import_helpers import ImportHelpers


class SpecialOfferImportService:

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
    @transaction.atomic
    def import_data(dataframe):

        start_time = time.perf_counter()
        print("⏳ Starting Special Offers import from Sheet 5...")

        result = {
            "processed": 0,
            "created_entities": 0,
            "created_specialties": 0,
            "created_offers": 0,
            "updated_offers": 0,
            "deleted_offers": 0,
        }

        # ============================================================
        # ✅ Cache للـ Entities
        # ============================================================
        print("⏳ Loading entities...")
        entities_cache = {}
        for e in ContractEntity.objects.all():
            key = ImportHelpers.normalize_text(e.name)
            entities_cache[key] = e
        print(f"   ✅ {len(entities_cache)} entities loaded")

        # ============================================================
        # ✅ Cache للـ Specialties
        # ============================================================
        print("⏳ Loading specialties...")
        specialties_cache = {}
        for s in Specialty.objects.all():
            key = ImportHelpers.normalize_text(s.name)
            specialties_cache[key] = s
        print(f"   ✅ {len(specialties_cache)} specialties loaded")

        # ============================================================
        # ✅ Cache للـ Special Offers
        # ============================================================
        print("⏳ Loading existing offers...")
        offers_cache = {}
        for o in SpecialOffer.objects.select_related("entity", "specialty"):
            key = (
                o.entity_id,
                o.offer_for,
                o.specialty_id,
                o.procedure_name,
            )
            offers_cache[key] = o
        print(f"   ✅ {len(offers_cache)} offers loaded")

        # ============================================================
        # ✅ قوائم التجميع للـ Bulk Operations
        # ============================================================
        offers_to_create = []
        offers_to_update = []
        sheet_offers = set()

        # ============================================================
        # ✅ Loop - استخدام أرقام الأعمدة (بدون Header)
        # ============================================================
        print("⏳ Processing rows...")
        total_rows = len(dataframe)
        processed = 0

        for index, row in enumerate(dataframe.to_dict("records"), start=1):

            # ✅ العمود 0: الشركه
            company_name = ImportHelpers.normalize_text(row.get(0, ""))
            company_name = SpecialOfferImportService.truncate_text(company_name, 255)

            if not company_name:
                continue

            # ✅ العمود 1: العرض خاص ب
            offer_for = ImportHelpers.normalize_text(row.get(1, ""))
            offer_for = SpecialOfferImportService.truncate_text(offer_for, 255)

            # ✅ العمود 2: التخصص
            specialty_name = ImportHelpers.normalize_text(row.get(2, ""))
            specialty_name = SpecialOfferImportService.truncate_text(specialty_name, 255)

            # ✅ إذا كان التخصص فارغاً، استخدم "غير محدد"
            if not specialty_name:
                specialty_name = "غير محدد"

            # ✅ العمود 3: الاجراء
            procedure_name = ImportHelpers.normalize_text(row.get(3, ""))
            procedure_name = SpecialOfferImportService.truncate_text(procedure_name, 255)

            if not procedure_name:
                continue

            # ✅ العمود 4: السعر
            price = ImportHelpers.clean_decimal(row.get(4, None))
            if price is None:
                price = Decimal('0.00')

            # ✅ العمود 5: اعتبار من
            valid_from = ImportHelpers.clean_date(row.get(5, None))

            # ✅ العمود 6: ساريه حتي
            valid_to = ImportHelpers.clean_date(row.get(6, None))

            # ✅ العمود 7: ملاحظات
            notes = ImportHelpers.normalize_text(row.get(7, ""))
            notes = SpecialOfferImportService.truncate_text(notes, 500)

            result["processed"] += 1
            processed = result["processed"]

            # ============================================================
            # ✅ Entity - من Cache
            # ============================================================
            entity_key = ImportHelpers.normalize_text(company_name)
            entity = entities_cache.get(entity_key)

            if not entity:
                entity = ContractEntity.objects.create(name=company_name)
                entities_cache[entity_key] = entity
                result["created_entities"] += 1

            # ============================================================
            # ✅ Specialty - من Cache
            # ============================================================
            specialty_key = ImportHelpers.normalize_text(specialty_name)
            specialty = specialties_cache.get(specialty_key)

            if not specialty:
                specialty = Specialty.objects.create(
                    name=specialty_name,
                    is_active=True,
                )
                specialties_cache[specialty_key] = specialty
                result["created_specialties"] += 1

            # ============================================================
            # ✅ Special Offer - من Cache
            # ============================================================
            offer_key = (
                entity.id,
                offer_for,
                specialty.id,
                procedure_name,
            )
            
            # ✅ تتبع العروض في الشيت
            sheet_offers.add(offer_key)
            
            existing_offer = offers_cache.get(offer_key)

            if existing_offer:
                # ✅ تحديث البيانات
                changed = False

                if existing_offer.price != price:
                    existing_offer.price = price
                    changed = True

                if existing_offer.valid_from != valid_from:
                    existing_offer.valid_from = valid_from
                    changed = True

                if existing_offer.valid_to != valid_to:
                    existing_offer.valid_to = valid_to
                    changed = True

                if existing_offer.notes != notes:
                    existing_offer.notes = notes
                    changed = True

                if existing_offer.is_active is not True:
                    existing_offer.is_active = True
                    changed = True

                if changed:
                    offers_to_update.append(existing_offer)
                    result["updated_offers"] += 1

            else:
                # ✅ إنشاء جديد
                new_offer = SpecialOffer(
                    entity=entity,
                    procedure_name=procedure_name,
                    offer_for=offer_for,
                    specialty=specialty,
                    price=price,
                    valid_from=valid_from,
                    valid_to=valid_to,
                    notes=notes,
                    is_active=True,
                )
                offers_to_create.append(new_offer)
                offers_cache[offer_key] = new_offer
                result["created_offers"] += 1

            if processed % 1000 == 0:
                print(f"   📊 Processed {processed}/{total_rows} rows...")

        print(f"   ✅ Processed {processed}/{total_rows} rows")

        # ============================================================
        # ✅ تنفيذ الـ Bulk Operations
        # ============================================================
        print(f"💾 Creating {len(offers_to_create)} offers...")
        print(f"💾 Updating {len(offers_to_update)} offers...")

        if offers_to_create:
            SpecialOffer.objects.bulk_create(offers_to_create, batch_size=1000)

        if offers_to_update:
            SpecialOffer.objects.bulk_update(
                offers_to_update,
                fields=[
                    "price",
                    "valid_from",
                    "valid_to",
                    "notes",
                    "is_active",
                ],
                batch_size=1000,
            )

        # ============================================================
        # ✅ Reload Offers
        # ============================================================
        offers_cache = {}
        for o in SpecialOffer.objects.select_related("entity", "specialty"):
            key = (
                o.entity_id,
                o.offer_for,
                o.specialty_id,
                o.procedure_name,
            )
            offers_cache[key] = o

        # ============================================================
        # ✅ Delete Offers not found in Sheet
        # ============================================================
        offers_to_delete = []

        for key, offer in offers_cache.items():
            if key not in sheet_offers:
                offers_to_delete.append(offer.id)

        if offers_to_delete:
            deleted, _ = SpecialOffer.objects.filter(
                id__in=offers_to_delete
            ).delete()

            result["deleted_offers"] = deleted
            print(f"🗑️ Deleted {deleted} offers")

        elapsed = time.perf_counter() - start_time
        print(f"✅ Completed in {elapsed:.2f} seconds")

        return result