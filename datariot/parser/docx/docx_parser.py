import logging
from typing import Iterator

from datariot.__spi__.error import DataRiotImportException, DataRiotException
from datariot.__spi__.type import Parsed, Parser
from datariot.parser.docx.docx_mixin import DocumentMixin
from datariot.util.io_util import get_files


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
        except:
            raise DataRiotException("error while opening docx file " + path)

        elements = [
            *self.parse_elements(document, document.sections[0].header),
            *self.parse_elements(document, document)
        ]

        return Parsed(path, elements)

    @staticmethod
    def parse_folder(path: str) -> Iterator[Parsed]:
        for file in get_files(path, ".docx"):
            try:
                yield DocxParser().parse(file)
            except DataRiotException as ex:
                logging.warning(ex)
