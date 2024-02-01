from dataclasses import dataclass
from typing import List, Tuple

from PIL.Image import Image
from docx.text.paragraph import Paragraph, Run

from datariot.__spi__.type import Formatter, Box, MediaAware
from datariot.util.image_util import to_base64


@dataclass
class DocxTextBox(Box):
    """
    Box implementation for the plain text docx elements.
    """

    def __init__(self, paragraph: Paragraph):
        super().__init__(None, None, None, None)
        self.p = paragraph

    @property
    def text(self):
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
            return doc.styles.element.xpath('w:docDefaults/w:rPrDefault/w:rPr/w:sz')[0].val.pt
        except:
            return -1

    def __repr__(self):
        return self.text


class DocxTableBox(Box):
    """
    Box implementation for the table docx elements.
    """

    def __init__(self, rows: list):
        super().__init__(None, None, None, None)
        self.rows = rows

    def __repr__(self):
        lenghts = []
        for row in self.rows:
            lenghts.append([])
            for i, col in enumerate(row):
                lenghts[-1].append(len(col))

        cols = [e.replace(':', '').replace("\n", " ").strip() for e in self.rows[0]]
        buffer = [" | ".join(cols), "-" * 10]

        for row in self.rows[1:]:
            buffer.append(" | ".join([e.replace("\n", " ").strip() for e in row]))

        return "\n" + "\n".join(buffer) + "\n"


class DocxImageBox(Box, MediaAware):
    """
    Box implementation for the image docx elements.
    """

    def __init__(self, name: str, image):
        super().__init__(None, None, None, None)
        self.name = name
        self.image = image

    def render(self, formatter: Formatter):
        return f"[image:{self.name}]"

    def get_file(self) -> Tuple[str, Image]:
        return self.name, self.image

    def to_hash(self) -> str:
        encoded = to_base64(self.image)
        from hashlib import sha256
        return str(sha256(encoded).hexdigest())
