from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Literal, Optional, Tuple, TypeVar, Generic

from PIL.Image import Image
from tqdm import tqdm

from datariot.util import write_file
from datariot.util.io_util import save_image, without_ext

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
