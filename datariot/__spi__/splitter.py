from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Iterator


@dataclass
class Chunk:
    text: str
    data: dict


class Splitter(ABC):

    @abstractmethod
    def __call__(self, text: str) -> Iterator[Chunk]:
        pass
