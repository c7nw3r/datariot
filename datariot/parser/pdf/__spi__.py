import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Literal, Optional, Callable

from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.psparser import PSEOF
from pydantic import BaseModel

from datariot.__spi__.type import Parsed
from datariot.parser.__spi__ import BoxFilterSizeConfig, FontSpecification, RegexPattern
from datariot.parser.pdf.pdf_formatter import JSONPDFFormatter


class TableBoxConfig(BaseModel):
    strategy: Literal["default", "camelot"] = "default"
    vertical_strategy: str = "lines"
    horizontal_strategy: str = "lines"


class TextBoxConfig(BaseModel):
    extraction_strategy: Literal["default", "re_crop"] = "default"
    """
    Strategy to get the final text of a box

    - `default`: final text is the concatenation of all merged text boxes
    - `re_crop`: final bounding box of merged text is cropped from the page
    and the native `.extract_text()` is called on the crop
    """


class OcrConfig(BaseModel):
    only_full_page: bool = False
    """Whether to perform ocr only on full page images, i.e., probably scans"""

    full_page_only_if_no_text: bool = False
    """Whether to perform ocr on a full page region containing extractable text"""

    strategy: Literal["text", "data"] = "text"
    """
    Strategy to extract text from images

    * `text`: pytesseract.image_to_string()
    * `data`: pytesseract.image_to_data() and use text bounding box logic
    """

    languages: List[str] = ["deu", "eng"]
    """Tesseract language abbreviations for ocr"""

    tesseract_config: str = "--psm 3"
    """String of Tesseract command line options, e.g. --oem, --psm, ..."""

    filter_box_min_chars: int = 50
    """Minimum number of characters in an ocr box to be included"""

    keep_image_box: bool = True
    """Whether to keep image boxes in addition to ocr boxes"""


# TODO: split into separate config classes
class BBoxConfig(BaseModel):
    filter_min_y: Optional[int] = None
    filter_max_y: Optional[int] = None
    filter_must_regexes: List[RegexPattern] = []
    filter_must_not_regexes: List[RegexPattern] = [RegexPattern(r"^\s*$")]
    extract_words_extra_attrs: List[str] = ["fontname", "size"]
    extract_words_keep_blank_chars: bool = True
    merge_same_font_name: bool = True
    merge_same_font_size: bool = True
    merge_same_font_weight: bool = True

    merge_blank_always: bool = True
    """always merge boxes which contain only whitespaces, irrespective of font"""

    merge_single_char_always: bool = True
    """always merge boxes with a single non-space character irrespective of font"""

    merge_blank_consecutive_lines: bool = True

    merge_same_line_always_after_most_common: bool = True
    """always merge next word to current bounding box if current bounding box has
    most common font"""

    merge_same_line_tolerance: int = 3
    merge_x_tolerance: int = 10
    merge_y_tolerance: int = 10
    columns_split: bool = True
    columns_gap: int = 2
    columns_min_lines: int = 2
    columns_split_fonts: List[FontSpecification] = ["most_common_size"]
    sorter_fuzzy: bool = False
    sorter_y_tolerance: int = 5
    parser_x_tolerance: int = 3
    parser_y_tolerance: int = 3
    merger_x_tolerance: int = 10
    merger_y_tolerance: int = 10
    merger_steps: int = 2
    image_filter_box_size: BoxFilterSizeConfig = BoxFilterSizeConfig(
        min_width=30, min_height=30
    )
    table_box_config: TableBoxConfig = TableBoxConfig()
    text_box_config: TextBoxConfig = TextBoxConfig()
    ocr_config: OcrConfig = OcrConfig()
    media_use_uuid: bool = True
    handle_hyperlinks: bool = True
    filter_hyperlink_patterns: List[str] = [r"https?\:\/\/\d+\.\d+\.\d+\.\d+\/"]


class PDFParserConfig(BaseModel):
    screenshot: bool = False
    ocr: bool = False
    include_images: bool = True
    bbox_config: BBoxConfig = BBoxConfig()
    object_filter: Optional[Callable[[dict], bool]] = None


@dataclass
class ParsedPDF(Parsed):
    metrics: dict = field(default_factory=lambda: {})

    @property
    def is_paged(self) -> bool:
        return True

    def to_json(self):
        formatter = JSONPDFFormatter()
        return {"path": self.path, "bboxes": [b.render(formatter) for b in self.bboxes]}


class ParsedPDFPage(ParsedPDF):
    @property
    def page_number(self) -> int:
        return next(self.bboxes).page_number


def resilient(func):
    def _decorator(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (PDFSyntaxError, PSEOF):
            with tempfile.NamedTemporaryFile() as tmp:
                import pdfplumber
                pdfplumber.repair(Path(args[0]), tmp.name)
                return func(self, tmp.name)

    return _decorator
