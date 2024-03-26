from typing import Generator

from datariot.__spi__.type import Parser


class EMLParser(Parser):
    """
    Parser implementation used to parse EML files based on the fase_mail library.
    """

    def __init__(self):
        try:
            from fast_mail_parser import parse_email, ParseError
            self.parse_email = parse_email
            self.ParseError = ParseError
        except ImportError:
            raise "no fast_mail library found. install datariot[eml]"

    def parse(self, path: str) -> Generator:
        with open(path, 'rb') as file:
            message_payload = file.read()

        try:
            email = self.parse_email(message_payload)
        except self.ParseError as e:
            raise e

        contents = [item.strip() for item in email.text_plain]
        contents = [content[:content.find("<html")] for content in contents]
        contents = [content for content in contents if len(content) > 0]
        contents = [{
            "type": "eml",
            "content": content,
            "timestamp": str(email.date)
        } for content in contents]

        for content in contents:
            yield content
