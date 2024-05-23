from copy import copy
from typing import List

from datariot.__spi__ import Formatter, Parsed
from datariot.__spi__.type import Box
from datariot.__util__.image_util import to_base64
from datariot.__util__.io_util import get_filename
from datariot.__util__.text_util import create_uuid_from_string
from datariot.parser.__spi__ import DocumentFonts
from datariot.parser.pdf.pdf_model import PDFImageBox, PDFTableBox, PDFTextBox


# from datariot.splitter import HTMLTagSplitter, RecursiveCharacterSplitter
# from datariot.__spi__.splitter import Chunk
#
# import pdfplumber
# import camelot
# import os
# import re
# import numpy as np
# import json
# from contextlib import redirect_stdout
# import hashlib


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
            return data
        elif isinstance(box, PDFTableBox):
            return data
        elif isinstance(box, PDFImageBox):
            data["data"] = to_base64(data["data"].original).decode("utf-8")
            return data


# class TablesImagesTextFormatter(HeuristicPDFFormatter):
#     def __init__(self, parsed: Parsed, enable_json: bool = False):
#         self.parsed_withtblsandimgs, self.media_list = self.process_tables_and_images(parsed)
#         super().__init__(parsed, enable_json)
#
#     def first_includes_second(self, box_tuple, box_datariot, page_height):
#         expr1 = box_tuple[0] < box_datariot.x1
#         expr2 = page_height - box_tuple[3] < box_datariot.y1
#         expr3 = box_tuple[2] > box_datariot.x2
#         expr4 = page_height - box_tuple[1] > box_datariot.y2
#         return (expr1 and expr2 and expr3 and expr4)
#
#     def is_overlapping(self, bbox1, bbox2):
#         return bbox1.x2 >= bbox2.x1 and bbox2.x2 >= bbox1.x1 and bbox1.y2 >= bbox2.y1 and bbox2.y2 >= bbox1.y1
#
#     def find_intersections(self, bbox, otherboxes):
#         same_page_boxes = [box for box in otherboxes if (bbox.page_number == box.page_number) and not (bbox == box)]
#         intersecting_boxes = [resultbox for resultbox in same_page_boxes if self.is_overlapping(bbox, resultbox)]
#         return intersecting_boxes
#
#     def find_intersections_recursive(self, bbox, otherboxes):
#         box_list = [bbox]
#         if bbox in otherboxes:
#             otherboxes.remove(bbox)
#         else:
#             return []  # was already processed in other branch of recursion
#         intersecting_boxes = self.find_intersections(bbox, otherboxes)
#         for intersecting_box in intersecting_boxes:
#             box_list.extend(self.find_intersections_recursive(intersecting_box, otherboxes))
#         return box_list
#
#     def get_group_bbox(self, group_boxes):
#         x1min = group_boxes[0].x1
#         y1min = group_boxes[0].y1
#         x2max = group_boxes[0].x2
#         y2max = group_boxes[0].y2
#         for addbox in group_boxes:
#             x1min = min(x1min, addbox.x1)
#             y1min = min(y1min, addbox.y1)
#             x2max = max(x2max, addbox.x2)
#             y2max = max(y2max, addbox.y2)
#         return x1min, y1min, x2max, y2max
#
#     def get_page_span(self, input):
#         res = re.findall('!\[pg\]\(\d+\)', input)
#         res_num = [int(x[6:9]) for x in res]
#         for match in res:
#             input = input.replace(match, " ")
#         if len(res_num) == 0:
#             return 0, 0, input
#         elif len(res_num) == 1:
#             return res_num[0], res_num[0], input
#         else:
#             return min(res_num), max(res_num), input
#
#     def process_tables_and_images(self, datariot_result):
#         pdf_reader = pdfplumber.open(datariot_result.path)
#
#         media_list = []
#         image_boxes_to_delete = []
#         processed_tables = []
#         for idx, bbox in enumerate(datariot_result.bboxes):
#             if isinstance(bbox, PDFTableBox):
#                 #print(f"TableBox on page {bbox.page_number}: Coords: {bbox.x1:.2f} {bbox.y1:.2f} {bbox.x2:.2f} {bbox.y2:.2f}")
#
#                 # get page dimensions to get the bounding boxes right
#                 page_height = pdf_reader.pages[bbox.page_number - 1].height
#
#                 offset = 0
#                 x1 = bbox.x1 - offset
#                 x2 = bbox.x2 + offset
#                 y1 = page_height - bbox.y1 - offset
#                 y2 = page_height - bbox.y2 + offset
#
#                 try:  # Try Lattice Schema
#                     tables_lat = camelot.read_pdf(datariot_result.path, pages=str(bbox.page_number), flavor="lattice",
#                                                   flag_size=False, copy_text=["h", "v"], line_scale=60,
#                                                   process_background=False, table_areas=[f"{x1},{y1},{x2},{y2}"])
#                     if len(tables_lat) == 0:
#                         lattice_acc = 0
#                     else:
#                         lattice_acc = tables_lat[0].parsing_report["accuracy"]
#                 except Exception as ex:
#                     lattice_acc = 0
#                     tables_lat = []
#
#                 try:  # Try Stream Schema
#                     tables_str = camelot.read_pdf(datariot_result.path, pages=str(bbox.page_number), flavor="stream",
#                                                   flag_size=False, row_tol=10, column_tol=10,
#                                                   table_areas=[f"{x1},{y1},{x2},{y2}"])
#                     if len(tables_str) == 0:
#                         #print("Stream failed without tables")
#                         stream_acc = 0
#                     else:
#                         stream_acc = tables_str[0].parsing_report["accuracy"]
#                 except Exception as ex:
#                     #print(f"Stream failed with Exception: {ex}")
#                     stream_acc = 0
#                     tables_str = []
#
#                 if (lattice_acc >= stream_acc) or (lattice_acc > 95.0):
#                     tables = tables_lat
#                 else:
#                     tables = tables_str
#
#                 if len(tables) == 0:  # no table found either with latice nor stream
#                     #print(f"No tables found. Text is: {bbox.__repr__()}")
#                     newtextbox = PDFTextBox(bbox.x1, bbox.y1, bbox.x2, bbox.y2, str(bbox.__repr__()), font_size=0,
#                                             font_name="", page_number=bbox.page_number)
#                     datariot_result.bboxes[idx] = newtextbox
#                 else:  # Table found --> check if there are images in table cells
#                     #print(f"Tables found. Lattice: {lattice_acc:.2f} Stream: {stream_acc:.2f}")
#                     table_bbox = tables[0]._bbox
#                     images_within_table = [box for box in datariot_result.bboxes if (isinstance(box, PDFImageBox) and (
#                                 box.page_number == bbox.page_number) and self.first_includes_second(table_bbox, box, page_height))]
#                     image_boxes_to_delete.extend(images_within_table)
#
#                     for row_idx, tbl_row in enumerate(tables[0].cells):
#                         for col_idx, tbl_cell in enumerate(tbl_row):
#                             for img_to_locate in images_within_table:
#                                 if self.first_includes_second((tbl_cell.x1, tbl_cell.y1, tbl_cell.x2, tbl_cell.y2),
#                                                          img_to_locate, page_height):
#                                     doc_name = create_uuid_from_string(os.path.basename(datariot_result.path))
#                                     img_name = create_uuid_from_string(img_to_locate.to_hash())
#                                     tables[0].df.iloc[row_idx, col_idx] += f"![Abbildung](doc/{doc_name}/{img_name})"
#                                     image_dict = {
#                                         "id": img_name,
#                                         "name": "Abbildung",
#                                         "description": "",
#                                         "source": doc_name,
#                                         "mime_type": "image/webp",
#                                         "content": to_base64(img_to_locate.crop().original).decode("utf-8"),
#                                         "properties": {}
#                                     }
#                                     media_list.append(image_dict)
#
#                     def repl_newline(x):
#                         return str(x).replace('\n', ' ')
#                     export_table = tables[0].df.map(repl_newline)
#
#                     # include table as dict
#                     newtextbox = PDFTextBox(bbox.x1, bbox.y1, bbox.x2, bbox.y2,
#                                             str(export_table.to_dict(orient="index")), font_size=0, font_name="",
#                                             page_number=bbox.page_number)
#                     datariot_result.bboxes[idx] = newtextbox
#                     processed_tables.append(export_table)
#
#         # delete image boxes that were within tables
#         for bbox_del in image_boxes_to_delete:
#             #save_image(f"./output/{create_uuid_from_string(os.path.basename(datariot_result.path))}", bbox_del)
#             datariot_result.bboxes.remove(bbox_del)
#
#         # Implement Box Merger for Images here
#         boxes_to_process = datariot_result.bboxes.copy()
#         box_groups = []
#         for idx, bbox in enumerate(datariot_result.bboxes):
#             if isinstance(bbox, PDFImageBox):
#                 if bbox in boxes_to_process:
#                     intersecting_boxes = self.find_intersections_recursive(bbox, boxes_to_process)
#                     # intersecting_boxes = [bbox] #skip grouping
#                     box_groups.append((bbox, intersecting_boxes))
#
#         group_image_boxes = []
#         for box_origin, box_group in box_groups:
#             x1, y1, x2, y2 = self.get_group_bbox(box_group)
#             newimagebox = PDFImageBox(box_origin.page, data={"x0": x1, "x1": x2, "top": y1, "bottom": y2})
#             group_image_boxes.append(newimagebox)
#             datariot_result.bboxes[datariot_result.bboxes.index(box_origin)] = newimagebox
#
#         boxes_to_remove = [box for box in datariot_result.bboxes if isinstance(box, PDFLineCurveBox) or (
#                     isinstance(box, PDFImageBox) and (box not in group_image_boxes))]
#         for box in boxes_to_remove:
#             datariot_result.bboxes.remove(box)
#
#         # Check if there are Background Images - if yes append after contained text
#         all_page_numbers = sorted(list(set([bx.page_number for bx in datariot_result.bboxes])))
#         resorted_boxlist = []
#         for page_to_process in all_page_numbers:
#             page_height = pdf_reader.pages[page_to_process - 1].height
#             page_width = pdf_reader.pages[page_to_process - 1].width
#             page_box_dummy = PDFTextBox(0, 0, page_width, page_height, "I am the page", font_size=0, font_name="",
#                                         page_number=0)
#             insert_dict = {}
#             bg_img_list = []
#             non_image_bboxes_on_page = [bx for bx in datariot_result.bboxes if
#                                         ((bx.page_number == page_to_process) and (not isinstance(bx, PDFImageBox)))]
#             image_bboxes_on_page = [bx for bx in datariot_result.bboxes if
#                                     ((bx.page_number == page_to_process) and (isinstance(bx, PDFImageBox)))]
#             for imbx in image_bboxes_on_page:
#                 intersects = self.find_intersections(imbx, non_image_bboxes_on_page)
#                 if len(intersects) > 0:  # background image
#                     # insert imbx after intersects[-1]
#                     bg_img_list.append(imbx)
#                     if intersects[-1] in insert_dict.keys():
#                         insert_dict[intersects[-1]].append(imbx)
#                     else:
#                         insert_dict[intersects[-1]] = [imbx]
#                 else:  # not a background image, leave where it is
#                     pass
#             for box in [bx for bx in datariot_result.bboxes if (bx.page_number == page_to_process)]:
#                 if box in bg_img_list:
#                     pass  # do not insert, will be inserted after last contained text
#                 else:
#                     # insert if box is on page
#                     if self.is_overlapping(box, page_box_dummy):
#                         resorted_boxlist.append(box)
#                     if box in insert_dict.keys():
#                         for insertbox in insert_dict[box]:
#                             # insert if box is on page
#                             if self.is_overlapping(insertbox, page_box_dummy):
#                                 resorted_boxlist.append(insertbox)
#
#         datariot_result.bboxes = resorted_boxlist
#
#         for idx, bbox in enumerate(datariot_result.bboxes):
#             if isinstance(bbox, PDFImageBox):
#                 doc_name = create_uuid_from_string(os.path.basename(datariot_result.path))
#                 img_name = create_uuid_from_string(bbox.to_hash())
#                 newtextbox = PDFTextBox(bbox.x1, bbox.y1, bbox.x2, bbox.y2, f"![Abbildung](doc/{doc_name}/{img_name})",
#                                         font_size=0, font_name="", page_number=bbox.page_number)
#                 image_dict = {
#                     "id": img_name,
#                     "name": "Abbildung",
#                     "description": "",
#                     "source": doc_name,
#                     "mime_type": "image/webp",
#                     "content": to_base64(bbox.crop().original).decode("utf-8"),
#                     "properties": {}
#                 }
#                 media_list.append(image_dict)
#                 datariot_result.bboxes[idx] = newtextbox
#                 #save_image(f"./output/{doc_name}", bbox)
#
#         return datariot_result, media_list
#
#
#     def process(self):
#         # count header levels and reformat to pseudo html
#         result_formatted = []
#         header_counts = {}
#         running_pagenum = 0
#         for b in self.parsed_withtblsandimgs.bboxes:
#             if b.text.startswith("#"):
#                 b.text = " " + b.text  # Hashtag at the beginning of line shall not be misinterpreted as header, therefore space is added
#             formatted = b.render(self)
#             m = re.search('^#+', formatted.split(" ")[0])
#             if m is None:
#                 if b.page_number > running_pagenum:
#                     running_pagenum = b.page_number
#                     result_formatted.append(f"![pg]({running_pagenum:03d})" + formatted)
#                 else:
#                     result_formatted.append(formatted)
#             else:
#                 header_level = len(m.group(0))
#                 if header_level in header_counts.keys():
#                     header_counts[header_level] = header_counts[header_level] + 1
#                 else:
#                     header_counts[header_level] = 1
#                 header_str = (' '.join(formatted.split(' ')[1:])).strip()
#                 if len(header_str) > 0:
#                     result_formatted.append(f"<h{header_level}>{header_str}</h{header_level}>")
#
#         # select which headers are doc title and which are used for splitting
#         title_hlevel_list = []
#         split_hlevel_list = []
#         no_split_hlevel_list = []  # need to be converted back to text-paragraphs, else eliminated by html splitter
#         num_overall_headers = sum(header_counts.values())
#         if num_overall_headers > 0:
#             for hlevel in np.arange(1, max(header_counts.keys()) + 1):
#                 if len(split_hlevel_list) == 0 and header_counts[hlevel] == 1:
#                     title_hlevel_list.append(f"<h{hlevel}>")
#                 elif header_counts[hlevel] > num_overall_headers * 0.1:
#                     split_hlevel_list.append(f"<h{hlevel}>")
#                 else:
#                     no_split_hlevel_list.append(f"<h{hlevel}>")
#         else:  # no headers found
#             pass
#
#         # extract title / remaining text is corpus
#         title = ""
#         text_corpus = ""
#         for textblock in result_formatted:
#             if textblock[0:4] in title_hlevel_list:
#                 title = title + textblock[4:-5].replace("\n", "") + " "
#                 text_corpus = text_corpus + textblock.replace(textblock[1:4], "p>") + "\n"
#             elif textblock[0:4] in split_hlevel_list:
#                 text_corpus = text_corpus + textblock + "\n"
#             elif textblock[0:4] in no_split_hlevel_list:
#                 text_corpus = text_corpus + textblock.replace(textblock[1:4], "p>") + "\n"
#             else:
#                 text_corpus = text_corpus + f"<p>" + textblock + "</p>\n"
#
#         # apply HTML Header Text Splitter
#         html_headers_to_split_on = [(x[1:3], f"Header {num + 1}") for num, x in enumerate(split_hlevel_list)]
#         html_splitter = HTMLTagSplitter(tags_to_split_on=html_headers_to_split_on,
#                                         return_each_element=False)  # datario
#
#         # Pre Split text_corpus since lxml used by HTMLHeaderTextSplitter has max num of headers to process
#         num_splittags_in_corpus = sum([len(list(re.finditer(split_tag, text_corpus))) for split_tag in
#                                        ["<" + x[0] + ">" for x in html_headers_to_split_on + ["p"]]])
#         MAX_PDF_HEADERS = 1000
#         if num_splittags_in_corpus < MAX_PDF_HEADERS:
#             pdf_splits = html_splitter(text_corpus)
#         else:
#             pdf_splits = []
#             pre_split_separators = ["<" + x[0] + ">" for x in html_headers_to_split_on] + ["<p>", "\n\n", "\n",
#                                                                                            ". ", " ", ""]
#             pre_split_chunk_size = int(len(text_corpus) / (num_splittags_in_corpus / MAX_PDF_HEADERS) / 2)
#             pdf_pre_splitter = RecursiveCharacterSplitter(separators=pre_split_separators,
#                                                           chunk_size=pre_split_chunk_size, chunk_overlap=0)
#             pre_split_text_corpus = pdf_pre_splitter.split_text(text_corpus)
#             for pre_split in pre_split_text_corpus:
#                 pdf_splits.extend(html_splitter(pre_split))
#
#         rec_text_splitter = RecursiveCharacterSplitter(chunk_size=750, chunk_overlap=0, separators=["\n\n", "\n"])
#         pdf_splits_recursive = rec_text_splitter.split_documents(pdf_splits)
#
#         document_metadata = {
#             "Title": title,
#             "source": os.path.basename(self.parsed_withtblsandimgs.path)
#         }
#
#         # Add Metadata and add Header Info to content of each chunk
#         running_page_number = 0
#         running_page_content = 0
#         running_header_text = ""
#         content = ""
#         content_list = []
#         for split in pdf_splits_recursive:
#             # Fill metadata fields of chunk
#             split.data["source"] = os.path.basename(self.parsed_withtblsandimgs.path)
#             split.data["Title"] = title
#
#             # Add page number to metadata
#             first_page, last_page, split.text = self.get_page_span(split.text)
#             if first_page >= running_page_number:
#                 running_page_number = first_page
#                 split.data["page"] = running_page_number
#                 if last_page > first_page:
#                     running_page_number = last_page
#             else:
#                 split.data["page"] = running_page_number
#
#             # Rebuild content blocks by page
#             if split.data["page"] > running_page_content:  # save previous page, start new page
#                 if len(content) > 0:  # save content
#                     newchunk = Chunk(text=content, data={"Title": document_metadata["Title"],
#                                                          "source": document_metadata["source"]})
#                     newchunk.data["page"] = running_page_content
#                     content_list.append(newchunk)
#                 else:  # no text, ignore content
#                     pass
#                 # new page started
#                 running_page_content = split.data["page"]
#                 # add correct header info
#                 header_text = (split.data["Title"] if "Title" in split.data.keys() else "") + "".join(
#                     [f" / {x}" for x in
#                      [split.data[f"Header {k}"] for k in np.arange(0, 10) if f"Header {k}" in split.data.keys()]])
#                 if running_header_text == header_text:
#                     content = ""
#                     pass  # Same header, no need to print again
#                 else:
#                     running_header_text = header_text
#                     content = header_text + "\n\n"
#                 # add content
#                 content = content + split.text
#                 split.data["offset"] = 0
#             else:  # same page
#                 split.data["offset"] = len(content) + 1
#                 # add corrent header info
#                 header_text = (split.data["Title"] if "Title" in split.data.keys() else "") + "".join(
#                     [f" / {x}" for x in
#                      [split.data[f"Header {k}"] for k in np.arange(0, 10) if f"Header {k}" in split.data.keys()]])
#                 if running_header_text == header_text:
#                     content = content + "\n"
#                 else:
#                     running_header_text = header_text
#                     content = content + "\n\n" + header_text + "\n\n"
#                 content = content + split.text
#
#             # Add Title and Header Info to content and update chunk-text
#             add_info = "Title: " + split.data["Title"] + "\n"
#             htaglist = [x for x in split.data.keys() if x.startswith("Header")]
#             for thishtag in htaglist:
#                 add_info = add_info + thishtag + ": " + split.data[thishtag] + "\n"
#             split.text = add_info + split.text
#
#         if len(content) > 0:  # save content
#             newchunk = Chunk(text=content, data=document_metadata)
#             newchunk.data["page"] = running_page_content
#             content_list.append(newchunk)
#
#         full_doc_chunks = {}
#         full_doc_chunks["metadata"] = document_metadata
#         full_doc_chunks["content"] = content_list
#
#         full_document = {}
#         full_document[os.path.basename(self.parsed_withtblsandimgs.path)] = full_doc_chunks
#
#         return pdf_splits_recursive, full_document, self.media_list
