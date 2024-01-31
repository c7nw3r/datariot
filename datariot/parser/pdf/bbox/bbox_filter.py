from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.pdf_model import PdfTextBox


class CoordinatesBoundingBoxFilter:
    def __init__(self, min_y: float, max_y: float):
        self.min_y = min_y
        self.max_y = max_y

    def __call__(self, page: Page, bboxes: List[PdfTextBox]) -> List[PdfTextBox]:
        def _filter(bbox):
            expr1 = bbox.y1 <= self.max_y if self.max_y is not None else True
            expr2 = bbox.y1 >= self.min_y if self.min_y is not None else True

            return expr1 and expr2

        return [bbox for bbox in bboxes if _filter(bbox)]
