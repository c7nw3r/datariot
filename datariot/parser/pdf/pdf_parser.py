import logging
from typing import Iterator

from datariot.__spi__.error import DataRiotImportException, DataRiotException
from datariot.__spi__.type import Parser, ParsedDocument
from datariot.parser.pdf.pdf_mixin import PageMixin
from datariot.util.io_util import get_filename, get_files


class PdfParser(Parser, PageMixin):

    def __init__(self, screenshot: bool = False):
        self.screenshot = screenshot

    def parse(self, path: str):
        try:
            import pdfplumber
        except ImportError:
            raise DataRiotImportException("pdf")

        bboxes = []
        reader = pdfplumber.open(path)

        outlines = list(reader.doc.get_outlines())

        for page in reader.pages:
            bboxes.extend(self.get_text_boxes(reader.doc, page))

            if self.screenshot:
                # TODO: reuse bboxes
                self.take_screenshot(page, self.get_text_boxes(reader.doc, page))

        return ParsedDocument(get_filename(path), bboxes)

    @staticmethod
    def parse_folder(path: str) -> Iterator[ParsedDocument]:
        for file in get_files(path, ".pdf"):
            try:
                yield PdfParser().parse(file)
            except DataRiotException as ex:
                logging.error(ex)
