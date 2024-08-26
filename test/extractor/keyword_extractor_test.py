from unittest import TestCase

from datariot.extractor.keyword_extractor import KeywordExtractor
from datariot.parser.pdf import PDFParser
from test.__asset__ import get_test_path


class KeywordExtractorTest(TestCase):

    def test_abcd(self):
        parser = PDFParser()
        parsed = parser.parse(get_test_path("wikipedia_de.pdf"))

        extractor = KeywordExtractor(langs=["de", "en"], min_occurrence=20)
        extracted = extractor.extract(parsed)

        keywords = [e.text for e in extracted]
        assert "wikipedia" in keywords
        assert "artikel" in keywords
        assert "autoren" in keywords
