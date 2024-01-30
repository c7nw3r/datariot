from datariot.__spi__ import Formatter, TextBox


class HeuristicDocxFormatter(Formatter):

    def __init__(self, document):
        self.document = document

    def format_text(self, text: TextBox) -> str:
        if text.style_name == "Title":
            return f"# {text.text}"

        if text.style_name == "Heading 1":
            return f"## {text.text}"
        if text.style_name == "Heading 2":
            return f"### {text.text}"
        if text.style_name == "Heading 3":
            return f"### {text.text}"
        if text.style_name == "List Paragraph":
            return f" * {text.text}"

        if text.style_name == "Title":
            return f"# {text.text}"

        if text.font_size == 16:
            if text.text[0].isdigit():
                return f"## {text.text}"
            return f"# {text.text}"
        return text.text
