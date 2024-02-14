from abc import ABC, abstractmethod
from typing import Iterator


class Splitter(ABC):

    @abstractmethod
    def __call__(self, text: str) -> Iterator[str]:
        pass
