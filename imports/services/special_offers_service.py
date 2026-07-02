from django.db import transaction

from contracts.models import (
    ContractEntity,
    Specialty,
    SpecialOffer,
)

from imports.utils.import_helpers import (
    ImportHelpers,
)


class SpecialOfferImportService:

    @staticmethod
    def get_entity(company_name, result):

        entity, created = ContractEntity.objects.get_or_create(
            name=company_name
        )

        if created:
            result["created_entities"] += 1

        return entity

    @staticmethod
    def get_specialty(specialty_name, result):

        specialty, created = Specialty.objects.get_or_create(
            name=specialty_name,
            defaults={
                "is_active": True,
            }
        )

        if created:
            result["created_specialties"] += 1

        return specialty

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        result = {
            "processed": 0,
            "created_entities": 0,
            "created_specialties": 0,
            "created_offers": 0,
            "updated_offers": 0,
        }

        for _, row in dataframe.iterrows():

            company_name = ImportHelpers.normalize_text(
                row.get("الشركه")
            )

            offer_for = ImportHelpers.normalize_text(
                row.get("العرض خاص ب")
            )

            specialty_name = ImportHelpers.normalize_text(
                row.get("التخصص")
            )

            procedure_name = ImportHelpers.normalize_text(
                row.get("الاجراء")
            )

            if not company_name or not procedure_name:
                continue

            result["processed"] += 1

            entity = SpecialOfferImportService.get_entity(
                company_name,
                result
            )

            specialty = SpecialOfferImportService.get_specialty(
                specialty_name,
                result
            )

            
            defaults = {

                "offer_for": offer_for,

                "specialty": specialty,

                "price": ImportHelpers.clean_decimal(
                    row.get("السعر")
                ),

                "valid_from": ImportHelpers.clean_date(
                    row.get("اعتبار من")
                ),

                "valid_to": ImportHelpers.clean_date(
                    row.get("ساريه حتي")
                ),

                "notes": ImportHelpers.normalize_text(
                    row.get("ملاحظات")
                ),

                "is_active": True,

            }

            offer, created = SpecialOffer.objects.update_or_create(

                entity=entity,

                procedure_name=procedure_name,

                defaults=defaults,

            )

            if created:
                result["created_offers"] += 1
            else:
                result["updated_offers"] += 1

        return result