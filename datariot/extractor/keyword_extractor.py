from collections import Counter
from dataclasses import dataclass
from typing import List

from datariot.__spi__.error import DataRiotImportException
from datariot.__spi__.type import Parsed, Extractor
from datariot.parser.__spi__ import TextAware


@dataclass
class Keyword:
    text: str
    count: int


class KeywordExtractor(Extractor):

    def __init__(self, langs: List[str], most_common: int = 5):
        self.most_common = most_common

        try:
            import stopwordsiso
            self.stopwords = stopwordsiso.stopwords(langs)
        except ImportError:
            raise DataRiotImportException("stopwordsiso")

    def extract(self, parsed: Parsed):
        tokens = []
        bboxes = [e for e in parsed.bboxes if isinstance(e, TextAware)]
        for box in bboxes:
            tokens.extend(box.text.lower().split(" "))

        tokens = [e.strip().lower() for e in tokens if len(e.strip()) >= 2]
        tokens = [e.replace(".", "") for e in tokens]
        tokens = [e.replace(",", "") for e in tokens]
        tokens = [e.replace(";", "") for e in tokens]
        tokens = [e.replace(":", "") for e in tokens]
        tokens = [e.replace("\n", "") for e in tokens]
        tokens = [e.replace("\r", "") for e in tokens]
        tokens = [e.replace("\t", "") for e in tokens]
        tokens = [e for e in tokens if e not in self.stopwords]

        counter = Counter(tokens)
        keywords = counter.most_common(self.most_common)

        return [Keyword(text, count) for text, count in keywords]
