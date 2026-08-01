import io
import pandas as pd
import gspread
from pathlib import Path
from datetime import datetime

from django.conf import settings

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


class GoogleSheetsService:

    _client = None
    _spreadsheet = None
    _cache = {}  # ✅ Cache للبيانات
    _cache_time = {}  # ✅ وقت التخزين

    @classmethod
    def get_client(cls):

        if cls._client is None:

            credentials = Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=SCOPES,
            )

            cls._client = gspread.authorize(credentials)

        return cls._client

    @classmethod
    def get_spreadsheet(cls, force_reload=False):  # ✅ إضافة force_reload

        # ✅ إذا كان force_reload، أعد فتح الـ Spreadsheet
        if force_reload:
            print(f"🔄 Force reloading spreadsheet at {datetime.now()}")
            cls._spreadsheet = None

        if cls._spreadsheet is None:
            cls._spreadsheet = cls.get_client().open_by_key(
                settings.GOOGLE_SPREADSHEET_ID
            )

        return cls._spreadsheet

    @classmethod
    def get_drive_service(cls):

        credentials = Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=[
                "https://www.googleapis.com/auth/drive.readonly",
                "https://www.googleapis.com/auth/spreadsheets.readonly",
            ],
        )

        return build(
            "drive",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )

    @classmethod
    def download_excel(cls):

        settings.TEMP_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        request = (
            cls.get_drive_service()
            .files()
            .export_media(
                fileId=settings.GOOGLE_SPREADSHEET_ID,
                mimeType=(
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
            )
        )

        file_stream = io.BytesIO()

        downloader = MediaIoBaseDownload(
            file_stream,
            request,
        )

        done = False

        while not done:

            _, done = downloader.next_chunk()

        with open(
            settings.TEMP_EXCEL_FILE,
            "wb",
        ) as output:

            output.write(
                file_stream.getvalue()
            )

        return Path(
            settings.TEMP_EXCEL_FILE
        )

    @classmethod
    def get_dataframe(cls, sheet_name, force_reload=False):  # ✅ إضافة force_reload

        cache_key = str(sheet_name)

        # ✅ إذا كان force_reload، احذف الـ Cache
        if force_reload:
            if cache_key in cls._cache:
                print(f"🔄 Force reload for sheet {sheet_name} (was cached at {cls._cache_time.get(cache_key, 'unknown')})")
                del cls._cache[cache_key]
                if cache_key in cls._cache_time:
                    del cls._cache_time[cache_key]

            # ✅ أعد فتح الـ Spreadsheet
            cls.get_spreadsheet(force_reload=True)

        # ✅ استخدام Cache إذا كان موجوداً
        if cache_key in cls._cache:
            print(f"✅ Using cached data for sheet {sheet_name}")
            return cls._cache[cache_key].copy()

        # ✅ قراءة جديدة من Google
        print(f"📥 Fetching fresh data from Google Sheets: {sheet_name}")

        worksheet = cls.get_spreadsheet().worksheet(
            str(sheet_name)
        )

        data = worksheet.get_all_values()

        if not data:
            print(f"⚠️ Sheet {sheet_name} is empty")
            return pd.DataFrame()

        # ✅ استخدام أول صف كـ header
        headers = data[0]
        rows = data[1:]

        # ✅ إنشاء DataFrame مع headers
        dataframe = pd.DataFrame(rows, columns=headers)

        # حذف الصفوف الفارغة بالكامل
        dataframe = dataframe.replace("", pd.NA)
        dataframe = dataframe.dropna(how="all")
        dataframe = dataframe.fillna("")

        dataframe = dataframe.reset_index(drop=True)

        # ✅ تخزين في Cache مع timestamp
        cls._cache[cache_key] = dataframe
        cls._cache_time[cache_key] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"✅ Cached sheet {sheet_name} with {len(dataframe)} rows")

        return dataframe.copy()

    @classmethod
    def clear_cache(cls):  # ✅ إضافة مسح الـ Cache
        cls._cache.clear()
        cls._cache_time.clear()
        cls._spreadsheet = None
        print("🗑️ Google Sheets cache cleared")