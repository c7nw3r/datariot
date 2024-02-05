from dataclasses import dataclass
import re


@dataclass
class RegexPattern:
    pattern: str
    flags: re.RegexFlag = 0
