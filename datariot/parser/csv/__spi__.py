from dataclasses import dataclass
from typing import Optional


@dataclass
class CsvParserConfig:
    newline: str = ''
    delimiter: str = ","
    quotechar: str = '"'
    skip_header: bool = False
    template: Optional[str] = None
