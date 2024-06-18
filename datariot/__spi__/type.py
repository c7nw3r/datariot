import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from math import ceil, floor
from typing import Callable, Generic, List, Literal, Optional, Tuple, TypeVar

from PIL.Image import Image
from tqdm import tqdm

from datariot.__util__ import write_file
from datariot.__util__.array_util import filter_none
from datariot.__util__.io_util import save_image, without_ext


T = TypeVar("T")


class Formatter(ABC, Generic[T]):
    """
    tbd
    """

    @abstractmethod
    def __call__(self, box: "Box") -> T:
        pass


class Box:
    """
    tbd
    """

    def __init__(
        self,
        x1: Optional[float],
        x2: Optional[float],
        y1: Optional[float],
        y2: Optional[float],
    ):
        self.x1 = floor(x1) if x1 is not None else None
        self.x2 = ceil(x2) if x2 is not None else None
        self.y1 = floor(y1) if y1 is not None else None
        self.y2 = ceil(y2) if y2 is not None else None

    @property
    def width(self) -> int:
        assert self.x1 is not None
        assert self.x2 is not None

        return abs(self.x2 - self.x1)

    @property
    def height(self) -> int:
        assert self.y1 is not None
        assert self.y2 is not None

        return abs(self.y2 - self.y1)

    @property
    def size(self) -> int:
        return self.width * self.height

    def is_contained_in(self, box: "Box") -> bool:
        expr1 = self.x1 >= box.x1
        expr2 = self.x2 <= box.x2
        expr3 = self.y1 >= box.y1
        expr4 = self.y2 <= box.y2

        if all([expr1, expr2, expr3, expr4]):
            return True

        return False

    def render(self, formatter: Formatter):
        return formatter(self)

    def intersect(self, box: "Box", x_tolerance: int = 0, y_tolerance: int = 0):
        expr1 = ((box.x1 or 0) - x_tolerance) <= (self.x1 or 0)
        expr2 = ((box.x2 or 0) + x_tolerance) >= (self.x2 or 0)
        expr3 = ((box.y1 or 0) - y_tolerance) <= (self.y1 or 0)
        expr4 = ((box.y2 or 0) + y_tolerance) >= (self.y2 or 0)

        return expr1 and expr2 and expr3 and expr4

    @staticmethod
    def from_dict(dictionary: dict):
        return Box(
            x1=dictionary["x0"],
            y1=dictionary["y0"],
            x2=dictionary["x1"],
            y2=dictionary["y1"],
        )

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

    @property
    @abstractmethod
    def id(self) -> str:
        pass

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

    @property
    def is_paged(self) -> bool:
        return False

    def render(self, evaluator, delimiter: str = "\n\n", show_progress: bool = False):
        array = tqdm(self.bboxes, disable=not show_progress, desc="render")
        return delimiter.join(filter_none([e.render(evaluator) for e in array]))

    def filter_by(self, expression: Callable[[Box], bool]):
        bboxes = [e for e in self.bboxes if expression(e)]
        return Parsed(self.path, bboxes, self.properties)

    def save(
        self,
        path: str,
        formatter: Formatter,
        delimiter: str = "\n\n",
        image_quality: int = 10,
    ):
        write_file(path, self.render(formatter, delimiter))

        for box in self.bboxes:
            if isinstance(box, MediaAware):
                save_image(without_ext(path), box, image_quality)

        if len(self.properties) > 0:
            write_file(without_ext(path) + ".json", json.dumps(self.properties))


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


def starts_with_filter(prefix: str) -> FileFilter:
    return lambda file: file[file.rfind("/") + 1 :].startswith(prefix)
