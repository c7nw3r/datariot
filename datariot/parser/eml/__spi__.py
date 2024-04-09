from dataclasses import dataclass

from datariot.__spi__ import Parsed


@dataclass
class ParsedEML(Parsed):
    timestamp: str
