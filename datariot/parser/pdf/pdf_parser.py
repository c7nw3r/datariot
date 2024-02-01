import logging
from dataclasses import dataclass
from typing import Iterator

from datariot.__spi__.error import DataRiotImportException, DataRiotException
from datariot.__spi__.type import Parser, Parsed
from datariot.parser.pdf.pdf_mixin import PageMixin
from datariot.util.io_util import get_files


@dataclass
class Config:
    screenshot: bool = False
    ocr: bool = False


class PDFParser(Parser, PageMixin):

    def __init__(self, config: Config = Config()):
        self.config = config
        try:
            import pdfplumber
        except ImportError:
            raise DataRiotImportException("pdf")
        try:
            if config.ocr:
                import pytesseract
        except ImportError:
            raise DataRiotImportException("ocr")

    def parse(self, path: str):
        import pdfplumber

        bboxes = []
        reader = pdfplumber.open(path)

        for page in reader.pages:
            boxes = self.get_boxes(reader.doc, page)
            bboxes.extend(boxes)

            if self.config.screenshot:
                self.take_screenshot(page, boxes)

        return Parsed(path, bboxes)

    @staticmethod
    def parse_folder(path: str, config: Config = Config()) -> Iterator[Parsed]:
        for file in get_files(path, ".pdf"):
            try:
                yield PDFParser(config).parse(file)
            except DataRiotException as ex:
                logging.warning(ex)
