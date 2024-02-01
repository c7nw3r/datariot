from datariot.__spi__ import Formatter
from datariot.__spi__.type import Box, Parsed
from datariot.parser.docx.docx_model import DocxTextBox, DocxImageBox, DocxTableBox
from datariot.util.text_util import create_uuid_from_string


class HeuristicDocxFormatter(Formatter):

    def __init__(self, parsed: Parsed):
        boxes = [e for e in parsed.bboxes if isinstance(e, DocxTextBox)]

        sizes = ([int(e.font_size) for e in boxes])
        sizes = list(reversed(sorted(sizes)))

        if len(boxes) == 0:
            self.most_used_size = None
            self.sizes = []
        else:
            self.most_used_size = max(set(sizes), key=sizes.count)
            self.sizes = list(reversed(sorted(set(sizes))))

    def __call__(self, box: Box) -> str:
        if isinstance(box, DocxTextBox):
            return self._format_text(box)
        if isinstance(box, DocxImageBox):
            return self._format_image(box)
        if isinstance(box, DocxTableBox):
            return self._format_table(box)

        return str(box)

    def _format_text(self, box: DocxTextBox):
        if box.style_name == "Title":
            return f"# {box.text}"

        if box.style_name == "Heading 1":
            return f"## {box.text}"
        if box.style_name == "Heading 2":
            return f"### {box.text}"
        if box.style_name == "Heading 3":
            return f"### {box.text}"
        if box.style_name == "List Paragraph":
            return f" * {box.text}"

        if self.most_used_size is not None and int(box.font_size) > self.most_used_size:
            order = self.sizes.index(int(box.font_size))
            return ("#" * (order + 1)) + " " + box.text

        return box.text

    def _format_image(self, image: DocxImageBox):
        try:
            name = create_uuid_from_string(image.to_hash())
            return f"![Abbildung]({name})"
        except OSError:
            return ""

    def _format_table(self, box: DocxTableBox):
        return box.__repr__()
