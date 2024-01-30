from dataclasses import dataclass
from typing import List, Union

from docx.text.paragraph import Paragraph

from datariot.__spi__.type import TextBox, Formatter, TableBox
from datariot.parser.docx.docx_mixin import DocxStyleMixin


@dataclass
class DocxTextBox(TextBox, DocxStyleMixin):
    """
    TextBox implementation for the docx document type.
    """

    def __init__(self, paragraph: Paragraph):
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

    def __repr__(self):
        return self.text


@dataclass
class DocxTableBox(TableBox):
    """
    TableBox implementation for the docx document type.
    """

    rows: list

    def render(self, evaluator: Formatter):
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
