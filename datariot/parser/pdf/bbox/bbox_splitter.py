from typing import List

import numpy as np
from pdfplumber.display import PageImage
from pdfplumber.page import Page

from datariot.parser.pdf.__spi__ import BBoxConfig
from datariot.parser.pdf.bbox.bbox_merger import CoordinatesBoundingBoxMerger
from datariot.parser.pdf.pdf_model import PDFTextBox


class ColumnLayoutBoundingBoxSplitter:

    def __init__(self, config: BBoxConfig):
        self._config = config
        self._box_merger = CoordinatesBoundingBoxMerger(config)

    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        if not bboxes or not self._config.columns_split:
            return bboxes

        results = []
        for bbox in bboxes:
            if bbox.x1 < page.width / 2 < bbox.x2:
                bbox_center_x = (bbox.x2 - bbox.x1) / 2
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

                    for crop in (crop_left, crop_right):
                        boxes = crop.extract_words(
                            extra_attrs=self._config.extract_words_extra_attrs,
                            keep_blank_chars=self._config.extract_words_keep_blank_chars
                        )
                        boxes = [PDFTextBox.from_dict(word) for word in boxes]
                        boxes = self._box_merger(page, boxes)
                        results.extend(boxes)
            else:
                results.append(bbox)

        return results

    def _is_monochrome(self, img: PageImage) -> bool:
        array = np.array(img.original.convert("RGB"))

        return np.sum(array == array[0, 0]) == array.size
