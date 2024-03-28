from typing import List, Optional, Tuple

from PIL.Image import Image
from pdfplumber.page import Page
from pdfplumber.table import Table

from datariot.__spi__.type import Box, ColumnPosition, FontWeight, MediaAware
from datariot.__util__.image_util import to_base64

DEFAULT_IMAGE_RESOLUTION = 72
IMAGE_RESOLUTION = 400


class PDFTextBox(Box):

    def __init__(
            self,
            x1: int,
            y1: int,
            x2: int,
            y2: int,
            text: str,
            font_size: int,
            font_name: str,
            page_number: int
    ):
        super().__init__(x1, x2, y1, y2)
        self._text = text
        self.font_size = font_size
        self.font_name = font_name
        self.page_number = page_number

    @staticmethod
    def from_dict(data: dict):
        x1 = data["x0"]
        y1 = data["top"]
        x2 = data["x1"]
        y2 = data["bottom"]
        text = data["text"]
        font_name = data["fontname"]
        font_size = data["size"]
        page_number = data["page_number"]
        return PDFTextBox(x1, y1, x2, y2, text, font_size, font_name, page_number)

    def with_text(self, text: str):
        return PDFTextBox(self.x1, self.y1, self.x2, self.y2, text, self._font_size, self._font_name, self.page_number)

    @property
    def text(self) -> str:
        return self._text

    @property
    def font_size(self) -> int:
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = round(value)

    @property
    def font_name(self) -> str:
        return self._font_name

    @font_name.setter
    def font_name(self, value):
        self._font_name = value

    @property
    def font_weight(self) -> Optional[FontWeight]:
        if self._font_name is None:
            return None
        if "bold" in self._font_name.lower():
            return "bold"
        return "regular"

    def copy(self):
        return PDFTextBox(
            self.x1,
            self.y1,
            self.x2,
            self.y2,
            self.text,
            self.font_size,
            self._font_name,
            self.page_number
        )

    def __repr__(self):
        return self.text


class PDFColumnTextBox(PDFTextBox):

    def __init__(
            self,
            x1: int,
            y1: int,
            x2: int,
            y2: int,
            text: str,
            font_size: int,
            font_name: str,
            page_number: int,
            num_columns: int,
            column: ColumnPosition
    ):
        super().__init__(x1, y1, x2, y2, text, font_size, font_name, page_number)
        self.num_columns = num_columns
        self.column = column

    @staticmethod
    def from_pdf_text_box(box: PDFTextBox, num_columns: int, column: ColumnPosition) -> "PDFColumnTextBox":
        return PDFColumnTextBox(
            box.x1,
            box.y1,
            box.x2,
            box.y2,
            box.text,
            box.font_size,
            box.font_name,
            box.page_number,
            num_columns,
            column
        )


class PDFOcrBox(PDFTextBox):

    def __init__(self, x1: int, y1: int, x2: int, y2: int, text: str, page_number: int = -1):
        super().__init__(x1, y1, x2, y2, text, -1, "regular", page_number)

    @staticmethod
    def from_ocr(data):
        ratio = IMAGE_RESOLUTION / DEFAULT_IMAGE_RESOLUTION
        left, top, width, height, text = data

        x1 = int(left / ratio)
        y1 = int(top / ratio)
        x2 = int((left + width) / ratio)
        y2 = int((top + height) / ratio)
        return PDFOcrBox(x1, y1, x2, y2, text)

    def with_text(self, text: str):
        return PDFOcrBox(self.x1, self.y1, self.x2, self.y2, text)


class PDFImageBox(Box, MediaAware):

    def __init__(self, page: Page, data: dict):
        super().__init__(int(data["x0"]), int(data["x1"]), int(data["top"]), int(data["bottom"]))
        self.page_number = page.page_number

        crop_box = (self.x1, self.y1, self.x2, self.y2)
        self.data = page.crop(crop_box, strict=False).to_image(resolution=IMAGE_RESOLUTION)

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

    def get_file(self) -> Tuple[str, Image]:
        name = f"image_{self.page_number}_{self.x1}_{self.y1}_{self.x2}_{self.y2}"
        return name, self.data.original

    def to_hash(self) -> str:
        encoded = to_base64(self.data.original)
        from hashlib import sha256
        return str(sha256(encoded).hexdigest())


class PDFTableBox(Box):

    def __init__(self, page: Page, data: Tuple[Table, List[List[str]]]):
        super().__init__(data[0].bbox[0], data[0].bbox[2], data[0].bbox[1], data[0].bbox[3])
        self.rows = data[1]
        self.page_number = page.page_number

    def __repr__(self):
        def to_col(cols: List[str]):
            return " | ".join([col for col in cols if col is not None])

        return "\n".join([to_col(row) for row in self.rows])
