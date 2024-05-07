import base64
import csv
import io
import logging
import xml.etree.ElementTree as ET
from xml.etree import ElementTree

from docx.document import Document as DocxDocument
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.section import _Header
from docx.table import _Cell, Table
from docx.text.paragraph import Paragraph, Run

from datariot.__spi__.error import DataRiotException
from datariot.__util__.image_util import from_base64
from datariot.parser.docx.docx_model import DocxTextBox, DocxTableBox, DocxImageBox, DocxListBox


# noinspection PyMethodMayBeStatic
class DocumentMixin:

    def has_numbering(self, paragraph: Paragraph):
        return len(paragraph._element.xpath("w:pPr/w:numPr/w:ilvl/@w:val")) > 0

    def iter_block_items(self, parent):
        if isinstance(parent, DocxDocument):
            parent_elm = parent.element.body
        elif isinstance(parent, _Cell):
            parent_elm = parent._tc
        elif isinstance(parent, _Header):
            for e in parent.iter_inner_content():
                yield e
            return
        else:
            raise DataRiotException("error while parsing docx block")

        for child in parent_elm.iterchildren():
            if isinstance(child, CT_P):
                yield Paragraph(child, parent)
            elif isinstance(child, CT_Tbl):
                yield Table(child, parent)

    def parse_elements(self, document, root):
        elements = []
        for block in self.iter_block_items(root):
            if isinstance(block, Paragraph):
                if len(block.text.strip()) > 0:
                    if self.has_numbering(block):
                        elements.append(DocxListBox(block))
                    else:
                        elements.append(DocxTextBox(block))
                    for run in block.runs:
                        elements.extend(self.parse_images(document, run))

            elif isinstance(block, Table):
                vf = io.StringIO()
                writer = csv.writer(vf)
                for row in block.rows:
                    writer.writerow(cell.text for cell in row.cells)
                vf.seek(0)

                rows = list(csv.reader(vf, delimiter=','))
                elements.append(DocxTableBox(rows))

        return elements

    def parse_images(self, document, run: Run):
        xmlstr = str(run.element.xml)
        my_namespaces = dict([node for _, node in ElementTree.iterparse(io.StringIO(xmlstr), events=['start-ns'])])
        root = ET.fromstring(xmlstr)
        if 'pic:pic' in xmlstr:
            for pic in root.findall('.//pic:pic', my_namespaces):
                cNvPr_elem = pic.find("pic:nvPicPr/pic:cNvPr", my_namespaces)
                name_attr = cNvPr_elem.get("name")
                blip_elem = pic.find("pic:blipFill/a:blip", my_namespaces)
                embed_attr = blip_elem.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                document_part = document.part

                if embed_attr not in document_part.related_parts:
                    return []

                image_part = document_part.related_parts[embed_attr]
                image_base64 = base64.b64encode(image_part._blob)
                image_base64 = image_base64.decode()

                try:
                    image = from_base64(image_base64)
                except Exception as ex:
                    logging.warning(ex)
                    return []

                return [DocxImageBox(name_attr, image)]

        return []
