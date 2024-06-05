from datariot.__spi__ import Formatter
from datariot.__spi__.type import T, Box
from datariot.parser.xlsx.__spi__ import XlsxParsed


class JSONXlsxFormatter(Formatter[dict]):

    def __init__(self, parsed: XlsxParsed):
        self.headers = parsed.header.values

    def __call__(self, box: Box) -> T:
        return {e[0].replace("\n", ""): e[1] for e in zip(self.headers, box.values)}


class TextXlsxFormatter(Formatter[dict]):

    def __init__(self, parsed: XlsxParsed):
        self.headers = parsed.header.values

    def __call__(self, box: Box) -> T:
        array = [
            *self.headers,
            box.values
        ]

        return {e[0].replace("\n", ""): e[1] for e in zip(self.headers, box.values)}
