from dataclasses import dataclass
from typing import List, Optional, Tuple, Union

from pdfplumber.page import Page
from pdfplumber.table import Table
from PIL.Image import Image

from datariot.__spi__.type import Box, ColumnPosition, FontWeight, MediaAware
from datariot.__util__.image_util import to_base64
from datariot.__util__.text_util import create_uuid_from_string
from datariot.parser.__spi__ import Font, FontAware, TextAware


DEFAULT_IMAGE_RESOLUTION = 72
IMAGE_RESOLUTION = 400


@dataclass
class PDFTextBoxAnnotation:
    start_idx: int
    end_idx: int
    uri: Optional[str] = None


class PDFTextBox(Box, FontAware, TextAware):
    def __init__(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        text: str,
        font_size: int,
        font_name: str,
        page_number: int,
        hyperlinks: Union[List[PDFTextBoxAnnotation], None] = None,
    ):
        super().__init__(x1, x2, y1, y2)
        self._text = text
        self.font_size = font_size
        self.font_name = font_name
        self.page_number = page_number
        if hyperlinks is not None:
            self.hyperlinks = hyperlinks
        else:
            self.set_hyperlink(None)

    @property
    def contains_hyperlinks(self) -> bool:
        return any(a.uri for a in self.hyperlinks)

    @property
    def last_hyperlink(self) -> Union[str, None]:
        return self.hyperlinks[-1].uri if self.hyperlinks else None

    def set_hyperlink(self, uri: Optional[str]) -> None:
        self.hyperlinks = [
            PDFTextBoxAnnotation(start_idx=0, end_idx=len(self.text), uri=uri)
        ]

    def add_hyperlinks(self, links: List[PDFTextBoxAnnotation]) -> None:
        self.hyperlinks.extend(links)

    def clean(self) -> None:
        self._clean_hyperlinks()

    def _clean_hyperlinks(self) -> None:
        if not self.hyperlinks:
            self.hyperlinks = []

        links: List[PDFTextBoxAnnotation] = []
        initial_link = self.hyperlinks[0]
        merged_link = PDFTextBoxAnnotation(
            start_idx=initial_link.start_idx,
            end_idx=initial_link.end_idx,
            uri=initial_link.uri,
        )
        absolute_idx = initial_link.end_idx
        for idx, h in enumerate(self.hyperlinks[1:], 1):
            if h.uri == self.hyperlinks[idx - 1].uri:
                if h.uri is None:
                    absolute_idx += 1
                merged_link.end_idx = merged_link.end_idx + h.end_idx
            else:
                absolute_idx += 1
                links.append(merged_link)
                merged_link = PDFTextBoxAnnotation(
                    start_idx=absolute_idx, end_idx=absolute_idx + h.end_idx, uri=h.uri
                )

            absolute_idx += h.end_idx
        links.append(merged_link)

        self.hyperlinks = [link for link in links if link.uri]

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
        return PDFTextBox(
            self.x1,
            self.y1,
            self.x2,
            self.y2,
            text,
            self._font_size,
            self._font_name,
            self.page_number,
            self.hyperlinks,
        )

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

    @property
    def font(self) -> Font:
        return Font(self.font_name, self.font_size, self.font_weight)

    def copy(self):
        return PDFTextBox(
            self.x1,
            self.y1,
            self.x2,
            self.y2,
            self.text,
            self.font_size,
            self._font_name,
            self.page_number,
            self.hyperlinks,
        )

    def __repr__(self):
        return self.text


class PDFColumnTextBox(PDFTextBox):
    def __init__(
        self,
        x1: float,
        y1: float,
        x2: float,
        y2: float,
        text: str,
        font_size: int,
        font_name: str,
        page_number: int,
        num_columns: int,
        column: ColumnPosition,
    ):
        super().__init__(x1, y1, x2, y2, text, font_size, font_name, page_number)
        self.num_columns = num_columns
        self.column = column

    @staticmethod
    def from_pdf_text_box(
        box: PDFTextBox, num_columns: int, column: ColumnPosition
    ) -> "PDFColumnTextBox":
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
            column,
        )


class PDFOcrBox(PDFTextBox):
    def __init__(
        self, x1: int, y1: int, x2: int, y2: int, text: str, page_number: int = -1
    ):
        super().__init__(x1, y1, x2, y2, text, -1, "regular", page_number)

    @staticmethod
    def from_ocr(data):
        ratio = IMAGE_RESOLUTION / DEFAULT_IMAGE_RESOLUTION
        left, top, width, height, text, page_number = data

        x1 = int(left / ratio)
        y1 = int(top / ratio)
        x2 = int((left + width) / ratio)
        y2 = int((top + height) / ratio)
        return PDFOcrBox(x1, y1, x2, y2, text, page_number)

    def with_text(self, text: str):
        return PDFOcrBox(self.x1, self.y1, self.x2, self.y2, text)


class PDFImageBox(Box, MediaAware):
    def __init__(self, page: Page, data: dict, id: Optional[str] = None):
        super().__init__(data["x0"], data["x1"], data["top"], data["bottom"])
        self.page = page
        self._id = id

    @property
    def page_number(self):
        return self.page.page_number

    @property
    def id(self) -> str:
        return self._id or create_uuid_from_string(self.to_hash(fast=True))

    def crop(self, crop_box: Optional[Box] = None):
        crop_box = crop_box or (self.x1, self.y1, self.x2, self.y2)
        return self.page.crop(crop_box, strict=False).to_image(
            resolution=IMAGE_RESOLUTION
        )

    def save(self, crop_box: Optional[Box] = None):
        data = self.crop(crop_box)
        x1, y1, x2, y2 = crop_box or (self.x1, self.y1, self.x2, self.y2)
        return data.save(f"./image_{self.page_number}_{x1}_{y1}_{x2}_{y2}.png")

    def __repr__(self):
        return f"x1:{self.x1}, y1:{self.y1}, x2:{self.x2}, y2:{self.y2}"

    def get_file(self, crop_box: Optional[Box] = None) -> Tuple[str, Image]:
        # TODO: get image data directly and don't take a screenshot (crop)
        data = self.crop(crop_box)
        x1, y1, x2, y2 = crop_box or (self.x1, self.y1, self.x2, self.y2)

        name = f"image_{self.page_number}_{x1}_{y1}_{x2}_{y2}"
        return name, data.original

    def to_hash(self, crop_box: Optional[Box] = None, fast: bool = False) -> str:
        from hashlib import sha256

        if fast:
            key = f"{self.page_number}:{self.x1}:{self.y1}:{self.x2}:{self.y2}"
            return str(sha256(key.encode("utf-8")).hexdigest())

        data = self.crop(crop_box)
        encoded = to_base64(data.original)

        return str(sha256(encoded).hexdigest())


class PDFLineCurveBox(Box):
    def __init__(self, page: Page, data: dict):
        super().__init__(data["x0"], data["x1"], data["top"], data["bottom"])
        self.page = page

    @property
    def page_number(self):
        return self.page.page_number

    def __repr__(self):
        return f"x1:{self.x1}, y1:{self.y1}, x2:{self.x2}, y2:{self.y2}"


class PDFTableBox(Box):
    def __init__(self, page: Page, data: Tuple[Table, List[List[str]]]):
        super().__init__(
            data[0].bbox[0], data[0].bbox[2], data[0].bbox[1], data[0].bbox[3]
        )
        self.rows = data[1]
        self.page_number = page.page_number

    def __repr__(self):
        def to_col(cols: List[str]):
            return " | ".join([col for col in cols if col is not None])

        return "\n".join([to_col(row) for row in self.rows])

    def __len__(self):
        return len(str(self).strip())


class PDFHyperlinkBox(Box):
    def __init__(self, x1: int, y1: int, x2: int, y2: int, uri: str):
        super().__init__(x1, x2, y1, y2)
        self.uri = uri.replace("&amp;", "&")

    @staticmethod
    def from_dict(data: dict):
        x1 = data["x0"]
        y1 = data["top"]
        x2 = data["x1"]
        y2 = data["bottom"]
        return PDFHyperlinkBox(x1, y1, x2, y2, data["uri"])
