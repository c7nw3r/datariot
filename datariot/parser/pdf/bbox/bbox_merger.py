from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.pdf_model import PDFTextBox


class CoordinatesBoundingBoxMerger:

    def __init__(self, x_tolerance: int = 10, y_tolerance: int = 10):
        self.x_tolerance = x_tolerance
        self.y_tolerance = y_tolerance

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if len(bboxes) == 0:
            return []

        results = []
        prev_bbox = bboxes[0].copy()
        for bbox in bboxes[1:]:
            is_same_line = abs(prev_bbox.y1 - bbox.y1) < 3

            expr1 = is_same_line and prev_bbox.x2 < bbox.x1 and (prev_bbox.x2 - bbox.x1) < self.x_tolerance
            expr2 = (bbox.y1 - prev_bbox.y2) < self.y_tolerance

            if expr1 or expr2:
                prev_bbox = prev_bbox.with_text(prev_bbox.text + (" " if is_same_line else "\n") + bbox.text)
                prev_bbox.x1 = min(prev_bbox.x1, bbox.x1)
                prev_bbox.y1 = min(prev_bbox.y1, bbox.y1)
                prev_bbox.x2 = max(prev_bbox.x2, bbox.x2)
                prev_bbox.y2 = max(prev_bbox.y2, bbox.y2)
            else:
                results.append(prev_bbox)
                prev_bbox = bbox.copy()

        if prev_bbox is not None:
            results.append(prev_bbox)

        return results
