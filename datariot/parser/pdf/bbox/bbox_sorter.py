from typing import List

from pdfplumber.page import Page
from datariot.parser.pdf.__spi__ import BBoxConfig

from datariot.parser.pdf.pdf_model import PDFTextBox
from datariot.util.array_util import flatten


class CoordinatesBoundingBoxSorter:

    def __init__(self, config: BBoxConfig):
        self._config = config

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if len(bboxes) == 0:
            return []

        if self._config.sorter_fuzzy:
            bboxes = self._sort_by_y(bboxes)

            lines = [[bboxes[0]]]
            for curr_box in bboxes[1:]:
                prev_box = lines[-1][-1]

                if abs(prev_box.y1 - curr_box.y1) <= self._config.sorter_y_tolerance:
                    lines[-1].append(curr_box)
                else:
                    lines[-1] = self._sort_by_x(lines[-1])
                    lines.append([curr_box])

            return flatten(lines)

        return self._sort_by_y(bboxes)

    def _sort_by_y(self, boxes: List[PDFTextBox]):
        return sorted(boxes, key=lambda x: (x.y1, x.x1))

    def _sort_by_x(self, boxes: List[PDFTextBox]):
        return sorted(boxes, key=lambda x: x.x1)
