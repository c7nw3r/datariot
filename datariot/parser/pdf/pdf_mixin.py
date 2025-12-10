import logging
import sys
from typing import List, Tuple, Union
from uuid import uuid4

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
    WithAndSizeBoundingBoxFilter,
)
from datariot.parser.pdf.bbox.bbox_merger import (
    CoordinatesBoundingBoxMerger,
    GeometricImageSegmentsMerger,
)
from datariot.parser.pdf.bbox.bbox_processor import (
    AnnotationBBoxProcessor,
    ReCropTextExtractionBBoxProcessor,
)
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

        tables = self.get_table_boxes(document, page, config)
        texts = self.get_text_boxes(
            document, page.filter(self.not_within_bboxes(tables)), config
        )
        images, ocr_texts = self.get_image_boxes(document, page, config)
        linecurves = self.get_linecurve_boxes(
            document, page.filter(self.not_within_bboxes(tables, margin=2)), config
        )

        images = self.get_merged_image_boxes(
            page, images + linecurves, config.bbox_config
        )

        boxes = tables + texts + ocr_texts + images
        boxes = box_sorter(page, boxes)

        return boxes

    def get_text_boxes(
        self, document: PDFDocument, page: Page, config: PDFParserConfig
    ) -> List[PDFTextBox]:
        bbox_config = config.bbox_config
        box_filter = WithAndSizeBoundingBoxFilter(bbox_config)
        box_merger = CoordinatesBoundingBoxMerger(bbox_config)
        box_slicer = ColumnStyleBoundingBoxSlicer(bbox_config)
        pos_filter = CoordinatesBoundingBoxFilter(bbox_config)
        txt_filter = TextContentBoundingBoxFilter(bbox_config)
        toc_filter = PDFOutlinesBoundingBoxFilter(document)
        annotation_processor = AnnotationBBoxProcessor(bbox_config)

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
        boxes = annotation_processor(page, boxes)
        boxes = box_filter(page, boxes)
        boxes = box_merger(page, boxes)
        boxes = box_slicer(page, boxes)
        boxes = toc_filter(page, boxes)
        boxes = pos_filter(page, boxes)
        boxes = txt_filter(page, boxes)

        for box in boxes:
            box.clean()

        if config.bbox_config.text_box_config.extraction_strategy == "re_crop":
            re_crop = ReCropTextExtractionBBoxProcessor()
            boxes = re_crop(page, boxes)

        return boxes

    def get_table_boxes(
        self, _document: PDFDocument, page: Page, config: PDFParserConfig
    ) -> List[PDFTableBox]:
        box_filter = NestedTableBoundingBoxFilter()
        table_config = config.bbox_config.table_box_config
        ts = {
            "vertical_strategy": table_config.vertical_strategy,
            "horizontal_strategy": table_config.horizontal_strategy,
        }

        kwargs = {"strict": True} if sys.version_info >= (3, 10) else {}

        boxes = [
            PDFTableBox(page, e)
            for e in zip(page.find_tables(ts), page.extract_tables(ts), **kwargs)
        ]
        boxes = [e for e in boxes if len(e) > 1]
        boxes = box_filter(page, boxes)

        return boxes

    def get_image_boxes(
        self, document: PDFDocument, page: Page, config: PDFParserConfig
    ) -> Tuple[List[PDFImageBox], List[PDFTextBox]]:
        if not config.include_images:
            return [], []

        identity_filter = BoxIdentityBoundingBoxFilter()
        size_filter = BoxSizeBoundingBoxFilter(config.bbox_config.image_filter_box_size)

        images = page.images
        img_boxes: List[PDFImageBox] = []
        for img in images:
            id_ = str(uuid4()) if config.bbox_config.media_use_uuid else None
            img_boxes.append(PDFImageBox(page, img, id_))

        img_boxes = size_filter(page, img_boxes)
        img_boxes = identity_filter(page, img_boxes)

        # TODO: only ocr full page images, i.e., scans
        text_boxes: List[PDFTextBox] = []
        if config.ocr:
            keep_img_boxes = []
            for box in img_boxes:
                ocr_boxes = self.get_text_boxes_by_ocr(
                    document, page, box, config.bbox_config
                )
                if not ocr_boxes or config.bbox_config.ocr_config.keep_image_box:
                    keep_img_boxes.append(box)

                text_boxes.extend(ocr_boxes)

            img_boxes = keep_img_boxes

        return img_boxes, text_boxes

    def get_linecurve_boxes(
        self, document: PDFDocument, page: Page, config: PDFParserConfig
    ) -> List[PDFLineCurveBox]:
        elements = page.lines
        elements.extend(page.rects)
        elements.extend(page.curves)
        elements = [e for e in elements if abs(int(e["x0"]) - int(e["x1"])) > 0]
        elements = [e for e in elements if abs(int(e["top"]) - int(e["bottom"])) > 0]

        boxes = [PDFLineCurveBox(page, e) for e in elements]
        boxes = [box for box in boxes if box.width >= 0]
        boxes = [box for box in boxes if box.height >= 0]

        return boxes

    def get_merged_image_boxes(
        self,
        page: Page,
        images: List[PDFImageBox],
        linecurves: List[PDFLineCurveBox],
        config: BBoxConfig,
    ) -> List[PDFImageBox]:
        if not config.line_curve_config.include_as_image_boxes and not images:
            return []

        geo_merger = GeometricImageSegmentsMerger(config)
        images = geo_merger(page, images + linecurves)

        if not config.line_curve_config.include_as_image_boxes:
            # Keep only merged images derived from image boxes
            anchors = [
                Box(
                    max(0, b.x1),
                    min(page.width, b.x2),
                    max(0, b.y1),
                    min(page.height, b.y2),
                )
                for b in images
            ]

            images = [
                bbox
                for bbox in images
                if any([anchor.is_contained_in(bbox) for anchor in anchors])
            ]

        identity_filter = BoxIdentityBoundingBoxFilter()
        size_filter = BoxSizeBoundingBoxFilter(config.image_filter_box_size)
        images = size_filter(page, images)
        images = identity_filter(page, images)

        return images

    def get_text_boxes_by_ocr(
        self,
        document: PDFDocument,
        page: Page,
        box: PDFImageBox,
        config: BBoxConfig,
    ) -> List[PDFTextBox]:
        import pytesseract

        if config.ocr_config.only_full_page:
            if (box.width < page.width - 20) and (box.height < page.height - 20):
                # smaller than either page width or height with 20 px margin
                return []

            if config.ocr_config.full_page_only_if_no_text:
                text = page.crop(tuple(box), strict=False).extract_text().strip()
                if text:
                    return []

        if config.ocr_config.strategy == "text":
            text = pytesseract.image_to_string(
                box.get_file()[1],
                lang="+".join(config.ocr_config.languages),
                config=config.ocr_config.tesseract_config,
            )

            # FIXME: determine font size and name
            return [
                PDFTextBox(
                    box.x1,
                    box.y1,
                    box.x2,
                    box.y2,
                    text,
                    font_size=-1,
                    font_name="",
                    page_number=box.page_number,
                )
            ]

        elif config.ocr_config.strategy == "data":
            box_merger = CoordinatesBoundingBoxMerger(config)
            box_filter = CoordinatesBoundingBoxFilter(config)
            box_sorter = CoordinatesBoundingBoxSorter(config)
            toc_filter = PDFOutlinesBoundingBoxFilter(document)

            dicts = pytesseract.image_to_data(
                box.get_file()[1],
                output_type=pytesseract.Output.DICT,
                lang="+".join(config.ocr_config.languages),
                config=config.ocr_config.tesseract_config,
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
                e
                for e in boxes
                if len(e.text.strip()) >= config.ocr_config.filter_box_min_chars
            ]

            return boxes
        else:
            raise ValueError(
                f"OCR strategy {config.ocr_config.strategy} is not defined."
            )

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

    def not_within_bboxes(self, bboxes: List[Box], margin: int = 0):
        def _not_within_bboxes(obj: dict):
            def obj_in_bbox(_bbox):
                v_mid = (obj["top"] + obj["bottom"]) / 2
                h_mid = (obj["x0"] + obj["x1"]) / 2
                return (
                    (h_mid >= _bbox.x1 - margin)
                    and (h_mid < _bbox.x2 + margin)
                    and (v_mid >= _bbox.y1 - margin)
                    and (v_mid < _bbox.y2 + margin)
                )

            return not any(obj_in_bbox(__bbox) for __bbox in bboxes)

        return _not_within_bboxes
