import email
from email import policy
from email.message import Message
from pathlib import Path
from typing import Union

from datariot.__spi__.type import Parser, Parsed
from datariot.parser.eml.__spi__ import ParsedEML
from datariot.parser.eml.eml_mixin import EMLMixin
from datariot.parser.eml.eml_model import EMLTextBox


class EMLParser(Parser, EMLMixin):
    """
    Parser implementation used to parse EML files based on the python native email library.
    """

    def parse(self, path: Union[str, Path]) -> Parsed:
        loaded_email = self.load_email(path)

        mail_date = loaded_email["Date"]

        bboxes = self.unpack_and_decode_email(loaded_email)
        bboxes = [content for content in bboxes if len(content) > 0]
        bboxes = [EMLTextBox(e) for e in bboxes]

        return ParsedEML(path, bboxes, mail_date)

    def load_email(self, file_path: Union[str, Path]) -> Message:
        try:
            return self.load_from_file(file_path)
        except UnicodeDecodeError:
            # Backup in case of parsing error
            return self.load_from_binary_file(file_path)

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> Message:
        with open(file_path, "r") as file:
            return email.message_from_file(file, policy=policy.default)

    @staticmethod
    def load_from_binary_file(file_path: Union[str, Path]) -> Message:
        with open(file_path, "rb") as file:
            return email.message_from_binary_file(file, policy=policy.default)
