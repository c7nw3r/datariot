import logging
import os
from typing import Generator, Iterator

from datariot.__spi__.error import DataRiotException, DataRiotImportException
from datariot.__spi__.type import FileFilter, Parser
from datariot.__util__.io_util import get_files
from datariot.parser.pdf.__spi__ import ParsedPDF, ParsedPDFPage, PDFParserConfig, resilient
from datariot.parser.pdf.filter.metrics_collector import MetricsCollector
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

    @resilient
    def parse(self, path: str) -> ParsedPDF:
        import pdfplumber

        bboxes = []

        with pdfplumber.open(path) as reader:
            properties = {
                k: v
                for k, v
                in reader.metadata.items()
                if isinstance(v, str) or isinstance(v, int) or isinstance(v, float)
            }

            metrics = {}
            for page in reader.pages:
                if self.config.object_filter:
                    page = page.filter(self.config.object_filter)

                metrics_collector = MetricsCollector(page)
                page = page.filter(metrics_collector)

                boxes = self.get_boxes(reader.doc, page, self.config)
                bboxes.extend(boxes)

                metrics[page.page_number - 1] = {
                    "tags": metrics_collector.tags,
                    "stroking_colors": metrics_collector.stroking_color,
                    "overlapping_pixels": metrics_collector.overlapping_pixels
                }

                if self.config.screenshot:
                    self.take_screenshot(page, boxes)

            properties["num_pages"] = len(reader.pages)

        if "size" not in properties:
            properties["size"] = os.stat(path).st_size
        if "name" not in properties:
            properties["name"] = path[path.rfind("/") + 1:]

        return ParsedPDF(path, bboxes, properties=properties, metrics=metrics)

    @resilient
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
                if hasattr(page.get_textmap, "cache_clear"):
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
