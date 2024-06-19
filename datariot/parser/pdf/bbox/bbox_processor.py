from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.bbox.__spi__ import BoundingBoxProcessor
from datariot.parser.pdf.pdf_model import PDFTextBox


class ReCropTextExtractionBBoxProcessor(BoundingBoxProcessor):
    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        processed = []
        for box in bboxes:
            crop = page.crop(tuple(box), strict=False)
            new_box = box.with_text(crop.extract_text())
            processed.append(new_box)

        return processed
