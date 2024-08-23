from dataclasses import dataclass

from datariot.__spi__.type import Parsed, Extractor
from datariot.parser.__spi__ import DocumentFonts, FontAware, TextAware


@dataclass
class Topic:
    order: int
    text: str


class TopicExtractor(Extractor):

    def __init__(self, min_order: int = 0):
        self.min_order = min_order

    def extract(self, parsed: Parsed):
        topics = []

        bboxes = [e for e in parsed.bboxes if isinstance(e, FontAware) and isinstance(e, TextAware)]
        doc_fonts = DocumentFonts.from_bboxes(bboxes)

        for box in bboxes:
            order = doc_fonts.get_size_rank(box.font.size)

            if order <= self.min_order:
                topics.append(Topic(order, box.text))

        return topics
