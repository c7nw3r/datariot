import pathlib
from dataclasses import dataclass, field
from io import BytesIO, StringIO
from typing import List, Tuple, TypedDict, Dict, Any

import requests

from datariot.__spi__.splitter import Splitter, Chunk

DEFAULT_TAGS = [
    ("h1", "Header 1"),
    ("h2", "Header 2"),
    ("h3", "Header 3"),
    ("h4", "Header 4"),
    ("h5", "Header 5"),
    ("h6", "Header 6"),
]

class ElementType(TypedDict):
    """Element type as typed dict."""

    url: str
    xpath: str
    content: str
    metadata: Dict[str, str]


@dataclass
class HTMLTagSplitter(Splitter):
    """
    Splitting HTML files based on specified headers.
    Requires lxml package.

    Args:
            tags_to_split_on: list of tuples of headers we want to track mapped to
                (arbitrary) keys for metadata. Allowed header values: h1, h2, h3, h4,
                h5, h6 e.g. [("h1", "Header 1"), ("h2", "Header 2)].
            return_each_element: Return each element w/ associated headers.
    """
    tags_to_split_on: List[Tuple[str, str]] = field(default_factory=lambda: DEFAULT_TAGS)
    return_each_element: bool = False

    def __post_init__(self):
        self.tags_to_split_on = sorted(self.tags_to_split_on)

    def aggregate_elements_to_chunks(self, elements: List[ElementType]) -> List[Chunk]:
        """Combine elements with common metadata into chunks

        Args:
            elements: HTML element content with associated identifying info and metadata
        """
        aggregated_chunks: List[ElementType] = []

        for element in elements:
            if (
                    aggregated_chunks
                    and aggregated_chunks[-1]["metadata"] == element["metadata"]
            ):
                # If the last element in the aggregated list
                # has the same metadata as the current element,
                # append the current content to the last element's content
                aggregated_chunks[-1]["content"] += "  \n" + element["content"]
            else:
                # Otherwise, append the current element to the aggregated list
                aggregated_chunks.append(element)

        return [
            Chunk(text=chunk["content"], data=chunk["metadata"])
            for chunk in aggregated_chunks
        ]

    def split_text_from_url(self, url: str) -> List[Chunk]:
        """Split HTML from web URL

        Args:
            url: web URL
        """
        r = requests.get(url)
        return self.split_text_from_file(BytesIO(r.content))

    def __call__(self, text: str) -> List[Chunk]:
        """Split HTML text string

        Args:
            text: HTML text
        """
        return self.split_text_from_file(StringIO(text))

    def split_text_from_file(self, file: Any) -> List[Chunk]:
        """Split HTML file

        Args:
            file: HTML file
        """
        try:
            from lxml import etree
        except ImportError as e:
            raise ImportError(
                "Unable to import lxml, please install with `pip install lxml`."
            ) from e
        # use lxml library to parse html document and return xml ElementTree
        # Explicitly encoding in utf-8 allows non-English
        # html files to be processed without garbled characters
        parser = etree.HTMLParser(encoding="utf-8")
        tree = etree.parse(file, parser)

        # document transformation for "structure-aware" chunking is handled with xsl.
        # see comments in html_chunks_with_headers.xslt for more detailed information.
        xslt_path = pathlib.Path(__file__).parent / "xsl/html_chunks_with_headers.xslt"
        xslt_tree = etree.parse(xslt_path)
        transform = etree.XSLT(xslt_tree)
        result = transform(tree)
        result_dom = etree.fromstring(str(result))

        # create filter and mapping for header metadata
        header_filter = [header[0] for header in self.tags_to_split_on]
        header_mapping = dict(self.tags_to_split_on)

        # map xhtml namespace prefix
        ns_map = {"h": "http://www.w3.org/1999/xhtml"}

        # build list of elements from DOM
        elements = []
        for element in result_dom.findall("*//*", ns_map):
            if element.findall("*[@class='headers']") or element.findall(
                    "*[@class='chunk']"
            ):
                elements.append(
                    ElementType(
                        url=file,
                        xpath="".join(
                            [
                                node.text or ""
                                for node in element.findall("*[@class='xpath']", ns_map)
                            ]
                        ),
                        content="".join(
                            [
                                node.text or ""
                                for node in element.findall("*[@class='chunk']", ns_map)
                            ]
                        ),
                        metadata={
                            # Add text of specified headers to metadata using header
                            # mapping.
                            header_mapping[node.tag]: node.text or ""
                            for node in filter(
                                lambda x: x.tag in header_filter,
                                element.findall("*[@class='headers']/*", ns_map),
                            )
                        },
                    )
                )

        if not self.return_each_element:
            return self.aggregate_elements_to_chunks(elements)
        else:
            return [Chunk(chunk["content"], chunk["metadata"]) for chunk in elements]
