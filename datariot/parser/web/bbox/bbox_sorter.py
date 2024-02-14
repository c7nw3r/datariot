from typing import List

from datariot.parser.pdf.pdf_model import PDFTextBox


class CoordinatesBoundingBoxSorter:

    def __call__(self, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if len(bboxes) == 0:
            return []
        return list(reversed(sorted(bboxes, key=lambda x: x.y1, reverse=True)))
