from dataclasses import dataclass, field
from typing import List, Optional

from datariot.parser.__spi__ import RegexPattern


@dataclass
class BBoxConfig:
    filter_min_y: Optional[int] = 50
    filter_max_y: Optional[int] = 710
    filter_must_regexes: List[RegexPattern] = field(default_factory=list)
    filter_must_not_regexes: List[RegexPattern] = field(default_factory=lambda: [RegexPattern(r"^\s*$")])
    extract_words_extra_attrs: List[str] = field(default_factory=lambda: ["fontname", "size"])
    extract_words_keep_blank_chars: bool = True
    merge_same_font_name: bool = True
    merge_same_font_size: bool = True
    merge_same_font_weight: bool = True
    merge_blank_always: bool = True
    merge_same_line_tolerance: int = 3
    merge_x_tolerance: int = 10
    merge_y_tolerance: int = 10
    columns_split: bool = True
    columns_gap: int = 10
