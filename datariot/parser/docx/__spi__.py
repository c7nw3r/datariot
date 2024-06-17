from pydantic import BaseModel

from datariot.__spi__.type import Parsed
from datariot.parser.docx.docx_model import DocxTextBox


class DocxParserConfig(BaseModel):
    include_images: bool = True


class ParsedDocx(Parsed):
    @property
    def is_paged(self) -> bool:
        text_box = next(b for b in self.bboxes if isinstance(b, DocxTextBox))

        return text_box.page_number is not None
