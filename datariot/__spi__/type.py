from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

from PIL import Image

from datariot.util import write_file
from datariot.util.io_util import get_dir


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


class MediaAware(ABC):

    @abstractmethod
    def get_file(self) -> Tuple[str, Image]:
        pass

    @abstractmethod
    def to_hash(self) -> str:
        pass


@dataclass
class Parsed:
    path: str
    bboxes: List[Box]

    def render(self, evaluator, delimiter: str = "\n\n"):
        return delimiter.join([e.render(evaluator) for e in self.bboxes])

    def save(self, path: str, formatter: Formatter, delimiter: str = "\n\n"):
        write_file(path, self.render(formatter, delimiter))

        for box in self.bboxes:
            if isinstance(box, MediaAware):
                name, file = box.get_file()
                write_file(f"{get_dir(path)}/{name}.{file.type}", file)


class Parser(ABC):

    @abstractmethod
    def parse(self, path: str):
        pass


FontWeight = Literal["regular", "bold"]
