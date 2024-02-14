from typing import List

from datariot.parser.__spi__ import DocumentFonts, Font, FontSpecification
from datariot.parser.pdf.pdf_model import PDFTextBox


# TODO: generalize to arbitrary text boxes
def check_font_specs(box: PDFTextBox, doc_fonts: DocumentFonts, specs: List[FontSpecification]) -> bool:
    for spec in specs:
        if isinstance(spec, Font):
            if not (
                (not spec.name or spec.name == box.font_name)
                and (not spec.size or spec.size == box.font_size)
                and (not spec.weight or spec.weight == box.font_weight)
            ):
                return False
        elif spec == "minimum_size" and box.font_size != doc_fonts.min_size:
            return False
        elif spec == "maximum_size" and box.font_size != doc_fonts.max_size:
            return False
        elif spec == "most_common_size" and box.font_size != doc_fonts.most_common_size:
            return False

    return True
