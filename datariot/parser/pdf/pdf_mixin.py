import logging
from typing import List

from pdfminer.pdfdocument import PDFDocument
from pdfplumber.page import Page

from datariot.__spi__.const import HEIGHT, LEFT, TEXT, TOP, WIDTH
from datariot.__spi__.type import Box
from datariot.parser.pdf.__spi__ import BBoxConfig, PDFParserConfig
from datariot.parser.pdf.bbox.bbox_filter import (
    BoxIdentityBoundingBoxFilter,
    BoxSizeBoundingBoxFilter,
    CoordinatesBoundingBoxFilter,
    NestedTableBoundingBoxFilter,
    PDFOutlinesBoundingBoxFilter,
    TextContentBoundingBoxFilter,
)
from datariot.parser.pdf.bbox.bbox_merger import CoordinatesBoundingBoxMerger
from datariot.parser.pdf.bbox.bbox_slicer import ColumnStyleBoundingBoxSlicer
from datariot.parser.pdf.bbox.bbox_sorter import CoordinatesBoundingBoxSorter
from datariot.parser.pdf.pdf_model import (
    PDFImageBox,
    PDFLineCurveBox,
    PDFOcrBox,
    PDFTableBox,
    PDFTextBox,
)


# noinspection PyMethodMayBeStatic
class PageMixin:
    def get_boxes(self, document: PDFDocument, page: Page, config: PDFParserConfig):
        box_sorter = CoordinatesBoundingBoxSorter(config.bbox_config)

        boxes = []
        boxes.extend(self.get_table_boxes(document, page, config))
        boxes.extend(
            self.get_text_boxes(
                document, page.filter(self.not_within_bboxes(boxes)), config.bbox_config
            )
        )
        boxes.extend(self.get_image_boxes(document, page, config))
        boxes.extend(self.get_linecurve_boxes(document, page, config))
        boxes = box_sorter(page, boxes)

        return boxes

    def get_text_boxes(
        self, document: PDFDocument, page: Page, config: PDFParserConfig
    ) -> List[PDFTextBox]:
        bbox_config = config.bbox_config
        box_merger = CoordinatesBoundingBoxMerger(bbox_config)
        box_slicer = ColumnStyleBoundingBoxSlicer(bbox_config)
        pos_filter = CoordinatesBoundingBoxFilter(bbox_config)
        txt_filter = TextContentBoundingBoxFilter(bbox_config)
        toc_filter = PDFOutlinesBoundingBoxFilter(document)
        # geo_merger = GeometricImageSegmentsMerger(config)

        words = page.extract_words(
            extra_attrs=bbox_config.extract_words_extra_attrs,
            keep_blank_chars=bbox_config.extract_words_keep_blank_chars,
            x_tolerance=bbox_config.parser_x_tolerance,
            y_tolerance=bbox_config.parser_y_tolerance,
        )
        boxes = [
            PDFTextBox.from_dict({**word, "page_number": page.page_number})
            for word in words
        ]
        boxes = [e for e in boxes if len(e.text.strip()) > 0]
        boxes = box_merger(page, boxes)
        boxes = box_slicer(page, boxes)
        boxes = toc_filter(page, boxes)
        boxes = pos_filter(page, boxes)
        boxes = txt_filter(page, boxes)
        # boxes = geo_merger(page, boxes)

        return boxes

    def get_table_boxes(
        self, _document: PDFDocument, page: Page, config: PDFParserConfig
    ):
        box_filter = NestedTableBoundingBoxFilter()

        ts = {
            "vertical_strategy": config.bbox_config.table_vertical_strategy,
            "horizontal_strategy": config.bbox_config.table_horizontal_strategy,
        }
        boxes = [
            PDFTableBox(page, e)
            for e in zip(page.find_tables(ts), page.extract_tables(ts))
        ]
        boxes = [e for e in boxes if len(e) > 1]
        boxes = box_filter(page, boxes)

        return boxes

    def get_image_boxes(
        self, document: PDFDocument, page: Page, config: PDFParserConfig
    ):
        identity_filter = BoxIdentityBoundingBoxFilter()
        size_filter = BoxSizeBoundingBoxFilter(config.bbox_config.image_filter_box_size)

        images = page.images
        img_boxes = [PDFImageBox(page, e) for e in images]

        img_boxes = size_filter(page, img_boxes)
        img_boxes = identity_filter(page, img_boxes)

        boxes = img_boxes
        # TODO: only ocr full page images, i.e., scans
        if config.ocr:
            boxes = []
            for box in img_boxes:
                boxes.extend(
                    self.get_text_boxes_by_ocr(document, page, box, config.bbox_config)
                )
                if config.bbox_config.ocr_keep_image_box:
                    boxes.append(box)

        return boxes

    def get_linecurve_boxes(
        self, document: PDFDocument, page: Page, config: PDFParserConfig
    ):
        box_filter = BoxIdentityBoundingBoxFilter()

        elements = page.lines
        elements.extend(page.rects)
        elements.extend(page.curves)
        elements = [e for e in elements if abs(int(e["x0"]) - int(e["x1"])) > 0]
        elements = [e for e in elements if abs(int(e["top"]) - int(e["bottom"])) > 0]

        boxes = [PDFLineCurveBox(page, e) for e in elements]
        boxes = [box for box in boxes if box.width >= 0]
        boxes = [box for box in boxes if box.height >= 0]
        boxes = box_filter(page, boxes)

        # TODO: merge linecurve boxes that are close

        return boxes

    def get_text_boxes_by_ocr(
        self,
        document: PDFDocument,
        page: Page,
        box: PDFImageBox,
        config: BBoxConfig,
    ):
        import pytesseract

        box_merger = CoordinatesBoundingBoxMerger(config)
        box_filter = CoordinatesBoundingBoxFilter(config)
        box_sorter = CoordinatesBoundingBoxSorter(config)
        toc_filter = PDFOutlinesBoundingBoxFilter(document)

        dicts = pytesseract.image_to_data(
            box.get_file()[1],
            output_type=pytesseract.Output.DICT,
            lang="+".join(config.ocr_tesseract_languages),
            config=config.ocr_tesseract_config,
        )
        ocr_boxes = zip(
            dicts[LEFT],
            dicts[TOP],
            dicts[WIDTH],
            dicts[HEIGHT],
            dicts[TEXT],
            [page.page_number] * len(dicts[LEFT]),
            strict=True,
        )

        boxes = [PDFOcrBox.from_ocr(e) for e in ocr_boxes]
        boxes = [e for e in boxes if len(e.text) > 0]
        boxes = box_sorter(page, boxes)
        boxes = box_merger(page, boxes)
        boxes = toc_filter(page, boxes)
        boxes = box_filter(page, boxes)
        boxes = [
            e for e in boxes if len(e.text.strip()) > config.ocr_filter_box_min_chars
        ]

        return boxes

    def take_screenshot(self, page: Page, bboxes: List[Box]):
        try:
            image = page.to_image()
            for bbox in bboxes:
                color = (100, 100, 100)
                image.draw_rect(
                    (bbox.x1, bbox.y1, bbox.x2, bbox.y2),
                    fill=color + (50,),
                    stroke=color,
                )
            image.save(f"./screenshot_{page.page_number}.jpg")
        except ValueError as ex:
            logging.warning(ex)

    def not_within_bboxes(self, bboxes: List[Box]):
        def _not_within_bboxes(obj: dict):
            def obj_in_bbox(_bbox):
                v_mid = (obj["top"] + obj["bottom"]) / 2
                h_mid = (obj["x0"] + obj["x1"]) / 2
                return (
                    (h_mid >= _bbox.x1)
                    and (h_mid < _bbox.x2)
                    and (v_mid >= _bbox.y1)
                    and (v_mid < _bbox.y2)
                )

            return not any(obj_in_bbox(__bbox) for __bbox in bboxes)

        return _not_within_bboxes
