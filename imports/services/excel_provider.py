import pandas as pd
from datetime import datetime
from imports.services.google_sheets_service import GoogleSheetsService


class ExcelProvider:

    _cache = {}
    _cache_timestamp = {}

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
        force_reload=False,
    ):

        cache_key = (
            str(sheet_name),
            str(header),
        )

        # Force reload
        if force_reload and cache_key in cls._cache:
            print(
                f"🔄 Force reload for sheet {sheet_name}"
            )

            del cls._cache[cache_key]

            if cache_key in cls._cache_timestamp:
                del cls._cache_timestamp[cache_key]

        # Use cache
        if cache_key in cls._cache:
            print(
                f"✅ Using cached data for sheet "
                f"{sheet_name} "
                f"(cached at "
                f"{cls._cache_timestamp.get(cache_key, 'unknown')})"
            )

            return cls._cache[cache_key].copy()

        # Read from Google Sheets
        print(
            f"📥 Fetching fresh data from Google Sheets: "
            f"{sheet_name}"
        )

        raw = GoogleSheetsService.get_dataframe(
            sheet_name,
            force_reload=force_reload,
        )

        if raw.empty:
            print(
                f"⚠️ Sheet {sheet_name} is empty"
            )
            return pd.DataFrame()

        # Debug
        for i in range(min(5, len(raw))):
            row_values = raw.iloc[i].tolist()

            print(
                f"Row {i}: "
                f"{row_values[:5] if row_values else 'empty'}..."
            )

            print("=" * 80)

        # ==================================================
        # GoogleSheetsService already returns a DataFrame
        # with the correct headers.
        #
        # لذلك لا نعيد بناء الـ DataFrame من أول صف.
        # ==================================================

        if header is None:
            dataframe = raw.copy()
            dataframe.columns = range(len(dataframe.columns))

        else:
            # GoogleSheetsService already returns a DataFrame
            # with the correct headers and real data.
            dataframe = raw.copy()

            # ضمان عدم وجود أسماء أعمدة مكررة
            dataframe.columns = cls.make_unique_columns(
                dataframe.columns
            )

        dataframe = dataframe.reset_index(drop=True)

        # Cache
        cls._cache[cache_key] = dataframe

        cls._cache_timestamp[cache_key] = (
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        print(
            f"✅ Cached sheet {sheet_name} "
            f"with {len(dataframe)} rows"
        )

        return dataframe.copy()

    @classmethod
    def clear_cache(cls):

        cls._cache.clear()
        cls._cache_timestamp.clear()

        print("🗑️ Cache cleared")

    @classmethod
    def read(
        cls,
        file_path=None,
        sheet_name=None,
        header=0,
        force_reload=False,
    ):

        # Local Excel file
        if file_path:

            from imports.utils.excel_reader import ExcelReader

            return ExcelReader.read_sheet(
                file_path=file_path,
                sheet_name=sheet_name,
            )

        # Google Sheets
        return cls.read_sheet(
            sheet_name=sheet_name,
            header=header,
            force_reload=force_reload,
        )