from typing import List

from pdfminer.pdfdocument import PDFDocument
from pdfplumber.page import Page

from datariot.parser.pdf.bbox.bbox_filter import CoordinatesBoundingBoxFilter, PDFOutlinesBoundingBoxFilter
from datariot.parser.pdf.bbox.bbox_merger import CoordinatesBoundingBoxMerger
from datariot.parser.pdf.bbox.bbox_sorter import CoordinatesBoundingBoxSorter
from datariot.parser.pdf.pdf_model import PdfTextBox


class PageMixin:

    def get_text_boxes(self, document: PDFDocument, page: Page) -> List[PdfTextBox]:
        box_merger = CoordinatesBoundingBoxMerger()
        box_filter = CoordinatesBoundingBoxFilter(50, 710)
        box_sorter = CoordinatesBoundingBoxSorter()
        toc_filter = PDFOutlinesBoundingBoxFilter(document)

        boxes = page.extract_words(extra_attrs=["fontname", "size"])
        boxes = [PdfTextBox(word) for word in boxes]
        boxes = box_merger(page, boxes)
        boxes = toc_filter(page, boxes)
        boxes = box_filter(page, boxes)
        boxes = box_sorter(page, boxes)

        return boxes

    def take_screenshot(self, page: Page, bboxes: List[PdfTextBox]):
        image = page.to_image()
        for bbox in bboxes:
            color = (100, 100, 100)
            image.draw_rect((bbox.x1, bbox.y1, bbox.x2, bbox.y2), fill=color + (50,), stroke=color)
        image.save(f"./screenshot_{page.page_number}.jpg")
