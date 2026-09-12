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

# ✅ 1️⃣ أضف هذه الـimports أعلى الملف
import random
import time
import requests
from urllib.parse import quote
from google.auth.transport.requests import Request

from requests.exceptions import ConnectionError, ReadTimeout, Timeout
from gspread.exceptions import APIError

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    # ✅ تم إزالة scope drive.readonly لأننا نستخدم get_drive_service() للـ Drive
]


class GoogleSheetsService:

    _client = None
    _spreadsheet = None
    _cache = {}
    _cache_time = {}

    # ============================================================
    # Google Sheets resilience / data layout
    # ============================================================

    _api_credentials = None

    GOOGLE_API_TIMEOUT = 60
    MAX_READ_RETRIES = 4

    RETRYABLE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    # عدد الصفوف التي تسبق أول Data Row لكل Sheet
    #
    # 0 = Header فقط ثم البيانات
    # 1 = Header في Row 0 + البيانات من Row 1
    # 2 = Header في Row 0 + صف قديم/إضافي في Row 1
    #
    # Sheet 9 نحافظ على سلوكه الحالي مؤقتًا.
    DATA_START_ROWS = {
        "6": 2,
        "9": 2,
        "10": 2,
        "11": 2,
        "12": 2,
    }

    DEFAULT_DATA_START_ROW = 1

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

    # ✅ 3️⃣ أضف Method جديدة داخل GoogleSheetsService (قبل get_dataframe)
    @classmethod
    def _get_api_credentials(cls):
        """
        Get cached Google credentials for direct Sheets REST API calls.
        """
        if cls._api_credentials is None:
            cls._api_credentials = Credentials.from_service_account_file(
                settings.GOOGLE_SERVICE_ACCOUNT_FILE,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets.readonly",
                ],
            )

        if not cls._api_credentials.valid:
            cls._api_credentials.refresh(Request())

        return cls._api_credentials

    @classmethod
    def _read_values_direct_api(cls, sheet_name):
        """
        Read sheet values directly through Google Sheets Values API.

        This intentionally bypasses:
            gspread -> worksheet.get_all_values()

        because direct REST Values API was proven to be much faster
        on the APP spreadsheet.
        """

        credentials = cls._get_api_credentials()

        spreadsheet_id = settings.GOOGLE_SPREADSHEET_ID

        # Quote the sheet title safely for A1 notation.
        safe_sheet_name = str(sheet_name).replace("'", "''")
        range_name = f"'{safe_sheet_name}'"

        encoded_range = quote(
            range_name,
            safe="",
        )

        url = (
            f"https://sheets.googleapis.com/v4/spreadsheets/"
            f"{spreadsheet_id}/values/{encoded_range}"
        )

        last_error = None

        for attempt in range(1, cls.MAX_READ_RETRIES + 1):
            started = time.perf_counter()

            try:
                # Refresh token only when necessary.
                if not credentials.valid:
                    credentials.refresh(Request())

                response = requests.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {credentials.token}",
                    },
                    params={
                        "majorDimension": "ROWS",
                        "valueRenderOption": "FORMATTED_VALUE",
                    },
                    timeout=cls.GOOGLE_API_TIMEOUT,
                )

                elapsed = time.perf_counter() - started

                if response.status_code == 200:
                    payload = response.json()

                    print(
                        f"✅ Direct Google Values API read completed: "
                        f"{sheet_name} in {elapsed:.2f}s"
                    )

                    return payload.get("values", [])

                if response.status_code in cls.RETRYABLE_STATUS_CODES:
                    last_error = RuntimeError(
                        f"Google Sheets API HTTP {response.status_code}: "
                        f"{response.text[:500]}"
                    )

                    print(
                        f"⚠️ Google Sheets API temporary error on "
                        f"sheet {sheet_name}: HTTP "
                        f"{response.status_code} "
                        f"(attempt {attempt}/{cls.MAX_READ_RETRIES})"
                    )

                else:
                    response.raise_for_status()

            except (
                requests.exceptions.ReadTimeout,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError,
            ) as exc:

                last_error = exc

                print(
                    f"⚠️ Google Sheets API timeout/connection error "
                    f"on sheet {sheet_name} "
                    f"(attempt {attempt}/{cls.MAX_READ_RETRIES}): "
                    f"{exc}"
                )

            if attempt < cls.MAX_READ_RETRIES:
                delay = min(30, 2 ** attempt) + random.uniform(0, 1)

                print(
                    f"⏳ Retrying direct API read for "
                    f"{sheet_name} in {delay:.1f}s..."
                )

                time.sleep(delay)

        print(
            f"❌ Direct Google Values API read failed permanently: "
            f"{sheet_name}"
        )

        raise last_error

    # ✅ 4️⃣ أهم تعديل: get_dataframe() - استبدالها بالكامل
    @classmethod
    def get_dataframe(cls, sheet_name, force_reload=False):

        sheet_name = str(sheet_name)
        cache_key = sheet_name

        # ============================================================
        # Force Reload
        # ============================================================

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

        # ============================================================
        # Cache
        # ============================================================

        if cache_key in cls._cache:

            print(
                f"✅ Using cached data for sheet {sheet_name}"
            )

            return cls._cache[cache_key].copy()

        # ============================================================
        # Fresh Read
        # ============================================================

        print(
            f"📥 Fetching fresh data from Google Sheets API: "
            f"{sheet_name}"
        )

        # ============================================================
        # DIRECT GOOGLE VALUES API
        # ============================================================

        data = cls._read_values_direct_api(sheet_name)

        if not data:

            print(
                f"⚠️ Sheet {sheet_name} is empty"
            )

            return pd.DataFrame()

        # ============================================================
        # Header
        # ============================================================

        headers = data[0]

        # ============================================================
        # Determine first actual data row
        # ============================================================

        data_start_row = cls.DATA_START_ROWS.get(
            sheet_name,
            cls.DEFAULT_DATA_START_ROW,
        )

        rows = data[data_start_row:]

        print(
            f"📊 Sheet {sheet_name}: "
            f"{len(data)} raw rows"
        )

        print(
            "📌 Header row: 0"
        )

        print(
            f"📌 Data starts at raw row: "
            f"{data_start_row}"
        )

        print(
            f"📌 Data rows before cleanup: "
            f"{len(rows)}"
        )

        # ============================================================
        # Safety
        # ============================================================

        if not rows:

            print(
                f"⚠️ Sheet {sheet_name} has no data rows"
            )

            return pd.DataFrame(
                columns=headers
            )

        # ============================================================
        # DataFrame
        # ============================================================

        # Normalize row width to match the header width.
        # Some sheets contain extra side-data beyond the official headers.
        header_count = len(headers)

        normalized_rows = [
            row[:header_count] + [""] * max(0, header_count - len(row))
            for row in rows
        ]

        dataframe = pd.DataFrame(
            normalized_rows,
            columns=headers
        )

        # ============================================================
        # Restore Google Drive Smart Chip URLs
        # Sheet 12 only
        # ============================================================

        if sheet_name == "12":

            link_columns = {
                "New Reprt",
                "New Approval",
            }

            column_indexes = {
                column: headers.index(column)
                for column in link_columns
                if column in headers
            }

            if column_indexes:

                last_data_row = (
                    data_start_row
                    + len(dataframe)
                    - 1
                )

                drive_links = cls.get_drive_links(
                    sheet_name="12",
                    start_row=data_start_row + 1,
                    end_row=last_data_row + 1,
                    end_column="U",
                )

                for dataframe_index in range(
                    len(dataframe)
                ):

                    sheet_row_index = (
                        data_start_row
                        + dataframe_index
                    )

                    for column_name, column_index in column_indexes.items():

                        link = drive_links.get(
                            (
                                sheet_row_index,
                                column_index,
                            )
                        )

                        if link and link.get("url"):
                            dataframe.at[
                                dataframe_index,
                                column_name
                            ] = link["url"]

        dataframe = dataframe.replace(
            "",
            pd.NA,
        )

        dataframe = dataframe.dropna(
            how="all"
        )

        dataframe = dataframe.fillna(
            ""
        )

        dataframe = dataframe.reset_index(
            drop=True
        )

        # ============================================================
        # Cache
        # ============================================================

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