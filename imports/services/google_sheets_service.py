import io
import re  # ✅ مضافة لاستخراج الـ file_id من الروابط
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
    # ✅ تم إزالة scope drive.readonly لأننا نستخدم get_drive_service() للـ Drive
]


class GoogleSheetsService:

    _client = None
    _spreadsheet = None
    _cache = {}
    _cache_time = {}

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
    def get_spreadsheet(cls, force_reload=False):
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
            output.write(file_stream.getvalue())

        return Path(settings.TEMP_EXCEL_FILE)

    # ✅ طريقة جديدة - مطلوبة لاستخراج Smart Chips
    @classmethod
    def get_sheets_api_service(cls):
        credentials = Credentials.from_service_account_file(
            settings.GOOGLE_SERVICE_ACCOUNT_FILE,
            scopes=SCOPES,
        )
        return build(
            "sheets",
            "v4",
            credentials=credentials,
            cache_discovery=False,
        )

    # ✅ طريقة جديدة - استخراج روابط Drive من Smart Chips (محسّنة بالقراءة على دفعات)
    @classmethod
    def get_drive_links(
        cls,
        sheet_name,
        start_row=1,
        end_row=None,
        end_column="U",
    ):
        """
        استخراج روابط ملفات Google Drive الموجودة كـ Smart Chips
        داخل خلايا Google Sheets.

        يتم القراءة على دفعات لتجنب Timeout مع الشيتات الكبيرة.

        Returns:
            {
                (row_index, column_index): {
                    "name": "...",
                    "url": "...",
                    "file_id": "...",
                    "mime_type": "..."
                }
            }
        """

        service = cls.get_sheets_api_service()

        # ============================================================
        # إعدادات القراءة
        # ============================================================

        BATCH_SIZE = 500

        if end_row is None:
            # لو لم يتم تحديد النهاية، نستخدم آخر صف معروف
            worksheet = cls.get_spreadsheet().worksheet(
                str(sheet_name)
            )

            end_row = worksheet.row_count

        links = {}

        current_row = start_row

        total_rows = end_row - start_row + 1

        print(
            f"⏳ Reading Drive Smart Chips in batches "
            f"of {BATCH_SIZE} rows..."
        )

        # ============================================================
        # القراءة على دفعات
        # ============================================================

        while current_row <= end_row:

            batch_end = min(
                current_row + BATCH_SIZE - 1,
                end_row,
            )

            range_name = (
                f"{sheet_name}!"
                f"A{current_row}:{end_column}{batch_end}"
            )

            print(
                f"   📥 Reading rows "
                f"{current_row}-{batch_end} "
                f"of {end_row}"
            )

            result = (
                service.spreadsheets()
                .get(
                    spreadsheetId=settings.GOOGLE_SPREADSHEET_ID,
                    ranges=[range_name],
                    includeGridData=True,
                )
                .execute()
            )

            # ========================================================
            # معالجة نتيجة الـBatch
            # ========================================================

            for sheet in result.get("sheets", []):

                data = sheet.get("data", [])

                for grid in data:

                    start_row_index = grid.get(
                        "startRow",
                        current_row - 1,
                    )

                    start_column_index = grid.get(
                        "startColumn",
                        0,
                    )

                    for row_offset, row_data in enumerate(
                        grid.get("rowData", [])
                    ):

                        values = row_data.get(
                            "values",
                            [],
                        )

                        for col_offset, cell in enumerate(
                            values
                        ):

                            # ============================================================
                            # استخراج Drive Link:
                            # 1) Smart Chip
                            # 2) Hyperlink عادي
                            # ============================================================

                            link_items = []

                            # ------------------------------------------------------------
                            # 1. Smart Chip
                            # ------------------------------------------------------------

                            for chip_run in cell.get("chipRuns", []):

                                rich_link = (
                                    chip_run
                                    .get("chip", {})
                                    .get("richLinkProperties", {})
                                )

                                url = rich_link.get("uri")

                                if url:
                                    link_items.append({
                                        "url": url,
                                        "mime_type": rich_link.get("mimeType"),
                                    })

                            # ------------------------------------------------------------
                            # 2. Hyperlink عادي
                            # ------------------------------------------------------------

                            if not link_items:

                                url = cell.get("hyperlink")

                                if not url:
                                    url = (
                                        cell.get("effectiveFormat", {})
                                        .get("textFormat", {})
                                        .get("link", {})
                                        .get("uri")
                                    )

                                if url:
                                    link_items.append({
                                        "url": url,
                                        "mime_type": None,
                                    })

                            # ------------------------------------------------------------
                            # معالجة الروابط
                            # ------------------------------------------------------------

                            for link_item in link_items:

                                url = link_item["url"]

                                value = (
                                    cell.get("formattedValue")
                                    or cell.get("effectiveValue", {})
                                    .get("stringValue")
                                    or ""
                                )

                                # --------------------------------------------------------
                                # استخراج File ID
                                # --------------------------------------------------------

                                file_id = None

                                patterns = [
                                    r"[?&]id=([^&]+)",
                                    r"/file/d/([^/]+)",
                                    r"/document/d/([^/]+)",
                                    r"/spreadsheets/d/([^/]+)",
                                ]

                                for pattern in patterns:

                                    match = re.search(
                                        pattern,
                                        url,
                                    )

                                    if match:
                                        file_id = match.group(1)
                                        break

                                # --------------------------------------------------------
                                # حفظ الرابط
                                # --------------------------------------------------------

                                links[
                                    (
                                        start_row_index + row_offset,
                                        start_column_index + col_offset,
                                    )
                                ] = {
                                    "name": value,
                                    "url": url,
                                    "file_id": file_id,
                                    "mime_type": link_item["mime_type"],
                                }

            # ========================================================
            # الانتقال للدفعة التالية
            # ========================================================

            current_row = batch_end + 1

        # ============================================================
        # النتيجة
        # ============================================================

        print(
            f"   ✅ Drive Smart Chips loaded: "
            f"{len(links)} links "
            f"from {total_rows} rows"
        )

        return links

    @classmethod
    def get_dataframe(cls, sheet_name, force_reload=False):
        cache_key = str(sheet_name)

        if force_reload:
            if cache_key in cls._cache:
                print(
                    f"🔄 Force reload for sheet {sheet_name} "
                    f"(was cached at "
                    f"{cls._cache_time.get(cache_key, 'unknown')})"
                )
                del cls._cache[cache_key]

            if cache_key in cls._cache_time:
                del cls._cache_time[cache_key]

            cls.get_spreadsheet(force_reload=True)

        if cache_key in cls._cache:
            print(
                f"✅ Using cached data for sheet {sheet_name}"
            )
            return cls._cache[cache_key].copy()

        print(
            f"📥 Fetching fresh data from Google Sheets: "
            f"{sheet_name}"
        )

        worksheet = cls.get_spreadsheet().worksheet(
            str(sheet_name)
        )

        data = worksheet.get_all_values()

        if not data:
            print(
                f"⚠️ Sheet {sheet_name} is empty"
            )
            return pd.DataFrame()

        print(f"RAW ROWS: {len(data)}")
        print(f"RAW ROW 0: {data[0]}")
        print(f"RAW ROW 1: {data[1]}")
        print(f"RAW ROW 2: {data[2]}")

        # Row 0 = الـ Headers الصحيحة
        headers = data[0]

        # Row 1 = Header قديم
        # Row 2 وما بعده = البيانات
        rows = data[2:]

        print(
            f"DATA ROWS AFTER SKIP: {len(rows)}"
        )
        print(
            f"FIRST DATA ROW: {rows[0]}"
        )

        dataframe = pd.DataFrame(
            rows,
            columns=headers,
        )

        dataframe = dataframe.replace(
            "",
            pd.NA,
        )

        dataframe = dataframe.dropna(
            how="all"
        )

        dataframe = dataframe.fillna("")

        dataframe = dataframe.reset_index(
            drop=True
        )

        cls._cache[cache_key] = dataframe

        cls._cache_time[cache_key] = (
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
        cls._cache_time.clear()
        cls._spreadsheet = None
        print("🗑️ Google Sheets cache cleared")