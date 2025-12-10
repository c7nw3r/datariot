from math import ceil
from typing import List, Union

from pdfplumber.page import Page

from datariot.__spi__.type import Box
from datariot.__util__.geometric_util import calculate_bounding_boxes
from datariot.parser.__spi__ import DocumentFonts
from datariot.parser.pdf.__spi__ import BBoxConfig
from datariot.parser.pdf.pdf_model import PDFImageBox, PDFLineCurveBox, PDFTextBox


class CoordinatesBoundingBoxMerger:
    def __init__(self, config: BBoxConfig):
        self._config = config

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if len(bboxes) == 0:
            return []

        doc_fonts = DocumentFonts.from_bboxes(bboxes)

        results: List[PDFTextBox] = []
        prev_bbox = bboxes[0].copy()
        for bbox in bboxes[1:]:
            is_same_line = (
                abs(prev_bbox.y2 - bbox.y2) <= self._config.merge_same_line_tolerance
            )
            is_blank = bbox.text.strip() == ""
            is_single_char = len(bbox.text.strip()) == 1
            is_prev_blank = prev_bbox.text.strip() == ""
            is_previous_most_common_font_size = (
                not is_prev_blank and prev_bbox.font_size == doc_fonts.most_common_size
            )
            has_link = bbox.last_hyperlink is not None
            is_same_link = prev_bbox.last_hyperlink == bbox.last_hyperlink
            continue_link = has_link and is_same_link

            # same font size
            expr1 = (
                not self._config.merge_same_font_size
                or prev_bbox.font_size == bbox.font_size
            )
            # same font name
            expr2 = (
                not self._config.merge_same_font_name
                or prev_bbox.font_name == bbox.font_name
            )
            # same font weight
            expr3 = (
                not self._config.merge_same_font_weight
                or prev_bbox.font_weight == bbox.font_weight
            )
            # always merge blanks, single chars, same line most common or font based
            font_rule = (
                (self._config.merge_blank_always and is_blank)
                or (self._config.merge_single_char_always and is_single_char)
                or (
                    self._config.merge_same_line_always_after_most_common
                    and is_previous_most_common_font_size
                    and is_same_line
                )
                or (expr1 and expr2 and expr3)
            )
            # same line
            same_line_rule = (
                is_same_line
                and prev_bbox.x2 < bbox.x1
                and (bbox.x1 - prev_bbox.x2) < self._config.merge_x_tolerance
            )
            # consecutive lines
            consecutive_line_rule = (
                self._config.merge_blank_consecutive_lines or not is_blank
            ) and (bbox.y1 - prev_bbox.y2) < self._config.merge_y_tolerance

            if continue_link or (
                font_rule and (same_line_rule or consecutive_line_rule)
            ):
                prev_is_blank = prev_bbox.text.strip() == ""
                separator = "" if continue_link else " " if is_same_line else "\n"
                prev_bbox = prev_bbox.with_text(prev_bbox.text + separator + bbox.text)
                if prev_is_blank:
                    prev_bbox.font_name = bbox.font_name
                    prev_bbox.font_size = bbox.font_size
                prev_bbox.x1 = min(prev_bbox.x1, bbox.x1)
                prev_bbox.y1 = min(prev_bbox.y1, bbox.y1)
                prev_bbox.x2 = max(prev_bbox.x2, bbox.x2)
                prev_bbox.y2 = max(prev_bbox.y2, bbox.y2)
                prev_bbox.add_hyperlinks(bbox.hyperlinks)
            else:
                results.append(prev_bbox)
                prev_bbox = bbox.copy()

        if prev_bbox is not None:
            results.append(prev_bbox)

        return results


class GeometricImageSegmentsMerger:
    def __init__(self, config: BBoxConfig):
        self.config = config

    def __call__(
        self, page: Page, bboxes: List[Union[PDFImageBox, PDFLineCurveBox]]
    ) -> List[Box]:
        if len(bboxes) == 0:
            return []

        import numpy as np

        roi = np.zeros((ceil(page.height), ceil(page.width)))
        height, width = roi.shape

        anchors = [
            Box(
                max(0, b.x1),
                min(width, b.x2),
                max(0, b.y1),
                min(height, b.y2),
            )
            for b in bboxes
            if isinstance(b, PDFImageBox)
        ]

        if len(anchors) == 0:
            return []

        for _ in range(self.config.merger_steps):
            for box in bboxes:
                y1 = max(0, box.y1 - self.config.merger_y_tolerance)
                y2 = min(height, box.y2 + self.config.merger_y_tolerance + 1)
                x1 = max(0, box.x1 - self.config.merger_x_tolerance)
                x2 = min(width, box.x2 + self.config.merger_x_tolerance + 1)

                roi[y1:y2, x1:x2] = 1

            bboxes = calculate_bounding_boxes(roi)
            bboxes = [
                PDFImageBox(
                    page,
                    {
                        "x0": e[0] - self.config.merger_x_tolerance,
                        "x1": e[1] + self.config.merger_x_tolerance,
                        "top": e[2] - self.config.merger_y_tolerance,
                        "bottom": e[3] + self.config.merger_y_tolerance,
                    },
                )
                for e in bboxes
            ]

        return [
            bbox
            for bbox in bboxes
            if any([anchor.is_contained_in(bbox) for anchor in anchors])
        ]
