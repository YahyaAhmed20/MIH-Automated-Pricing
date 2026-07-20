import io
import pandas as pd
import gspread
from pathlib import Path

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
    def get_spreadsheet(cls):

        if cls._spreadsheet is None:

            cls._spreadsheet = (
                cls.get_client().open_by_key(
                    settings.GOOGLE_SPREADSHEET_ID
                )
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
    def get_dataframe(cls, sheet_name):

        worksheet = cls.get_spreadsheet().worksheet(
            str(sheet_name)
        )

        data = worksheet.get_all_values()

        if not data:
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

        return dataframe