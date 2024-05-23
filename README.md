problem with pdfplumber version > 11
bounding box reihenfolge unterschiedlich

pdfplumber auf version 0.10.4 festgelegt, weil version 0.11.0 in der Funktion
extract_words(
extra_attrs=config.extract_words_extra_attrs,
keep_blank_chars=config.extract_words_keep_blank_chars,
x_tolerance=config.parser_x_tolerance,
y_tolerance=config.parser_y_tolerance
)
die zurückgegebene box-Reihenfolge nicht sortiert, sobald der parameter "extra_attrs" befüllt ist. Das führt dazu dass Textboxen falsch gemerged werden.