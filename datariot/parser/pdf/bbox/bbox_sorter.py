from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.pdf_model import PdfTextBox


class CoordinatesBoundingBoxSorter:

    def __call__(self, page: Page, bboxes: List[PdfTextBox]) -> List[PdfTextBox]:
        return list(reversed(sorted(bboxes, key=lambda x: x.y1, reverse=True)))
