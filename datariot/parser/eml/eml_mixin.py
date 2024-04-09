import base64
import quopri
from email.message import Message
from typing import Optional


class EMLMixin:

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
            return half_decoded_text.decode("utf-8")
        except UnicodeDecodeError:
            return half_decoded_text.decode("latin-1")
