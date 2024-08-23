from unittest import TestCase

from datariot.parser.pdf import PDFParser
from test.__asset__ import get_test_path


class PDFParserTest(TestCase):

    def test_parsed_properties(self):
        parser = PDFParser()
        parsed = parser.parse(get_test_path("wikipedia_de.pdf"))

        assert parsed.properties["size"] is not None
        assert parsed.properties["name"] is not None
