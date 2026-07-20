import pandas as pd

from imports.services.google_sheets_service import (
    GoogleSheetsService,
)


class ExcelProvider:

    _cache = {}

    @staticmethod
    def make_unique_columns(columns):

        used = {}
        unique = []

        for column in columns:

            column = str(column).strip()

            if column not in used:

                used[column] = 0
                unique.append(column)

            else:

                used[column] += 1

                unique.append(
                    f"{column}.{used[column]}"
                )

        return unique

    @classmethod
    def read_sheet(
        cls,
        sheet_name,
        header=0,
    ):

        cache_key = (
            str(sheet_name),
            str(header),
        )

        if cache_key in cls._cache:
            return cls._cache[cache_key].copy()

        # البيانات الخام من Google
        raw = GoogleSheetsService.get_dataframe(
            sheet_name
        )

        if raw.empty:

            return pd.DataFrame()

        rows = raw.values.tolist()
        
        for i in range(5):
            print(f"Row {i}:")
            print(rows[i])
            print("=" * 80)

        # ==========================
        # header=None
        # ==========================
        if header is None:

            dataframe = pd.DataFrame(rows)
            dataframe.columns = range(
                len(dataframe.columns)
            )

        # ==========================
        # header = رقم الصف
        # ==========================
        else:

            columns = cls.make_unique_columns(
                rows[header]
            )

            dataframe = pd.DataFrame(
                rows[header + 1:],
                columns=columns,
            )

        dataframe = dataframe.reset_index(
            drop=True
        )

        cls._cache[
            cache_key
        ] = dataframe

        return dataframe.copy()

    @classmethod
    def clear_cache(cls):

        cls._cache.clear()

    @classmethod
    def read(
        cls,
        file_path=None,
        sheet_name=None,
        header=0,
    ):

        # لو فيه ملف محلي
        if file_path:

            from imports.utils.excel_reader import (
                ExcelReader,
            )

            return ExcelReader.read_sheet(
                file_path=file_path,
                sheet_name=sheet_name,
            )

        # غير كده اقرأ من Google Sheets
        return cls.read_sheet(
            sheet_name=sheet_name,
            header=header,
        )