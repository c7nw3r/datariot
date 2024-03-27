from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class Chunk:
    text: str
    data: dict = field(default_factory=lambda: {})


class Splitter(ABC):

    @abstractmethod
    def __call__(self, text: str) -> List[Chunk]:
        pass
