import logging
from dataclasses import dataclass
from typing import Iterator

from datariot.__spi__.error import DataRiotImportException, DataRiotException
from datariot.__spi__.type import Parser, ParsedDocument
from datariot.parser.pdf.pdf_mixin import PageMixin
from datariot.util.io_util import get_filename, get_files


@dataclass
class Config:
    screenshot: bool = False
    ocr: bool = False


class PdfParser(Parser, PageMixin):

    def __init__(self, config: Config = Config()):
        self.config = config
        try:
            if config.ocr:
                import pytesseract
        except ImportError:
            raise DataRiotImportException("ocr")

    def parse(self, path: str):
        try:
            import pdfplumber
        except ImportError:
            raise DataRiotImportException("pdf")

        bboxes = []
        reader = pdfplumber.open(path)

        for page in reader.pages:
            boxes = self.get_boxes(reader.doc, page)
            bboxes.extend(boxes)

            if self.config.screenshot:
                self.take_screenshot(page, boxes)

        if len(bboxes) == 0 and self.config.ocr:
            pass

        return ParsedDocument(path, get_filename(path), bboxes)

    @staticmethod
    def parse_folder(path: str, config: Config = Config()) -> Iterator[ParsedDocument]:
        for file in get_files(path, ".pdf"):
            try:
                yield PdfParser(config).parse(file)
            except DataRiotException as ex:
                logging.warning(ex)
