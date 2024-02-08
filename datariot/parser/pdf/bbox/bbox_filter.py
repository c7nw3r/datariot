from typing import List

from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfplumber.page import Page

from datariot.__spi__.type import Box
from datariot.parser.pdf.pdf_model import PDFTextBox


class CoordinatesBoundingBoxFilter:
    def __init__(self, min_y: float, max_y: float):
        self.min_y = min_y
        self.max_y = max_y

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
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

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        def _filter(box: PDFTextBox):
            if box.text[0].isdigit() and "....." in box.text:
                return False
            return True

        return list(filter(_filter, bboxes))


from typing import List, TypeVar

T = TypeVar('T')


class BoxOverlapsBoundingBoxFilter:

    def __call__(self, page: Page, bboxes: List[T]) -> List[T]:
        if len(bboxes) == 0:
            return []

        def by_size(_box: Box):
            w = _box.x2 - _box.x1
            h = _box.y2 - _box.y1
            return w * h

        bboxes = list(reversed(sorted(bboxes, key=by_size)))
        result = []

        for i in range(len(bboxes)):
            box1 = bboxes[i]
            exclude = False
            for j in range(len(bboxes)):
                if i == j:
                    continue

                box2 = bboxes[j]

                expr1 = box2.x1 <= box1.x1
                expr2 = box2.y1 <= box1.y1
                expr3 = box2.x2 >= box1.x2
                expr4 = box2.y2 >= box1.y2

                if all([expr1, expr2, expr3, expr4]):
                    exclude = True

            if not exclude:
                result.append(box1)

        return result
