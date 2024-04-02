import re
from typing import List, TypeVar

from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfplumber.page import Page

from datariot.__spi__.type import Box
from datariot.parser.pdf.__spi__ import BBoxConfig
from datariot.parser.pdf.bbox.__spi__ import BoundingBoxFilter
from datariot.parser.pdf.pdf_model import PDFTextBox


class CoordinatesBoundingBoxFilter(BoundingBoxFilter):
    def __init__(self, config: BBoxConfig):
        self._config = config

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        is_landscape = page.layout.width > page.layout.height

        def _filter(bbox: PDFTextBox):
            if is_landscape:
                return True

            expr1 = bbox.y1 <= self._config.filter_max_y if self._config.filter_max_y is not None else True
            expr2 = bbox.y1 >= self._config.filter_min_y if self._config.filter_min_y is not None else True

            return expr1 and expr2

        return [b for b in bboxes if _filter(b)]


class PDFOutlinesBoundingBoxFilter(BoundingBoxFilter):

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

        return [b for b in bboxes if _filter(b)]


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

                # checking for boxes overlap
                expr1 = box1.x2 >= box2.x1
                expr2 = box2.x2 >= box1.x1
                expr3 = box1.y2 >= box2.y1
                expr4 = box2.y2 >= box1.y1

                if all([expr1, expr2, expr3, expr4]):
                    exclude = True

            if not exclude:
                result.append(box1)

        return result


class BoxIdentityBoundingBoxFilter:

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
            for j in range(i+1, len(bboxes)):
                box2 = bboxes[j]

                # checking for boxes identity
                expr1 = box1.x1 == box2.x1
                expr2 = box1.x2 == box2.x2
                expr3 = box1.y1 == box2.y1
                expr4 = box1.y2 == box2.y2

                if all([expr1, expr2, expr3, expr4]):
                    exclude = True

            if not exclude:
                result.append(box1)

        return result


class TextContentBoundingBoxFilter(BoundingBoxFilter):

    def __init__(self, config: BBoxConfig) -> None:
        self._config = config

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        def _filter(box: PDFTextBox):
            for regex in self._config.filter_must_regexes:
                if not re.search(regex.pattern, box.text, regex.flags):
                    return False

            for regex in self._config.filter_must_not_regexes:
                if re.search(regex.pattern, box.text, regex.flags):
                    return False

            return True

        return [b for b in bboxes if _filter(b)]
