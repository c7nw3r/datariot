from typing import List

from pdfminer.pdfdocument import PDFDocument
from pdfplumber.page import Page

from datariot.parser.pdf.bbox.bbox_filter import CoordinatesBoundingBoxFilter, PDFOutlinesBoundingBoxFilter, \
    BoxOverlapsBoundingBoxFilter
from datariot.parser.pdf.bbox.bbox_merger import CoordinatesBoundingBoxMerger
from datariot.parser.pdf.bbox.bbox_sorter import CoordinatesBoundingBoxSorter
from datariot.parser.pdf.pdf_model import PdfTextBox, PDFImageBox, PDFOcrBox
from datariot.util.array_util import flatten

LEFT = "left"
TOP = "top"
WIDTH = "width"
HEIGHT = "height"
TEXT = "text"

class PageMixin:

    def get_boxes(self, document: PDFDocument, page: Page):
        boxes = self.get_text_boxes(document, page)
        boxes = [*boxes, *self.get_image_boxes(document, page, use_ocr=len(boxes) == 0)]

        return boxes

    def get_text_boxes(self, document: PDFDocument, page: Page) -> List[PdfTextBox]:
        box_merger = CoordinatesBoundingBoxMerger()
        box_filter = CoordinatesBoundingBoxFilter(50, 710)
        box_sorter = CoordinatesBoundingBoxSorter()
        toc_filter = PDFOutlinesBoundingBoxFilter(document)

        boxes = page.extract_words(extra_attrs=["fontname", "size"])
        boxes = [PdfTextBox.from_dict(word) for word in boxes]
        boxes = box_merger(page, boxes)
        boxes = toc_filter(page, boxes)
        boxes = box_filter(page, boxes)
        boxes = box_sorter(page, boxes)

        return boxes

    def get_image_boxes(self, document: PDFDocument, page: Page, use_ocr: bool = False):
        box_filter = BoxOverlapsBoundingBoxFilter()

        boxes = page.images
        boxes = [PDFImageBox(page, e) for e in boxes]
        boxes = [box for box in boxes if box.width >= 300]
        boxes = [box for box in boxes if box.height >= 300]
        boxes = box_filter(page, boxes)

        if use_ocr:
            boxes = flatten([self.get_text_boxes_by_ocr(document, page, box) for box in boxes])

        return boxes

    def get_text_boxes_by_ocr(self, document: PDFDocument, page: Page, box: PDFImageBox):
        import pytesseract
        box_merger = CoordinatesBoundingBoxMerger()
        box_filter = CoordinatesBoundingBoxFilter(50, 710)
        box_sorter = CoordinatesBoundingBoxSorter()
        toc_filter = PDFOutlinesBoundingBoxFilter(document)

        # TODO: fix language
        dicts = pytesseract.image_to_data(box.data.original, output_type=pytesseract.Output.DICT, lang="deu")
        boxes = [PDFOcrBox.from_ocr(e) for e in zip(dicts[LEFT], dicts[TOP], dicts[WIDTH], dicts[HEIGHT], dicts[TEXT])]
        boxes = [e for e in boxes if len(e.text) > 0]
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
