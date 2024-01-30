from abc import abstractmethod
from typing import Protocol


class BoxProto(Protocol):
    pass


class TextProto(BoxProto):

    @property
    @abstractmethod
    def text(self) -> str:
        pass

    @property
    @abstractmethod
    def font_size(self) -> int:
        pass

    @property
    @abstractmethod
    def style_name(self) -> str:
        pass
