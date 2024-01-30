from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.pdf_model import PdfTextBox


class PageMixin:

    def get_text_boxes(self, page: Page) -> List[PdfTextBox]:
        words = page.extract_words(extra_attrs=["fontname", "size"])

        if len(words) == 0:
            return []

        return [PdfTextBox(word) for word in words]

    def take_screenshot(self, page: Page, bboxes: List[PdfTextBox]):
        image = page.to_image()
        for bbox in bboxes:
            color = (100, 100, 100)
            image.draw_rect((bbox.x1, bbox.y1, bbox.x2, bbox.y2), fill=color + (50,), stroke=color)
        image.save(f"./screenshot_{page.page_number}.jpg")
