from datariot.__spi__ import Formatter, Parsed
from datariot.__spi__.type import Box
from datariot.parser.pdf import PDFTextBox


class HeuristicPDFFormatter(Formatter):

    def __init__(self, parsed: Parsed):
        boxes = [e for e in parsed.bboxes if isinstance(e, PDFTextBox)]

        sizes = ([int(e.font_size) for e in boxes])
        sizes = list(reversed(sorted(sizes)))

        if len(boxes) == 0:
            self.most_used_size = None
            self.sizes = []
        else:
            self.most_used_size = max(set(sizes), key=sizes.count)
            self.sizes = list(reversed(sorted(set(sizes))))

    def __call__(self, box: Box) -> str:
        if isinstance(box, PDFTextBox):
            return self._format_text(box)

        return box.render(self)

    def _format_text(self, box: PDFTextBox):
        if self.most_used_size is not None and int(box.font_size) > self.most_used_size:
            order = self.sizes.index(int(box.font_size))
            return ("#" * (order + 1)) + " " + box.text

        if ord(box.text[0]) == 61623:
            return " *" + box.text[1:]
        if ord(box.text[0]) == 9633:
            return " *" + box.text[1:]

        return box.text
