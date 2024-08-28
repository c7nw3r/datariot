from typing import List

from pdfplumber.page import Page

from datariot.__spi__.type import Box
from datariot.parser.__spi__ import DocumentFonts
from datariot.parser.pdf.__spi__ import BBoxConfig
from datariot.parser.pdf.pdf_model import PDFHyperlinkBox, PDFTextBox


class CoordinatesBoundingBoxMerger:
    def __init__(self, config: BBoxConfig):
        self._config = config

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if len(bboxes) == 0:
            return []

        doc_fonts = DocumentFonts.from_bboxes(bboxes)

        results = []
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
            prev_has_link = prev_bbox.hyperlink is not None
            has_link = bbox.hyperlink is not None
            is_same_link = prev_bbox.hyperlink == bbox.hyperlink
            continue_link = has_link and is_same_link
            start_link = has_link and not is_same_link
            end_link = (not has_link or start_link) and prev_has_link

            if start_link:
                bbox = bbox.with_text(f"[{bbox.text}")
            if end_link:
                prev_bbox = prev_bbox.with_text(
                    f"{prev_bbox.text}]({prev_bbox.hyperlink})"
                )

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

            if font_rule and (same_line_rule or consecutive_line_rule):
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
                prev_bbox.hyperlink = bbox.hyperlink
            else:
                results.append(prev_bbox)
                prev_bbox = bbox.copy()

        if prev_bbox is not None:
            results.append(prev_bbox)

        return results


class GeometricImageSegmentsMerger:
    def __init__(self, config: BBoxConfig):
        self._config = config

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if len(bboxes) == 0:
            return []

        c_boxes = [Box.from_dict(e) for e in page.curves]
        l_boxes = [Box.from_dict(e) for e in page.lines]

        # for text_box in bboxes:
        #     for curve_box in c_boxes:
        #         if curve_box.intersect(text_box):
        #             print("intersect curve")

        # for text_box in bboxes:
        #     for line_box in l_boxes:
        #         if line_box.intersect(text_box):
        #             print("intersect line")
        #             text_box = self._extend(text_box, line_box)

        return bboxes
