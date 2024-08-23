from datariot.__spi__ import Formatter
from datariot.parser.csv.csv_model import CsvTextBox


class TextFormatter(Formatter[str]):

    def __call__(self, box: 'Box') -> str:
        if isinstance(box, CsvTextBox):
            return box.text
        return str(box)
