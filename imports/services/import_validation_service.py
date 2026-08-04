from imports.utils.import_helpers import ImportHelpers


class ImportValidationService:

    INVALID_VALUES = {
        "",
        "-",
        "None",
        "N/A",
        "#REF!",
        "#ref!",
        "#VALUE!",
        "#NAME?",
        "#DIV/0!",
        "#NUM!",
        "#NULL!",
        "# code",
        "#CODE",
    }

    @classmethod
    def normalize(cls, value):

        return ImportHelpers.normalize_text(value)

    @classmethod
    def is_placeholder(cls, value):

        value = cls.normalize(value)

        return value in cls.INVALID_VALUES

    @classmethod
    def has_company(cls, company_name):

        return not cls.is_placeholder(company_name)

    @classmethod
    def has_package_name(cls, package_name):

        return not cls.is_placeholder(package_name)

    @classmethod
    def valid_package_codes(cls, package_codes):

        valid = []

        for code in package_codes:

            code = cls.normalize(code)

            if cls.is_placeholder(code):
                continue

            valid.append(code)

        return valid