from dataclasses import dataclass
from typing import Optional, List

from datariot.__spi__ import Parsed
from datariot.__util__.array_util import flatten


@dataclass
class XlsxParserConfig:
    included_rows: Optional[List[int]] = None
    included_cols: Optional[List[int]] = None
    worksheet_id: Optional[int] = None


@dataclass
class XlsxParsed(Parsed):

    def __post_init__(self):
        self.header = self.bboxes[0]
        self.bboxes = self.bboxes[1:]

    def render_as_string(self, delimiter: str = "\n\n"):
        return delimiter.join([
            *self.header.values,
            *flatten([e.values for e in self.bboxes])
        ])