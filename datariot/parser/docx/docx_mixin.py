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
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph, Run

from datariot.__spi__.error import DataRiotException
from datariot.__util__.array_util import flatten
from datariot.__util__.image_util import from_base64
from datariot.parser.docx.docx_model import (
    DocxImageBox,
    DocxListBox,
    DocxTableBox,
    DocxTextBox,
)


# noinspection PyMethodMayBeStatic
class DocumentMixin:
    def has_numbering(self, paragraph: Paragraph):
        return len(paragraph._element.xpath("w:pPr/w:numPr/w:ilvl/@w:val")) > 0

    def has_rendered_page_breaks(self, doc: DocxDocument) -> bool:
        for para in doc.paragraphs:
            if para.rendered_page_breaks:
                return True

        return False

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
        root_name = type(root).__name__.replace("_", "").lower()

        elements = []
        curr_page_number = 1 if self.has_rendered_page_breaks(document) else None
        for block in self.iter_block_items(root):
            if isinstance(block, Paragraph):
                w_t = block._element.xpath(".//w:sdt//w:t")
                if len(block.text.strip()) > 0 or len(w_t) > 0:
                    if self.has_numbering(block):
                        elements.append(DocxListBox(root_name, block, curr_page_number))
                    else:
                        elements.append(DocxTextBox(root_name, block, curr_page_number))
                    for run in block.runs:
                        # FIXME
                        if root_name != "header":
                            elements.extend(self.parse_images(root_name, document, run))

                if curr_page_number:
                    curr_page_number += len(block.rendered_page_breaks)

            elif isinstance(block, Table):
                vf = io.StringIO()
                writer = csv.writer(vf)
                paragraphs = []
                for row in block.rows:
                    paragraphs.append(flatten([cell.paragraphs for cell in row.cells]))
                    writer.writerow(cell.text for cell in row.cells)
                vf.seek(0)

                rows = list(csv.reader(vf, delimiter=","))
                elements.append(DocxTableBox(root_name, rows, paragraphs))

        return elements

    def parse_images(self, root_name: str, document, run: Run):
        xmlstr = str(run.element.xml)
        my_namespaces = dict(
            [
                node
                for _, node in ElementTree.iterparse(
                    io.StringIO(xmlstr), events=["start-ns"]
                )
            ]
        )
        root = ET.fromstring(xmlstr)
        if "pic:pic" in xmlstr:
            for pic in root.findall(".//pic:pic", my_namespaces):
                cNvPr_elem = pic.find("pic:nvPicPr/pic:cNvPr", my_namespaces)
                name_attr = cNvPr_elem.get("name")
                blip_elem = pic.find("pic:blipFill/a:blip", my_namespaces)
                embed_attr = blip_elem.get(
                    "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"
                )
                document_part = document.part

                if embed_attr not in document_part.related_parts:
                    return []

                image_part = document_part.related_parts[embed_attr]
                image_base64 = base64.b64encode(image_part.blob)
                image_base64 = image_base64.decode()

                try:
                    image = from_base64(image_base64)
                except Exception as ex:
                    logging.warning(ex)
                    return []

                return [DocxImageBox(root_name, name_attr, image)]

        return []

    def parse_custom_properties(self, path: str) -> dict:
        import zipfile

        import lxml.etree

        try:
            zipped_file = zipfile.ZipFile(path)
            opened_file = zipped_file.open("docProps/custom.xml")
        except Exception:
            return {}

        xml = lxml.etree.parse(opened_file)
        opened_file.close()
        zipped_file.close()
        root = xml.getroot()
        name_to_value = {}

        for element in root:
            name_to_value[element.attrib["name"]] = element[0].text

        return name_to_value

    def parse_core_properties(self, document: DocxDocument) -> dict:
        core_property_names = [
            "title",
            "subject",
            "author",
            "keywords",
            "last_modified_by",
            "last_printed",
            "created",
            "modified",
            "category",
            "comments",
            "content_status",
            "identifier",
            "language",
            "revision",
            "version",
        ]

        return {
            prop: str(getattr(document.core_properties, prop))
            for prop in core_property_names
            if prop is not None and prop != ""
        }

    def parse_properties(self, path: str, document: DocxDocument) -> dict:
        custom_properties = self.parse_custom_properties(path)
        core_properties = self.parse_core_properties(document)

        return core_properties | custom_properties
