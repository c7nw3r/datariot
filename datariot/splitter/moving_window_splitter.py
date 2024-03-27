from typing import Iterator

from datariot.__spi__.error import DataRiotException
from datariot.__spi__.splitter import Splitter, Chunk


class MovingWindowSplitter(Splitter):

    def __init__(self, size: int, overlap: int):
        self.size = size
        self.overlap = overlap

        if size < 1 or overlap < 0:
            raise DataRiotException('size must be >= 1 and overlap >= 0')

    def __call__(self, text: str) -> Iterator[Chunk]:
        if len(text) < self.size:
            yield Chunk(text, {})
            return

        for i in range(0, len(text) - self.overlap, self.size - self.overlap):
            yield Chunk(text[i:i + self.size])
