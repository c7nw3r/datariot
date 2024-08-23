from typing import List, TypeVar


T = TypeVar("T")


def flatten(array: List[List[T]]) -> List[T]:
    return [e for sublist in array for e in sublist]


def filter_none(array: List):
    return [e for e in array if e is not None]
