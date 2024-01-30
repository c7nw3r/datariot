import csv
import io

from datariot.__spi__.error import DataRiotImportException, DataRiotException
from datariot.__spi__.type import ParsedDocument, Parser
from datariot.util.io_util import get_filename, get_files


class DocxParser(Parser):

    def parse(self, path: str):
        try:
            from docx import Document
            from docx.document import Document as DocxDocument
            from docx.oxml.table import CT_Tbl
            from docx.oxml.text.paragraph import CT_P
            from docx.table import _Cell, Table
            from docx.text.paragraph import Paragraph
            from datariot.parser.docx import docx_model
        except ImportError:
            raise DataRiotImportException("docx")

        try:
            document = Document(path)
        except:
            raise DataRiotException("error while opening docx file " + path)

        def iter_block_items(parent):
            if isinstance(parent, DocxDocument):
                parent_elm = parent.element.body
            elif isinstance(parent, _Cell):
                parent_elm = parent._tc
            else:
                raise DataRiotException("error while parsing docx block")

            for child in parent_elm.iterchildren():
                if isinstance(child, CT_P):
                    yield Paragraph(child, parent)
                elif isinstance(child, CT_Tbl):
                    yield Table(child, parent)

        elements = []
        for block in iter_block_items(document):
            if isinstance(block, Paragraph):
                if len(block.text.strip()) > 0:
                    elements.append(docx_model.DocxTextBox(block))

            elif isinstance(block, Table):
                vf = io.StringIO()
                writer = csv.writer(vf)
                for row in block.rows:
                    writer.writerow(cell.text for cell in row.cells)
                vf.seek(0)

                rows = list(csv.reader(vf, delimiter=','))
                elements.append(docx_model.DocxTableBox(rows))

        return ParsedDocument(get_filename(path), elements)

    @staticmethod
    def parse_folder(path: str):
        parsed = []
        parser = DocxParser()

        for file in get_files(path, ".docx"):
            try:
                parsed.append(parser.parse(file))
            except ValueError:
                continue

        return parsed
