from typing import Optional, Tuple, List

from pdfplumber.page import Page
from pdfplumber.table import Table

from datariot.__spi__.type import FontWeight, Box

DEFAULT_IMAGE_RESOLUTION = 72
IMAGE_RESOLUTION = 400


class PDFTextBox(Box):

    def __init__(self, x1: int, y1: int, x2: int, y2: int, text: str, size: int, font_name: str):
        super().__init__(x1, x2, y1, y2)
        self._text = text
        self._size = size
        self._font_name = font_name

    @staticmethod
    def from_dict(data: dict):
        x1 = data["x0"]
        y1 = data["top"]
        x2 = data["x1"]
        y2 = data["bottom"]
        text = data["text"]
        font_name = data["fontname"]
        font_size = data["size"]
        return PDFTextBox(x1, y1, x2, y2, text, font_size, font_name)

    def with_text(self, text: str):
        return PDFTextBox(self.x1, self.y1, self.x2, self.y2, text, self._size, self._font_name)

    @property
    def text(self) -> str:
        return self._text

    @property
    def font_size(self) -> int:
        return self._size

    @property
    def font_weight(self) -> Optional[FontWeight]:
        if self._font_name is None:
            return None
        if "bold" in self._font_name.lower():
            return "bold"
        return "regular"

    def copy(self):
        return PDFTextBox(self.x1, self.y1, self.x2, self.y2, self.text, self.font_size, self._font_name)

    def __repr__(self):
        return self.text


class PDFOcrBox(PDFTextBox):

    def __init__(self, x1: int, y1: int, x2: int, y2: int, text: str):
        super().__init__(x1, x2, y1, y2, text, -1, "regular")

    @staticmethod
    def from_ocr(data):
        ratio = IMAGE_RESOLUTION / DEFAULT_IMAGE_RESOLUTION

        x1 = int(data[0] / ratio)
        y1 = int(data[1] / ratio)
        x2 = int((data[0] + data[2]) / ratio)
        y2 = int((data[1] + data[3]) / ratio)
        return PDFOcrBox(x1, y1, x2, y2, data[4])

    def with_text(self, text: str):
        return PDFOcrBox(self.x1, self.y1, self.x2, self.y2, text)


class PDFImageBox(Box):

    def __init__(self, page: Page, data: dict):
        super().__init__(int(data["x0"]), int(data["x1"]), int(data["top"]), int(data["bottom"]))
        self.page_number = page.page_number

        self.data = page.crop((self.x1,
                               max(0, int(page.height - self.y2)),
                               self.x2,
                               max(0, int(page.height - self.y1)))).to_image(resolution=IMAGE_RESOLUTION)

    @property
    def width(self):
        return self.x2 - self.x1

    @property
    def height(self):
        return self.y2 - self.y1

    def save(self):
        return self.data.save(f"./image_{self.page_number}_{self.x1}_{self.y1}_{self.x2}_{self.y2}.png")

    def __repr__(self):
        return f"x1:{self.x1}, y1:{self.y1}, x2:{self.x2}, y2:{self.y2}"


class PDFTableBox(Box):

    def __init__(self, data: Tuple[Table, List[List[str]]]):
        super().__init__(data[0].bbox[0], data[0].bbox[2], data[0].bbox[1], data[0].bbox[3])
        self.rows = data[1]

    def __repr__(self):
        def to_col(cols: List[str]):
            return " | ".join([col for col in cols if col is not None])

        return "\n".join([to_col(row) for row in self.rows])

    #def render(self, formatter: Formatter):
    #    return self.__repr__()
