from typing import List

from pdfplumber.page import Page
from datariot.parser.pdf.__spi__ import BBoxConfig

from datariot.parser.pdf.pdf_model import PDFTextBox


class CoordinatesBoundingBoxMerger:

    def __init__(self, config: BBoxConfig):
        self._config = config

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if len(bboxes) == 0:
            return []

        results = []
        prev_bbox = bboxes[0].copy()
        for bbox in bboxes[1:]:
            is_same_line = abs(prev_bbox.y2 - bbox.y2) <= self._config.merge_same_line_tolerance
            is_blank = bbox.text.strip() == ""

            # same font size
            expr1 = not self._config.merge_same_font_size or prev_bbox.font_size == bbox.font_size
            # same font name
            expr2 = not self._config.merge_same_font_name or prev_bbox.font_name == bbox.font_name
            # same font weight
            expr3 = not self._config.merge_same_font_weight or prev_bbox.font_weight == bbox.font_weight
            # always merge blanks or font based
            font_rule = (self._config.merge_blank_always and is_blank) or (expr1 and expr2 and expr3)
            # same line
            same_line_rule = (
                is_same_line
                and prev_bbox.x2 < bbox.x1
                and (bbox.x1 - prev_bbox.x2) < self._config.merge_x_tolerance
            )
            # consecutive lines
            consecutive_line_rule = (bbox.y1 - prev_bbox.y2) < self._config.merge_y_tolerance

            if font_rule and (same_line_rule or consecutive_line_rule):
                prev_is_blank = prev_bbox.text.strip() == ""
                prev_bbox = prev_bbox.with_text(prev_bbox.text + (" " if is_same_line else "\n") + bbox.text)
                if prev_is_blank:
                    prev_bbox.font_name = bbox.font_name
                    prev_bbox.font_size = bbox.font_size
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
