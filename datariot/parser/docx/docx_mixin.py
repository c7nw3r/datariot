from typing import List

from docx.text.run import Run


class DocxStyleMixin:
    def get_max_font_size(self, runs: List[Run]) -> int:
        max_size = -1
        for run in runs:
            font_size = int(run.font.size.pt) if run.font.size is not None else -1
            if font_size > max_size:
                max_size = run.font.size.pt

            if max_size == -1:
                array = run.element.xpath("./w:rPr/w:szCs/@w:val")
                if len(array) > 0:
                    max_size = int(array[0]) / 2

        return max_size

    def get_default_font_size(self, doc):
        try:
            styles_element = doc.styles.element

            r_pr_default = styles_element.xpath('w:docDefaults/w:rPrDefault/w:rPr/w:sz')[0]
            return r_pr_default.val.pt
        except:
            return -1
