from imports.utils.import_helpers import ImportHelpers


class SheetMapper:

    def __init__(
        self,
        dataframe,
        header_row=0,
        columns=None,
    ):
        self.dataframe = dataframe
        self.header_row = header_row
        self.columns = columns
        self.mapping = {}

        self._build_mapping()

    def _build_mapping(self):
        """
        بناء خريطة تربط أسماء الأعمدة بفهارسها.
        """
        if self.columns is not None:
            columns = self.columns
        else:
            columns = list(self.dataframe.columns)

        for index, column in enumerate(columns):
            column = ImportHelpers.normalize_text(column)

            if column in self.mapping:
                raise ValueError(
                    f"Duplicate column name found: {column}"
                )

            self.mapping[column] = index