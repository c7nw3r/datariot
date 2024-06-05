from datariot.__spi__.type import Box


class XlsxRowBox(Box):
    def __init__(self, row_cols):
        x1 = row_cols[0].row
        y1 = row_cols[0].column
        x2 = row_cols[-1].row
        y2 = row_cols[-1].column

        super().__init__(x1, x2, y1, y2)
        self.values = [e.value for e in row_cols]
