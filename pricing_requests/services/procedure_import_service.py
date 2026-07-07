from django.db import transaction

from pricing_requests.models import Procedure

from imports.utils.import_helpers import ImportHelpers


class ProcedureImportService:

    @staticmethod
    @transaction.atomic
    def import_data(dataframe):

        result = {
            "processed": 0,
            "created": 0,
            "updated": 0,
            "skipped": 0,
        }

        for _, row in dataframe.iterrows():

            code = ImportHelpers.normalize_text(
                row.get("الكود")
            )

            if not code:
                result["skipped"] += 1
                continue

            defaults = {

                "operation_name": ImportHelpers.normalize_text(
                    row.get("أسم العملية")
                ),

                "specialty_name": ImportHelpers.normalize_text(
                    row.get("التخصص")
                ),

                "category": ImportHelpers.normalize_text(
                    row.get("التصنيف")
                ),

                "english_name": ImportHelpers.normalize_text(
                    row.get("المسمي باللغه الانجليزيه")
                ),

            }

            _, created = Procedure.objects.update_or_create(

                code=code,

                defaults=defaults,

            )

            if created:

                result["created"] += 1

            else:

                result["updated"] += 1

            result["processed"] += 1

        return result