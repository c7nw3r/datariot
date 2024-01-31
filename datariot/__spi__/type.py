from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal


class Formatter(ABC):

    @abstractmethod
    def format_text(self, text: 'TextBox'):
        pass

    @abstractmethod
    def format_image(self, image: 'ImageBox'):
        pass


class Box(ABC):
    x1: int
    x2: int
    y1: int
    y2: int

    @abstractmethod
    def render(self, formatter: Formatter):
        pass


class TextBox(Box):

    @property
    @abstractmethod
    def text(self) -> str:
        pass

    @property
    @abstractmethod
    def font_size(self) -> int:
        pass

    def render(self, formatter: Formatter):
        return formatter.format_text(self)


class TableBox(Box):
    pass


class ImageBox(Box):
    def render(self, formatter: Formatter):
        return formatter.format_image(self)


@dataclass
class ParsedDocument:
    path: str
    name: str  # TODO: remove
    bboxes: List[Box]

    def render(self, evaluator):
        return "\n".join([e.render(evaluator) for e in self.bboxes])


class Parser(ABC):

    @abstractmethod
    def parse(self, path: str):
        pass


FontWeight = Literal["regular", "bold"]
