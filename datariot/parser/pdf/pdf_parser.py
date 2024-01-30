import logging
from typing import Iterator

from datariot.__spi__.error import DataRiotImportException, DataRiotException
from datariot.__spi__.type import Parser, ParsedDocument
from datariot.parser.pdf.pdf_mixin import PageMixin
from datariot.util.io_util import get_filename, get_files


class PdfParser(Parser, PageMixin):

    def parse(self, path: str, **kwargs):
        try:
            import pdfplumber
        except ImportError:
            raise DataRiotImportException("pdf")

        bboxes = []
        reader = pdfplumber.open(path)
        for page in reader.pages:
            bboxes.extend(self.get_text_boxes(page))

            if kwargs.get("screenshot"):
                self.take_screenshot(page, self.get_text_boxes(page))

        return ParsedDocument(get_filename(path), bboxes)

    @staticmethod
    def parse_folder(path: str) -> Iterator[ParsedDocument]:
        for file in get_files(path, ".pdf"):
            try:
                yield PdfParser().parse(file)
            except DataRiotException as ex:
                logging.error(ex)
