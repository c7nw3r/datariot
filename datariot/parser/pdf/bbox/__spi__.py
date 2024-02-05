from abc import ABC, abstractmethod
from typing import List

from pdfplumber.page import Page

from datariot.parser.pdf.pdf_model import PDFTextBox


class BoundingBoxFilter(ABC):

    @abstractmethod
    def __call__(self, page: Page, bboxes: List[PDFTextBox]) -> List[PDFTextBox]:
        pass
