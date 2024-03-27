from typing import Union, Optional
from pathlib import Path
import base64

import email
from email.message import Message
from email import policy

import quopri

from datariot.__spi__.type import Parser


class EMLParser(Parser):
    """
    Parser implementation used to parse EML files based on the fase_mail library.
    """

    def __init__(self):
        try:
            # Left as placeholder in case other mandatory packages
            # are included at a later point in time
            pass

        except ImportError:
            raise "no fast_mail library found. install datariot[eml]"

    def parse(self, path: Union[str, Path]) -> list:

        loaded_email = self.load_email(path)

        mail_date = loaded_email["Date"]

        email_contents = self.unpack_and_decode_email(loaded_email)
        email_contents = [content for content in email_contents if len(content) > 0]

        email_contents = [{
            "type": "eml",
            "content": content,
            "timestamp": mail_date
        } for content in email_contents]

        return email_contents

    def load_email(self, file_path: Union[str, Path]) -> Message:

        try:
            loaded_email = self.load_from_file(file_path)

        except UnicodeDecodeError:
            # Backup in case of parsing error
            loaded_email = self.load_from_binary_file(file_path)

        return loaded_email

    @staticmethod
    def load_from_file(file_path: Union[str, Path]) -> Message:

        with open(file_path, "r") as file:
            loaded_email = email.message_from_file(file, policy=policy.default)

        return loaded_email

    @staticmethod
    def load_from_binary_file(file_path: Union[str, Path]) -> Message:

        with open(file_path, "rb") as file:
            loaded_email = email.message_from_binary_file(file, policy=policy.default)

        return loaded_email

    def unpack_and_decode_email(self, input_email: Message) -> list:
        decoded_email_parts = []

        if input_email.is_multipart():
            email_parts = input_email.get_payload()
        else:
            email_parts = [input_email]

        for current_part in email_parts:

            if current_part.is_multipart():
                subpart_payloads = self.unpack_and_decode_email(current_part)
                decoded_email_parts.extend(subpart_payloads)

            else:
                current_part_payload = current_part.get_payload()
                email_encoding = current_part['Content-Transfer-Encoding']
                try:
                    current_decoded_part = self.decode(current_part_payload, encoding=email_encoding)
                except ValueError:
                    current_decoded_part = ""

                decoded_email_parts.append(current_decoded_part)

        return decoded_email_parts

    @staticmethod
    def decode(input_text: str, encoding: Optional[str]) -> str:

        # Get encoding
        if encoding is None or encoding == "" or encoding == "8bit":
            # assume its utf-8 encoding
            half_decoded_text = input_text.encode("utf-8")

        elif encoding == "7bit":
            half_decoded_text = quopri.decodestring(input_text)

        elif encoding == "base64" or encoding == "Base64":
            half_decoded_text = base64.b64decode(input_text.encode("utf8"))

        elif encoding == "quoted-printable":
            half_decoded_text = quopri.decodestring(input_text)

        else:
            raise ValueError(f"Unknown encoding '{encoding}'")

        # Then decode
        # decoding_schemes = ["utf-8", "latin-1"]
        try:
            decoded_text = half_decoded_text.decode("utf-8")
        except UnicodeDecodeError:
            decoded_text = half_decoded_text.decode("latin-1")

        return decoded_text
