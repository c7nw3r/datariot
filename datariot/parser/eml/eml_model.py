from dataclasses import dataclass

from datariot.__spi__.type import Box


@dataclass
class EMLTextBox(Box):
    """
    Box implementation for the plain text docx elements.
    """

    def __init__(self, text: str):
        super().__init__(None, None, None, None)
        self.text = text
