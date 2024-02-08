from typing import List

from bs4 import BeautifulSoup, Tag
from bs4 import NavigableString

from datariot.__spi__ import Formatter
from datariot.parser.web.web_model import WebBox
from datariot.util.text_util import remove_whitespace


class WebMarkdownFormatter(Formatter):

    def __call__(self, box: WebBox) -> str:
        html = box.element.get_attribute("outerHTML")
        soup = BeautifulSoup(html, "lxml")
        return "".join(self.traverse_element(soup))

    def traverse_element(self, element: Tag, level: int = 1) -> List[str]:
        def find_elements(tag: Tag):
            return [TextWrapper(e) if isinstance(e, NavigableString) else e for e in tag.contents]

        if element.name == "h1":
            text = remove_whitespace(element.text)
            return [f"# {text}\n"] if len(text) > 0 else []
        if element.name == "h2":
            text = remove_whitespace(element.text)
            return [f"## {text}\n"] if len(text) > 0 else []
        if element.name == "h3":
            text = remove_whitespace(element.text)
            return [f"### {text}\n"] if len(text) > 0 else []
        if element.name == "h4":
            text = remove_whitespace(element.text)
            return [f"#### {text}\n"] if len(text) > 0 else []
        if element.name == "li":
            results = [self.traverse_element(e, level + 1) for e in find_elements(element)]
            results = [item for sublist in results for item in sublist]
            return [f"{level * '*'} ", *results, "\n"]
        if element.name == "b":
            return [remove_whitespace(element.text)] if len(element.text.strip()) > 0 else []
        if element.name == "strong":
            return ["*" + remove_whitespace(element.text) + "*"] if len(element.text.strip()) > 0 else []
        if element.name == "span":
            return [remove_whitespace(element.text)] if len(element.text.strip()) > 0 else []
        if element.name == "br":
            return ["\n"]
        if element.name == "p":
            results = [self.traverse_element(e, level) for e in find_elements(element)]
            results = [item for sublist in results for item in sublist]
            return [*results, "\n"]
        if element.name == "a":
            if "href" not in element.attrs:
                return []

            href = element.attrs['href']
            if href is None:
                return []

            text = remove_whitespace(element.text)
            return [] if "javascript" in href else [f"[{text}]({href.strip()})"]

        results = [self.traverse_element(e, level) for e in find_elements(element)]
        return [item for sublist in results for item in sublist]


class TextWrapper:
    def __init__(self, text: str):
        self.name = "span"
        self.text = text
