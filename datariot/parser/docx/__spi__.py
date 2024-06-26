from pydantic import BaseModel

from datariot.__spi__.type import Parsed
from datariot.parser.__spi__ import BoxFilterSizeConfig
from datariot.parser.docx.docx_model import DocxTextBox


class DocxParserConfig(BaseModel):
    include_images: bool = True
    image_filter_box_size: BoxFilterSizeConfig = BoxFilterSizeConfig(
        min_width=30, min_height=30
    )
    media_use_uuid: bool = True


class ParsedDocx(Parsed):
    @property
    def is_paged(self) -> bool:
        text_box = next(b for b in self.bboxes if isinstance(b, DocxTextBox))

        return text_box.page_number is not None
