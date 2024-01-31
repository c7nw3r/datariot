from datariot.__spi__ import Formatter
from datariot.__spi__.type import Box
from datariot.parser.docx.docx_model import DocxTextBox


class HeuristicDocxFormatter(Formatter):

    def __init__(self, document):
        self.document = document

    def __call__(self, box: Box) -> str:
        if isinstance(box, DocxTextBox):
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

            # FIXME
            if box.font_size == 16:
                if box.text[0].isdigit():
                    return f"## {box.text}"
                return f"# {box.text}"
            return box.text

        return box.render(self)
