from typing import List, Tuple

from pdfplumber.display import PageImage
from pdfplumber.page import CroppedPage, Page

from datariot.__spi__.type import ColumnPosition
from datariot.__util__.fonts import check_font_specs
from datariot.parser.__spi__ import DocumentFonts
from datariot.parser.pdf.__spi__ import BBoxConfig
from datariot.parser.pdf.bbox.bbox_merger import CoordinatesBoundingBoxMerger
from datariot.parser.pdf.pdf_model import PDFColumnTextBox, PDFTextBox


class ColumnStyleBoundingBoxSlicer:

    def __init__(self, config: BBoxConfig):
        self._config = config
        self._box_merger = CoordinatesBoundingBoxMerger(config)

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if not bboxes or not self._config.columns_split:
            return bboxes

        doc_fonts = DocumentFonts.from_bboxes(bboxes)
        results = []
        for bbox in bboxes:
            if (
                (bbox.x1 < page.width / 2 < bbox.x2)
                and len(bbox.text.splitlines()) >= self._config.columns_min_lines
                and check_font_specs(bbox, doc_fonts, self._config.columns_split_fonts)
            ):
                column_crops = self._get_two_column_crops(page, bbox)
                if not column_crops:
                    column_crops = self._get_three_column_crops(page, bbox)

                if column_crops:
                    for crop, num, col in column_crops:
                        # TODO: refactor to avoid code repetition from mixin
                        crop_bboxes = crop.extract_words(
                            extra_attrs=self._config.extract_words_extra_attrs,
                            keep_blank_chars=self._config.extract_words_keep_blank_chars
                        )
                        crop_bboxes = [
                            PDFTextBox.from_dict({**word, "page_number": page.page_number})
                            for word in crop_bboxes
                        ]
                        crop_bboxes = self._box_merger(page, crop_bboxes)
                        crop_bboxes = [PDFColumnTextBox.from_pdf_text_box(b, num, col) for b in crop_bboxes]
                        results.extend(crop_bboxes)

                    continue

            results.append(bbox)

        return results

    def _get_two_column_crops(self, page: Page, bbox: PDFTextBox) -> List[Tuple[CroppedPage, int, ColumnPosition]]:
        bbox_center_x = bbox.x1 + (bbox.x2 - bbox.x1) / 2
        gap = page.crop(
            (bbox_center_x-self._config.columns_gap, bbox.y1, bbox_center_x+self._config.columns_gap, bbox.y2),
            strict=False
        )
        if self._is_monochrome(gap.to_image()):
            crop_left = page.crop(
                (bbox.x1, bbox.y1, bbox_center_x, bbox.y2),
                strict=False
            )
            crop_right = page.crop(
                (bbox_center_x, bbox.y1, bbox.x2, bbox.y2),
                strict=False
            )

            return [(crop_left, 2, "left"), (crop_right, 2, "right")]

        return []

    def _get_three_column_crops(self, page: Page, bbox: PDFTextBox) -> List[Tuple[CroppedPage, int, ColumnPosition]]:
        bbox_col_x1 = bbox.x1 + (bbox.x2 - bbox.x1) / 3
        bbox_col_x2 = bbox.x1 + (bbox.x2 - bbox.x1) * 2 / 3
        gaps = [
            page.crop(
                (col_x-self._config.columns_gap, bbox.y1, col_x+self._config.columns_gap, bbox.y2),
                strict=False
            )
            for col_x in (bbox_col_x1, bbox_col_x2)
        ]

        if all(self._is_monochrome(gap.to_image()) for gap in gaps):
            crop_left = page.crop(
                (bbox.x1, bbox.y1, bbox_col_x1, bbox.y2),
                strict=False
            )
            crop_center = page.crop(
                (bbox_col_x1, bbox.y1, bbox_col_x2, bbox.y2),
                strict=False
            )
            crop_right = page.crop(
                (bbox_col_x2, bbox.y1, bbox.x2, bbox.y2),
                strict=False
            )

            return [(crop_left, 3, "left"), (crop_center, 3, "center"), (crop_right, 3, "right")]

        return []

    def _is_monochrome(self, img: PageImage) -> bool:
        _min, _max = img.original.convert("L").getextrema()
        return _min == _max
