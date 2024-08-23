import csv

from datariot.__spi__.type import Parser, Parsed
from datariot.parser.csv.__spi__ import CsvParserConfig
from datariot.parser.csv.csv_model import CsvLineBox, CsvTextBox


class CsvParser(Parser):

    def __init__(self, config: CsvParserConfig = CsvParserConfig()):
        self.config = config

    def parse(self, path: str):
        with open(path, newline=self.config.newline) as csvfile:
            reader = csv.reader(csvfile, delimiter=self.config.delimiter, quotechar=self.config.quotechar)
            bboxes = [CsvLineBox(e) for e in reader]

            if self.config.skip_header:
                bboxes = bboxes[1:]

            if self.config.template is not None:
                bboxes = [self.config.template.format(*e.row) for e in bboxes]
                bboxes = [CsvTextBox(e) for e in bboxes]

            return Parsed(path, bboxes)
