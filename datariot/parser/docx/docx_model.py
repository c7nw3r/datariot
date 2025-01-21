from dataclasses import dataclass
from typing import List, Optional, Tuple

from PIL.Image import Image
from docx.text.paragraph import Paragraph, Run

from datariot.__spi__.type import Box, MediaAware
from datariot.__util__.array_util import flatten
from datariot.__util__.image_util import to_base64
from datariot.__util__.text_util import create_uuid_from_string


@dataclass
class DocxTextBox(Box):
    """
    Box implementation for the plain text docx elements.
    """

    def __init__(
        self,
        root_name: str,
        paragraph: Paragraph,
        page_number: Optional[int] = None,
    ):
        super().__init__(None, None, None, None)
        self.root_name = root_name
        self.p = paragraph
        self.page_number = page_number

    @property
    def text(self):
        if len(self.p._element.xpath(".//w:sdt//w:t")) > 0:
            segments = self.p._element.xpath(".//w:t")
            return " ".join([str(e) for e in segments])

        return self.p.text

    @property
    def style_name(self):
        return self.p.style.name

    @property
    def style(self):
        return self.p.style

    @property
    def font_size(self):
        font_size = self.get_max_font_size(self.p.runs)
        if font_size >= 0:
            return font_size
        if self.style.font.size is not None:
            return self.style.font.size.pt
        return self.get_default_font_size(self.p.__doc__)

    def get_max_font_size(self, runs: List[Run]) -> int:
        max_size = -1
        for run in runs:
            font_size = int(run.font.size.pt) if run.font.size is not None else -1
            if font_size > max_size:
                max_size = run.font.size.pt

            if max_size == -1:
                array = run.element.xpath("./w:rPr/w:szCs/@w:val")
                if len(array) > 0:
                    max_size = int(array[0]) / 2

        return max_size

    def get_default_font_size(self, doc):
        try:
            return doc.styles.element.xpath("w:docDefaults/w:rPrDefault/w:rPr/w:sz")[
                0
            ].val.pt
        except:
            return -1

    def __repr__(self):
        return self.text


class DocxListBox(DocxTextBox):
    def __init__(
        self,
        root_name: str,
        paragraph: Paragraph,
        page_number: Optional[int] = None,
    ):
        super().__init__(root_name, paragraph, page_number)

        ilvl = self.p._element.xpath("w:pPr/w:numPr/w:ilvl/@w:val")
        self.numbering = int(ilvl[0])


class DocxTableBox(Box):
    """
    Box implementation for the table docx elements.
    """

    def __init__(self,
                 root_name: str,
                 rows: List, paragraphs: List[List[Paragraph]],
                 page_number: Optional[int] = None):
        super().__init__(None, None, None, None)
        self.rows = rows
        self.paragraphs = paragraphs
        self.root_name = root_name
        self.page_number = page_number

    @property
    def font_sizes(self) -> List[int]:
        def get_font_size(runs: List[Run]) -> int:
            max_size = -1
            for run in runs:
                font_size = int(run.font.size.pt) if run.font.size is not None else -1
                if font_size > max_size:
                    max_size = run.font.size.pt

                if max_size == -1:
                    array = run.element.xpath("./w:rPr/w:szCs/@w:val")
                    if len(array) > 0:
                        max_size = int(array[0]) / 2

            return max_size

        return [get_font_size(p.runs) for p in flatten(self.paragraphs)]

    def __repr__(self):
        lenghts = []
        for row in self.rows:
            lenghts.append([])
            for i, col in enumerate(row):
                lenghts[-1].append(len(col))

        cols = [e.replace(":", "").replace("\n", " ").strip() for e in self.rows[0]]
        buffer = [" | ".join(cols), "-" * 10]

        for row in self.rows[1:]:
            buffer.append(" | ".join([e.replace("\n", " ").strip() for e in row]))

        return "\n" + "\n".join(buffer) + "\n"


class DocxImageBox(Box, MediaAware):
    """
    Box implementation for the image docx elements.
    """

    def __init__(self, root_name: str, name: str, image, id: Optional[str] = None, page_number: Optional[int] = None,):
        super().__init__(None, None, None, None)
        self.name = name
        self.image = image
        self.root_name = root_name
        self._id = id
        self.page_number = page_number

    @property
    def id(self) -> str:
        return self._id or create_uuid_from_string(self.to_hash(fast=True))

    def get_file(self) -> Tuple[str, Image]:
        return self.name, self.image

    def to_hash(self, fast: bool = False) -> str:
        from hashlib import sha256

        if fast:
            return str(sha256(self.name.encode("utf-8")).hexdigest())

        encoded = to_base64(self.image)
        return str(sha256(encoded).hexdigest())
