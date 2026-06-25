import pandas as pd


class ExcelReader:

    @staticmethod
    def read_sheet(
        file_path,
        sheet_name
    ):

        dataframe = pd.read_excel(
            file_path,
            sheet_name=sheet_name
        )

        # ============================================================
        # ✅ تنظيف أسماء الأعمدة
        # ============================================================
        dataframe.columns = (
            dataframe.columns
            .astype(str)
            .str.strip()
        )

        return dataframe