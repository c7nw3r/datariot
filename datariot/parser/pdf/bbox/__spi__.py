from abc import ABC, abstractmethod
from typing import List, TypeVar

from pdfplumber.page import Page

from datariot.__spi__.type import Box


B = TypeVar("B", bound=Box)


class BoundingBoxFilter(ABC):
    @abstractmethod
    def __call__(self, page: Page, bboxes: List[B]) -> List[B]:
        pass


class BoundingBoxProcessor(ABC):
    @abstractmethod
    def __call__(self, page: Page, bboxes: List[B]) -> List[B]:
        pass
