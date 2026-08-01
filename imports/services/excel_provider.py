import pandas as pd
from datetime import datetime
from imports.services.google_sheets_service import GoogleSheetsService


class ExcelProvider:

    _cache = {}
    _cache_timestamp = {}  # لتتبع وقت التخزين

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
                unique.append(f"{column}.{used[column]}")

        return unique

    @classmethod
    def read_sheet(
        cls,
        sheet_name,
        header=0,
        force_reload=False,  # ✅ إضافة المعامل الجديد
    ):

        cache_key = (
            str(sheet_name),
            str(header),
        )

        # ✅ إذا كان force_reload، احذف الـ Cache
        if force_reload and cache_key in cls._cache:
            print(f"🔄 Force reload for sheet {sheet_name}")
            del cls._cache[cache_key]
            if cache_key in cls._cache_timestamp:
                del cls._cache_timestamp[cache_key]

        # ✅ استخدام Cache إذا كان موجوداً
        if cache_key in cls._cache:
            print(f"✅ Using cached data for sheet {sheet_name} (cached at {cls._cache_timestamp.get(cache_key, 'unknown')})")
            return cls._cache[cache_key].copy()

        # ✅ قراءة جديدة من Google
        print(f"📥 Fetching fresh data from Google Sheets: {sheet_name}")
        raw = GoogleSheetsService.get_dataframe(
            sheet_name,
            force_reload=force_reload,  # ✅ تمرير force_reload
        )

        if raw.empty:
            print(f"⚠️ Sheet {sheet_name} is empty")
            return pd.DataFrame()

        rows = raw.values.tolist()

        # Debug (اختياري)
        for i in range(min(5, len(rows))):
            print(f"Row {i}: {rows[i][:5] if rows[i] else 'empty'}...")
            print("=" * 80)

        # ==========================
        # header=None
        # ==========================
        if header is None:
            dataframe = pd.DataFrame(rows)
            dataframe.columns = range(len(dataframe.columns))

        # ==========================
        # header = رقم الصف
        # ==========================
        else:
            columns = cls.make_unique_columns(rows[header])
            dataframe = pd.DataFrame(
                rows[header + 1:],
                columns=columns,
            )

        dataframe = dataframe.reset_index(drop=True)

        # ✅ تخزين في Cache مع timestamp
        cls._cache[cache_key] = dataframe
        cls._cache_timestamp[cache_key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"✅ Cached sheet {sheet_name} with {len(dataframe)} rows")

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
        force_reload=False,  # ✅ إضافة المعامل الجديد
    ):

        # لو فيه ملف محلي
        if file_path:
            from imports.utils.excel_reader import ExcelReader
            return ExcelReader.read_sheet(
                file_path=file_path,
                sheet_name=sheet_name,
            )

        # غير كده اقرأ من Google Sheets
        return cls.read_sheet(
            sheet_name=sheet_name,
            header=header,
            force_reload=force_reload,  # ✅ تمرير المعامل
        )