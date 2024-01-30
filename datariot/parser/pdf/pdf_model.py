from dataclasses import dataclass
from typing import Optional

from datariot.__spi__.type import TextBox, FontWeight


@dataclass
class PdfTextBox(TextBox):
    x1: float
    y1: float
    x2: float
    y2: float
    text: str
    font_size: Optional[float]
    font_name: Optional[str]

    @property
    def font_weight(self) -> Optional[FontWeight]:
        if self.font_name is None:
            return None
        if "bold" in self.font_name.lower():
            return "bold"
        return "regular"
