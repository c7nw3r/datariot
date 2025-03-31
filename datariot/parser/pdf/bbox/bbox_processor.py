import logging
import re
from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.__spi__ import BBoxConfig
from datariot.parser.pdf.bbox.__spi__ import BoundingBoxProcessor
from datariot.parser.pdf.pdf_model import PDFHyperlinkBox, PDFTextBox


class ReCropTextExtractionBBoxProcessor(BoundingBoxProcessor):
    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        processed = []
        for box in bboxes:
            if box.contains_hyperlinks:
                new_box = box
            else:
                crop = page.crop(tuple(box), strict=False)
                new_box = box.with_text(crop.extract_text())

            processed.append(new_box)

        return processed


class AnnotationBBoxProcessor(BoundingBoxProcessor):
    def __init__(self, config: BBoxConfig) -> None:
        self._config = config

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if self._config.handle_hyperlinks:
            try:
                hyperlinks = page.root_page.hyperlinks
            except Exception as ex:
                logging.warning(f"error while resolving hyperlinks on page {page.page_number}: {ex}")
                hyperlinks = []

            hyperlinks = [
                PDFHyperlinkBox.from_dict({**h, "page_number": page.page_number})
                for h in hyperlinks
            ]

            hyperlinks = [
                link
                for link in hyperlinks
                if not any(
                    re.match(p, link.uri)
                    for p in self._config.filter_hyperlink_patterns
                )
            ]

            for box in bboxes:
                for h in hyperlinks:
                    if box.is_corner_contained_in(h):
                        box.set_hyperlink(h.uri)
                        break

        return bboxes
