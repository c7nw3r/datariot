from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from datariot.__spi__.error import DataRiotImportException
from datariot.__spi__.type import Parsed, Extractor
from datariot.parser.__spi__ import TextAware


@dataclass
class Keyword:
    text: str
    count: int

@dataclass
class KeywordExtractor(Extractor):
    langs: List[str]
    tokens_to_remove: List[str] = field(default_factory=lambda: [".", ",", ";", ":", "\n", "\r", "\t"])
    remove_numbers: bool = True

    def __post_init__(self):
        try:
            import stopwordsiso
            self.stopwords = stopwordsiso.stopwords(self.langs)
        except ImportError:
            raise DataRiotImportException("stopwordsiso")

    def extract(self, parsed: Parsed, most_common: int = 5, min_occurrence: Optional[int] = None):
        tokens = []
        bboxes = [e for e in parsed.bboxes if isinstance(e, TextAware)]
        for box in bboxes:
            tokens.extend(box.text.lower().split(" "))

        tokens = [e.strip().lower() for e in tokens if len(e.strip()) >= 2]

        for token in self.tokens_to_remove:
            tokens = [e.replace(token, "") for e in tokens]

        if self.remove_numbers:
            tokens = [e for e in tokens if not e.isdigit()]

        tokens = [e for e in tokens if e not in self.stopwords]

        counter = Counter(tokens)
        keywords = counter.most_common(most_common)

        if min_occurrence is not None:
            keywords = [(k, v) for k, v in keywords if v >= min_occurrence]

        return [Keyword(text, count) for text, count in keywords]
