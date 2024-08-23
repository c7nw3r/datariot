from dataclasses import dataclass

from datariot.__spi__.type import Box


@dataclass
class CsvLineBox(Box):
    """
    Box implementation for a csv line.
    """

    def __init__(self, row):
        super().__init__(None, None, None, None)
        self.row = row

    def __repr__(self):
        return "Row(" + ", ".join(self.row) + ")"


@dataclass
class CsvTextBox(Box):
    """
    Box implementation for a csv line.
    """

    def __init__(self, text):
        super().__init__(None, None, None, None)
        self.text = text

    def __repr__(self):
        return f"Row({self.text})"
