from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple

from PIL.Image import Image

from datariot.util import write_file
from datariot.util.io_util import without_ext, save_image
from datariot.util.text_util import create_uuid_from_string


class Formatter(ABC):
    """
    tbd
    """

    @abstractmethod
    def __call__(self, box: 'Box'):
        pass


class Box(ABC):
    """
    tbd
    """

    def __init__(self, x1: Optional[int], x2: Optional[int], y1: Optional[int], y2: Optional[int]):
        self.x1 = x1
        self.x2 = x2
        self.y1 = y1
        self.y2 = y2

    def render(self, formatter: Formatter):
        return formatter(self)


class MediaAware(ABC):
    """
    tbd
    """

    @abstractmethod
    def get_file(self) -> Tuple[str, Image]:
        pass

    @abstractmethod
    def to_hash(self) -> str:
        pass


@dataclass
class Parsed:
    """
    Result object of a parser invocation.
    Contains the path of the parsed document as well as all parsed boxes.
    """

    path: str
    bboxes: List[Box]

    def render(self, evaluator, delimiter: str = "\n\n"):
        return delimiter.join([e.render(evaluator) for e in self.bboxes])

    def save(self, path: str,
             formatter: Formatter,
             delimiter: str = "\n\n",
             image_quality: int = 10):
        write_file(path, self.render(formatter, delimiter))

        for box in self.bboxes:
            if isinstance(box, MediaAware):
                _, file = box.get_file()
                name = create_uuid_from_string(box.to_hash())
                save_image(f"{without_ext(path)}/{name}.webp", file, image_quality)


class Parser(ABC):
    """
    tbd
    """

    @abstractmethod
    def parse(self, path: str):
        pass


FontWeight = Literal["regular", "bold"]
