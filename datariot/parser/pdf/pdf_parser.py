import logging
import os
from typing import Iterator
from typing import Generator, Iterator

from datariot.__spi__.error import DataRiotException, DataRiotImportException
from datariot.__spi__.type import FileFilter, Parser
from datariot.__util__.io_util import get_files
from datariot.parser.pdf.__spi__ import ParsedPDF, ParsedPDFPage, PDFParserConfig
from datariot.parser.pdf.pdf_mixin import PageMixin


_DEFAULT_PARSER_CONFIG = PDFParserConfig()


class PDFParser(Parser, PageMixin):
    def __init__(self, config: PDFParserConfig = _DEFAULT_PARSER_CONFIG):
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

    def get_number_of_pages(self, path) -> int:
        import pdfplumber

        with pdfplumber.open(path) as reader:
            return len(reader.pages)

    def parse(self, path: str) -> ParsedPDF:
        import pdfplumber

        bboxes = []

        with pdfplumber.open(path) as reader:
            properties = reader.metadata
            for page in reader.pages:
                boxes = self.get_boxes(reader.doc, page, self.config)
                bboxes.extend(boxes)

                if self.config.screenshot:
                    self.take_screenshot(page, boxes)

        return ParsedPDF(path, bboxes, properties=properties)

    def parse_paged(self, path: str) -> Generator[ParsedPDFPage, None, None]:
        import pdfplumber

        with pdfplumber.open(path) as reader:
            properties = reader.metadata
            for page in reader.pages:
                boxes = self.get_boxes(reader.doc, page, self.config)

                if self.config.screenshot:
                    self.take_screenshot(page, boxes)

                yield ParsedPDFPage(path, boxes, properties=properties)
                page.flush_cache()
                # TODO: update pdfplumber where cache handling is improved by default
                # https://github.com/jsvine/pdfplumber/issues/193
                page.get_textmap.cache_clear()

    @staticmethod
    def parse_folder(
        path: str,
        config: PDFParserConfig = _DEFAULT_PARSER_CONFIG,
        file_filter: FileFilter = lambda _: True,
    ) -> Iterator[ParsedPDF]:
        parser = PDFParser(config)
        for file in get_files(path, ".pdf"):
            try:
                if file_filter(file):
                    yield parser.parse(file)
            except DataRiotException as ex:
                logging.warning(ex)
