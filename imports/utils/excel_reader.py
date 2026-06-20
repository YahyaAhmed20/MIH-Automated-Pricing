import pandas as pd


class ExcelReader:

    @staticmethod
    def read_sheet(
        file_path,
        sheet_name
    ):
        return pd.read_excel(
            file_path,
            sheet_name=sheet_name
        )