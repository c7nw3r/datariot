from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, Optional

from datariot.util import write_file


class Formatter(ABC):

    @abstractmethod
    def __call__(self, box: 'Box'):
        pass


class Box(ABC):
    def __init__(self, x1: Optional[int], x2: Optional[int], y1: Optional[int], y2: Optional[int]):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

    def render(self, formatter: Formatter):
        return formatter(self)


@dataclass
class Parsed:
    path: str
    bboxes: List[Box]

    def render(self, evaluator):
        return "\n".join([e.render(evaluator) for e in self.bboxes])

    def save(self, path: str, formatter: Formatter):
        write_file(path, self.render(formatter))


class Parser(ABC):

    @abstractmethod
    def parse(self, path: str):
        pass


FontWeight = Literal["regular", "bold"]
