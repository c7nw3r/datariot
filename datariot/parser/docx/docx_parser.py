import logging
from typing import Iterator

from datariot.__spi__.error import DataRiotImportException, DataRiotException
from datariot.__spi__.type import Parsed, Parser, FileFilter
from datariot.__util__.io_util import get_files
from datariot.parser.docx.docx_mixin import DocumentMixin


class DocxParser(Parser, DocumentMixin):

    def __init__(self):
        try:
            from docx import Document
        except ImportError:
            raise DataRiotImportException("docx")

    def parse(self, path: str):
        from docx import Document

        try:
            document = Document(path)
        except OSError:
            raise DataRiotException("error while opening docx file " + path)

        elements = [
            *self.parse_elements(document, document.sections[0].header),
            *self.parse_elements(document, document)
        ]

        properties = self.parse_custom_properties(path)
        return Parsed(path, elements, properties)

    @staticmethod
    def parse_folder(path: str, file_filter: FileFilter = lambda _: True) -> Iterator[Parsed]:
        for file in get_files(path, ".docx"):
            try:
                if file_filter(file):
                    yield DocxParser().parse(file)
            except DataRiotException as ex:
                logging.warning(ex)
