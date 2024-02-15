from copy import copy
from typing import List

from datariot.__spi__ import Formatter, Parsed
from datariot.__spi__.type import Box
from datariot.parser.__spi__ import DocumentFonts
from datariot.parser.pdf import PDFImageBox, PDFTableBox, PDFTextBox
from datariot.util.image_util import to_base64
from datariot.util.io_util import get_filename
from datariot.util.text_util import create_uuid_from_string


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

        # TODO: infinite recursion?
        # return box.render(self)
        return repr(box)

    def _format_text(self, box: PDFTextBox):
        if self._doc_fonts.most_common_size and box.font_size > self._doc_fonts.most_common_size:
            order = self._doc_fonts.get_size_rank(box.font_size)
            return ("#" * (order + 1)) + " " + box.text

        return box.text

    def _format_table(self, box: PDFTableBox):
        if len(box.rows) <= 5 or not self.enable_json:
            return box.__repr__()

        try:
            # convert the rows to json lines
            header = [e for e in box.rows[0] if e is not None and len(e) > 0]

            def to_dict(row: List[str]):
                row = [e for e in row if e is not None and len(e) > 0]
                return {header[i]: self._format_table_cell(e) for i, e in enumerate(row)}

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
            img_name = create_uuid_from_string(box.to_hash())
            # FIXME: language
            return f"![Abbildung](doc/{doc_name}/{img_name})"
        except OSError:
            return ""


class JSONPDFFormatter(Formatter[dict]):

    def __call__(self, box: Box) -> dict:
        data = copy(box.__dict__)
        data["type"] = box.__class__.__name__

        if isinstance(box, PDFTextBox):
            return data
        elif isinstance(box, PDFTableBox):
            return data
        elif isinstance(box, PDFImageBox):
            data["data"] = to_base64(data["data"].original).decode("utf-8")
            return data
