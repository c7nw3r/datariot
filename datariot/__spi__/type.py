from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Tuple, TypeVar, Generic, Callable

from PIL.Image import Image
from tqdm import tqdm

from datariot.__util__ import write_file
from datariot.__util__.io_util import save_image, without_ext

T = TypeVar('T')


class Formatter(ABC, Generic[T]):
    """
    tbd
    """

    @abstractmethod
    def __call__(self, box: 'Box') -> T:
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

    def intersect(self, box: 'Box', x_tolerance: int = 0, y_tolerance: int = 0):
        expr1 = ((box.x1 or 0) - x_tolerance) <= (self.x1 or 0)
        expr2 = ((box.x2 or 0) + x_tolerance) >= (self.x2 or 0)
        expr3 = ((box.y1 or 0) - y_tolerance) <= (self.y1 or 0)
        expr4 = ((box.y2 or 0) + y_tolerance) >= (self.y2 or 0)

        return expr1 and expr2 and expr3 and expr4

    @staticmethod
    def from_dict(dictionary: dict):
        return Box(x1=dictionary["x0"], y1=dictionary["y0"], x2=dictionary["x1"], y2=dictionary["y1"])

    def __repr__(self):
        return f"({self.x1},{self.y1},{self.x2},{self.y2})"

    def __iter__(self):
        yield self.x1
        yield self.y1
        yield self.x2
        yield self.y2


class MediaAware(ABC):
    """
    tbd
    """

    @abstractmethod
    def get_file(self) -> Tuple[str, Image]:
        pass

    @abstractmethod
    def to_hash(self, fast: bool = False) -> str:
        pass


@dataclass
class Parsed:
    """
    Result object of a parser invocation.
    Contains the path of the parsed document as well as all parsed boxes.
    """

    path: str
    bboxes: List[Box]
    properties: dict = field(default_factory=lambda: {})

    def render(self, evaluator, delimiter: str = "\n\n", show_progress: bool = False):
        array = tqdm(self.bboxes, disable=not show_progress, desc="render")
        return delimiter.join([e.render(evaluator) for e in array])

    def save(self, path: str,
             formatter: Formatter,
             delimiter: str = "\n\n",
             image_quality: int = 10):
        write_file(path, self.render(formatter, delimiter))

        for box in self.bboxes:
            if isinstance(box, MediaAware):
                save_image(without_ext(path), box, image_quality)


class Parser(ABC):
    """
    tbd
    """

    @abstractmethod
    def parse(self, path: str):
        pass


FontWeight = Literal["regular", "bold"]
ColumnPosition = Literal["left", "center", "right"]

FileFilter = Callable[[str], bool]
