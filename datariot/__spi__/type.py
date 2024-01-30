from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal


class Formatter(ABC):

    @abstractmethod
    def format_text(self, text: 'TextBox'):
        pass


class Box(ABC):

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


@dataclass
class ParsedDocument:
    name: str
    bboxes: List[Box]

    def render(self, evaluator):
        return "\n".join([e.render(evaluator) for e in self.bboxes])


class Parser(ABC):

    @abstractmethod
    def parse(self, path: str):
        pass

FontWeight = Literal["regular", "bold"]
