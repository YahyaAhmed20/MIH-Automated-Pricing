from medical_catalog.models import (
    Specialty,
    Procedure,
)


class ProcedureImportService:

    @staticmethod
    def clean_value(value):

        if value is None:
            return ""

        text = str(value).strip()

        if text.lower() == "nan":
            return ""

        return text

    @staticmethod
    def import_data(dataframe):

        created_specialties = 0
        created_procedures = 0
        updated_procedures = 0

        errors = []

        for index, row in dataframe.iterrows():

            try:

                procedure_code = (
                    ProcedureImportService.clean_value(
                        row.get("procedure_code")
                    )
                )

                if not procedure_code:
                    continue

                specialty_name = (
                    ProcedureImportService.clean_value(
                        row.get("specialty")
                    )
                )

                specialty, specialty_created = (
                    Specialty.objects.get_or_create(
                        name=specialty_name,
                        defaults={
                            "is_active": True
                        }
                    )
                )

                if specialty_created:
                    created_specialties += 1

                procedure, created = (
                    Procedure.objects.update_or_create(
                        code=procedure_code,
                        defaults={
                            "specialty": specialty,

                            "name_ar":
                                ProcedureImportService.clean_value(
                                    row.get(
                                        "procedure_name_ar"
                                    )
                                ),

                            "name_en":
                                ProcedureImportService.clean_value(
                                    row.get(
                                        "procedure_name_en"
                                    )
                                ),

                            "classification":
                                ProcedureImportService.clean_value(
                                    row.get(
                                        "procedure_category"
                                    )
                                ) or None,

                            "is_active": True,
                        }
                    )
                )

                if created:
                    created_procedures += 1
                else:
                    updated_procedures += 1

            except Exception as e:

                errors.append(
                    f"Row {index + 2}: {str(e)}"
                )

        return {
            "created_specialties":
                created_specialties,

            "created_procedures":
                created_procedures,

            "updated_procedures":
                updated_procedures,

            "errors_count":
                len(errors),

            "errors":
                errors,
        }