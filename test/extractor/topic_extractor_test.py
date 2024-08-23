from unittest import TestCase

from datariot.extractor.topic_extractor import TopicExtractor
from datariot.parser.pdf import PDFParser
from test.__asset__ import get_test_path


class TopicExtractorTest(TestCase):

    def test_abcd(self):
        parser = PDFParser()
        parsed = parser.parse(get_test_path("wikipedia_de.pdf"))

        extractor = TopicExtractor(min_order=1)
        extracted = extractor.extract(parsed)

        assert len(extracted) == 18
