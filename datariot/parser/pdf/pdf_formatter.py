from copy import copy
from dataclasses import asdict
from typing import Callable, List, Tuple

from datariot.__spi__ import Formatter, Parsed
from datariot.__spi__.type import Box
from datariot.__util__.image_util import to_base64
from datariot.__util__.io_util import get_filename
from datariot.__util__.text_util import create_uuid_from_string
from datariot.parser.__spi__ import DocumentFonts
from datariot.parser.pdf.pdf_model import (
    PDFImageBox,
    PDFTableBox,
    PDFTextBox,
    PDFTextBoxAnnotation,
)


class HeuristicPDFFormatter(Formatter[str]):
    def __init__(self, parsed: Parsed, enable_json: bool = False):
        self.enable_json = enable_json

        self._doc_fonts = DocumentFonts.from_bboxes(
            [b for b in parsed.bboxes if isinstance(b, PDFTextBox)]
        )

        self.doc_path = parsed.path

    def __call__(self, box: Box) -> str:
        if isinstance(box, PDFTextBox):
            return self._format_text(box)
        if isinstance(box, PDFTableBox):
            return self._format_table(box)
        if isinstance(box, PDFImageBox):
            return self._format_image(box)

        return repr(box)

    def _format_text(self, box: PDFTextBox):
        text = box.text
        offset = 0
        for link in box.hyperlinks:
            text, curr_offset = self._insert_hyperlink(text, link, offset)
            offset += curr_offset

        if (
            self._doc_fonts.most_common_size
            and box.font_size > self._doc_fonts.most_common_size
        ):
            order = self._doc_fonts.get_size_rank(box.font_size)

            text = ("#" * (order + 1)) + " " + text

        return text

    def _insert_hyperlink(
        self, text: str, link: PDFTextBoxAnnotation, offset: int
    ) -> Tuple[str, int]:
        if link.uri is None:
            return text, 0

        start_idx = link.start_idx + offset
        end_idx = link.end_idx + 1 + offset
        before = text[:start_idx]
        after = text[end_idx:]
        replaced = f" [{text[start_idx: end_idx]}]({link.uri}) "

        return f"{before}{replaced}{after}", len(link.uri) + 6

    def _format_table(self, box: PDFTableBox):
        if len(box.rows) <= 5 or not self.enable_json:
            return box.__repr__()

        try:
            # convert the rows to json lines
            header = [e for e in box.rows[0] if e is not None and len(e) > 0]

            def to_dict(row: List[str]):
                row = [e for e in row if e is not None and len(e) > 0]
                return {
                    header[i]: self._format_table_cell(e) for i, e in enumerate(row)
                }

            import json

            rows = [to_dict(e) for e in box.rows[1:]]
            return "\n".join([json.dumps(e) for e in rows])
        except IndexError:
            return box.__repr__()

    def _format_table_cell(self, text: str):
        return text

    def _format_image(self, box: PDFImageBox):
        try:
            doc_name = create_uuid_from_string(get_filename(self.doc_path))
            img_name = create_uuid_from_string(box.to_hash(fast=True))
            # FIXME: language
            return f"![Abbildung](doc/{doc_name}/{img_name})"
        except OSError:
            return ""


class JSONPDFFormatter(Formatter[dict]):
    def __call__(self, box: Box) -> dict:
        data = copy(box.__dict__)
        data["type"] = box.__class__.__name__

        if isinstance(box, PDFTextBox):
            data["hyperlinks"] = [asdict(h) if h else None for h in box.hyperlinks]
            return data
        elif isinstance(box, PDFTableBox):
            return data
        elif isinstance(box, PDFImageBox):
            data["data"] = to_base64(data["data"].original).decode("utf-8")
            return data
