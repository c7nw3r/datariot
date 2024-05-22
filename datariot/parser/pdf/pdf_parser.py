import logging
from typing import Iterator

from datariot.__spi__.error import DataRiotImportException, DataRiotException
from datariot.__spi__.type import Parser, FileFilter
from datariot.__util__.io_util import get_files
from datariot.parser.pdf.__spi__ import PDFParserConfig, ParsedPDF
from datariot.parser.pdf.pdf_mixin import PageMixin


class PDFParser(Parser, PageMixin):

    def __init__(self, config: PDFParserConfig = PDFParserConfig()):
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

        with pdfplumber.open(path) as reader:
            for page in reader.pages:
                boxes = self.get_boxes(reader.doc, page, self.config)
                bboxes.extend(boxes)

                if self.config.screenshot:
                    self.take_screenshot(page, boxes)

        return ParsedPDF(path, bboxes)

    @staticmethod
    def parse_folder(path: str,
                     config: PDFParserConfig = PDFParserConfig(),
                     file_filter: FileFilter = lambda _: True) -> Iterator[ParsedPDF]:
        for file in get_files(path, ".pdf"):
            try:
                if file_filter(file):
                    yield PDFParser(config).parse(file)
            except DataRiotException as ex:
                logging.warning(ex)
