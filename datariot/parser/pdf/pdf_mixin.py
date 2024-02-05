import logging
from typing import List

from pdfminer.pdfdocument import PDFDocument
from pdfplumber.page import Page

from datariot.__spi__.type import Box
from datariot.parser.pdf.__spi__ import BBoxConfig
from datariot.parser.pdf.bbox.bbox_filter import (
    BoxOverlapsBoundingBoxFilter,
    ContentBoundingBoxFilter,
    CoordinatesBoundingBoxFilter,
    PDFOutlinesBoundingBoxFilter,
)
from datariot.parser.pdf.bbox.bbox_merger import CoordinatesBoundingBoxMerger
from datariot.parser.pdf.bbox.bbox_sorter import CoordinatesBoundingBoxSorter
from datariot.parser.pdf.bbox.bbox_splitter import ColumnLayoutBoundingBoxSplitter
from datariot.parser.pdf.pdf_model import PDFImageBox, PDFOcrBox, PDFTableBox, PDFTextBox
from datariot.util.array_util import flatten


LEFT = "left"
TOP = "top"
WIDTH = "width"
HEIGHT = "height"
TEXT = "text"


class PageMixin:

    def get_boxes(self, document: PDFDocument, page: Page, config: BBoxConfig):
        box_sorter = CoordinatesBoundingBoxSorter()

        boxes = []
        boxes.extend(self.get_table_boxes(document, page))
        boxes.extend(self.get_text_boxes(document, page.filter(self.not_within_bboxes(boxes)), config))
        boxes.extend(self.get_image_boxes(document, page, use_ocr=len(boxes) == 0))
        boxes = box_sorter(page, boxes)

        return boxes

    def get_text_boxes(self, document: PDFDocument, page: Page, config: BBoxConfig) -> List[PDFTextBox]:
        box_merger = CoordinatesBoundingBoxMerger(config)
        box_splitter = ColumnLayoutBoundingBoxSplitter(config)
        box_filter = CoordinatesBoundingBoxFilter(config)
        content_filter = ContentBoundingBoxFilter(config)
        toc_filter = PDFOutlinesBoundingBoxFilter(document)

        boxes = page.extract_words(
            extra_attrs=config.extract_words_extra_attrs,
            keep_blank_chars=config.extract_words_keep_blank_chars
        )
        boxes = [PDFTextBox.from_dict(word) for word in boxes]
        boxes = box_merger(page, boxes)
        boxes = box_splitter(page, boxes)
        boxes = toc_filter(page, boxes)
        boxes = box_filter(page, boxes)
        boxes = content_filter(page, boxes)

        return boxes

    def get_table_boxes(self, _document: PDFDocument, page: Page):
        ts = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}
        return [PDFTableBox(page, e) for e in zip(page.find_tables(ts), page.extract_tables(ts))]

    def get_image_boxes(self, document: PDFDocument, page: Page, use_ocr: bool = False):
        box_filter = BoxOverlapsBoundingBoxFilter()

        boxes = page.images
        boxes = [e for e in boxes if abs(int(e["x0"]) - int(e["x1"])) > 0]
        boxes = [e for e in boxes if abs(int(e["top"]) - int(e["bottom"])) > 0]
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
        box_sorter = CoordinatesBoundingBoxSorter(fuzzy=True)
        toc_filter = PDFOutlinesBoundingBoxFilter(document)

        # TODO: fix language
        dicts = pytesseract.image_to_data(box.data.original, output_type=pytesseract.Output.DICT, lang="deu")
        boxes = [PDFOcrBox.from_ocr(e) for e in zip(dicts[LEFT], dicts[TOP], dicts[WIDTH], dicts[HEIGHT], dicts[TEXT])]
        boxes = [e for e in boxes if len(e.text) > 0]
        boxes = box_sorter(page, boxes)
        boxes = box_merger(page, boxes)
        boxes = toc_filter(page, boxes)
        boxes = box_filter(page, boxes)

        return boxes

    def take_screenshot(self, page: Page, bboxes: List[PDFTextBox]):
        try:
            image = page.to_image()
            for bbox in bboxes:
                color = (100, 100, 100)
                image.draw_rect((bbox.x1, bbox.y1, bbox.x2, bbox.y2), fill=color + (50,), stroke=color)
            image.save(f"./screenshot_{page.page_number}.jpg")
        except ValueError as ex:
            logging.warning(ex)

    def not_within_bboxes(self, bboxes: List[Box]):
        def _not_within_bboxes(obj: dict):
            def obj_in_bbox(_bbox):
                v_mid = (obj["top"] + obj["bottom"]) / 2
                h_mid = (obj["x0"] + obj["x1"]) / 2
                return (h_mid >= _bbox.x1) and (h_mid < _bbox.x2) and (v_mid >= _bbox.y1) and (v_mid < _bbox.y2)

            return not any(obj_in_bbox(__bbox) for __bbox in bboxes)

        return _not_within_bboxes
