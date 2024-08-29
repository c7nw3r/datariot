from unittest import TestCase

from datariot.extractor.title_extractor import TitleExtractor
from datariot.parser.pdf import PDFParser
from test.__asset__ import get_test_path


class TitleExtractorTest(TestCase):

    def test_abcd(self):
        parser = PDFParser()
        parsed = parser.parse(get_test_path("wikipedia_de.pdf"))

        extractor = TitleExtractor(min_order=1)
        extracted = extractor.extract(parsed)

        assert len(extracted) == 18
