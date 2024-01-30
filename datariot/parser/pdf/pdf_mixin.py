from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.pdf_model import PdfTextBox


class PageMixin:

    def get_text_boxes(self, page: Page) -> List[PdfTextBox]:
        words = page.extract_words(extra_attrs=["fontname", "size"])

        if len(words) == 0:
            return []

        def to_bounding_box(row: dict) -> PdfTextBox:
            return PdfTextBox(x1=row["x0"], x2=row["x1"], y1=row["top"], y2=row["bottom"], text=row["text"],
                              font_size=row["size"] or -1, font_name=row["fontname"] or "unknown")

        return [to_bounding_box(word) for word in words]

    def take_screenshot(self, page: Page, bboxes: List[PdfTextBox]):
        image = page.to_image()
        for bbox in bboxes:
            color = (100, 100, 100)
            image.draw_rect((bbox.x1, bbox.y1, bbox.x2, bbox.y2), fill=color + (50,), stroke=color)
        image.save(f"./screenshot_{page.page_number}.jpg")
