from typing import List

from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfplumber.page import Page

from datariot.parser.pdf.pdf_model import PdfTextBox
import pdfplumber

class CoordinatesBoundingBoxFilter:
    def __init__(self, min_y: float, max_y: float):
        self.min_y = min_y
        self.max_y = max_y

    def __call__(self, page: Page, bboxes: List[PdfTextBox]) -> List[PdfTextBox]:
        is_landscape = page.layout.width > page.layout.height

        def _filter(bbox):
            if is_landscape:
                return True

            expr1 = bbox.y1 <= self.max_y if self.max_y is not None else True
            expr2 = bbox.y1 >= self.min_y if self.min_y is not None else True

            return expr1 and expr2

        return [bbox for bbox in bboxes if _filter(bbox)]


class PDFOutlinesBoundingBoxFilter:

    def __init__(self, document: PDFDocument):
        try:
            self.outlines = list(document.get_outlines())
        except PDFNoOutlines:
            self.outlines = []

    def __call__(self, page: Page, bboxes: List[PdfTextBox]) -> List[PdfTextBox]:
        titles = [e for _, e, _, _, _ in self.outlines]

        def _filter(box: PdfTextBox):
            # FIXME
            if box.text.lower() == "inhaltsverzeichnis":
                return False

            if box.text[0].isdigit() and "....." in box.text:
                return False
            return True

        return list(filter(_filter, bboxes))
