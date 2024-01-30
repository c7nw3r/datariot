from dataclasses import dataclass
from typing import Optional

from datariot.__spi__.type import TextBox, FontWeight


class PdfTextBox(TextBox):

    def __init__(self, data: dict):
        self.x1 = data["x0"]
        self.y1 = data["top"]
        self.x2 = data["x1"]
        self.y2 = data["bottom"]
        self.font_name = data["fontname"]
        self.data = data

    @property
    def text(self) -> str:
        return self.data["text"]

    @property
    def font_size(self) -> int:
        return self.data["size"]

    @property
    def font_weight(self) -> Optional[FontWeight]:
        if self.font_name is None:
            return None
        if "bold" in self.font_name.lower():
            return "bold"
        return "regular"
