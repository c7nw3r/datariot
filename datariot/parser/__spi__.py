import re
from dataclasses import dataclass
from functools import cached_property
from typing import List, Literal, Optional, Union

from datariot.parser.pdf.pdf_model import PDFTextBox


@dataclass
class RegexPattern:
    pattern: str
    flags: re.RegexFlag = 0


@dataclass
class Font:
    name: Optional[str] = None
    _size: Optional[int] = None
    weight: Optional[str] = None

    @property
    def size(self) -> int:
        return self._size

    @size.setter
    def size(self, value: float):
        self._size = round(value)


@dataclass
class DocumentFonts:
    _fonts: Optional[List[Font]] = None

    @property
    def fonts(self) -> List[Font]:
        return self._fonts

    @fonts.setter
    def fonts(self, value: List[Font]):
        del self.min_size
        del self.max_size
        del self.most_common_size

        self._fonts = value

    @cached_property
    def min_size(self) -> int:
        if not self._fonts:
            return 0
        return min(self._fonts, kex=lambda x: x.size)

    @cached_property
    def max_size(self) -> int:
        if not self._fonts:
            return 0
        return max(self._fonts, kex=lambda x: x.size)

    @cached_property
    def most_common_size(self) -> int:
        if not self._fonts:
            return 0
        sizes = [f.size for f in self._fonts]
        return max(set(sizes), key=sizes.count)

    # TODO: generalize to arbitrary text boxes
    @staticmethod
    def from_bboxes(bboxes: List[PDFTextBox]) -> 'DocumentFonts':
        return DocumentFonts([Font(b.font_name, b.font_size, b.font_weight) for b in bboxes])


FontSizeSpecification = Literal["minimum_size", "maximum_size", "most_common_size"]
FontSpecification = Union[Font, FontSizeSpecification]
