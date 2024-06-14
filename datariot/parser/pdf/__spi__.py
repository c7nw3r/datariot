from dataclasses import dataclass, field
from typing import List, Optional

from datariot.__spi__.type import Parsed
from datariot.parser.__spi__ import FontSpecification, RegexPattern
from datariot.parser.pdf.pdf_formatter import JSONPDFFormatter


@dataclass
class BoxSizeConfig:
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None


# TODO: split into separate config classes
@dataclass
class BBoxConfig:
    filter_min_y: Optional[int] = None
    filter_max_y: Optional[int] = None
    filter_must_regexes: List[RegexPattern] = field(default_factory=list)
    filter_must_not_regexes: List[RegexPattern] = field(
        default_factory=lambda: [RegexPattern(r"^\s*$")]
    )
    extract_words_extra_attrs: List[str] = field(
        default_factory=lambda: ["fontname", "size"]
    )
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
    columns_split_fonts: List[FontSpecification] = field(
        default_factory=lambda: ["most_common"]
    )
    sorter_fuzzy: bool = False
    sorter_y_tolerance: int = 5
    parser_x_tolerance: int = 3
    parser_y_tolerance: int = 3
    image_filter_box_size: BoxSizeConfig = field(
        default_factory=lambda: BoxSizeConfig(min_width=30, min_height=30)
    )
    table_vertical_strategy: str = "lines_strict"
    table_horizontal_strategy: str = "lines_strict"

    ocr_tesseract_languages: list[str] = ["deu", "eng"]
    """Tesseract language abbreviations for ocr"""

    ocr_tesseract_config: str = "--psm 3"
    """String of Tesseract command line options, e.g. --oem, --psm, ..."""

    ocr_filter_box_min_chars: int = 50
    """Minimum number of characters in an ocr box to be included"""

    ocr_keep_image_box: bool = True
    """Whether to keep image boxes in addition to ocr boxes"""


@dataclass
class PDFParserConfig:
    screenshot: bool = False
    ocr: bool = False
    bbox_config: BBoxConfig = BBoxConfig()


class ParsedPDF(Parsed):
    def to_json(self):
        formatter = JSONPDFFormatter()
        return {"path": self.path, "bboxes": [b.render(formatter) for b in self.bboxes]}
