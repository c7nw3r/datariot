from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.bbox.bbox_filter import CoordinatesBoundingBoxFilter
from datariot.parser.pdf.bbox.bbox_merger import CoordinatesBoundingBoxMerger
from datariot.parser.pdf.pdf_model import PdfTextBox


class PageMixin:

    def get_text_boxes(self, page: Page) -> List[PdfTextBox]:
        bbox_merger = CoordinatesBoundingBoxMerger()
        bbox_filter = CoordinatesBoundingBoxFilter(50, 710)

        bboxes = page.extract_words(extra_attrs=["fontname", "size"])
        bboxes = [PdfTextBox(word) for word in bboxes]
        bboxes = bbox_merger(page, bboxes)
        bboxes = bbox_filter(page, bboxes)

        return bboxes

    def take_screenshot(self, page: Page, bboxes: List[PdfTextBox]):
        image = page.to_image()
        for bbox in bboxes:
            color = (100, 100, 100)
            image.draw_rect((bbox.x1, bbox.y1, bbox.x2, bbox.y2), fill=color + (50,), stroke=color)
        image.save(f"./screenshot_{page.page_number}.jpg")
