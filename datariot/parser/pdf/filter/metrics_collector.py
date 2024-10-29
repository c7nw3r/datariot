from math import ceil

from pdfplumber.page import Page


class MetricsCollector:

    def __init__(self, page: Page):
        import numpy as np
        _, _, max_x, max_y = page.bbox
        self.array = np.zeros((ceil(max_x), ceil(max_y)), dtype=np.byte)

        self.max_x = max_x
        self.max_y = max_y

        self.tags = {}
        self.stroking_color = {}
        self.overlapping_pixels = 0

    def __call__(self, obj) -> bool:
        import numpy as np
        tag = obj.get("tag", "None")
        color = obj.get("stroking_color", "None")

        if tag not in self.tags:
            self.tags[tag] = 0
        self.tags[tag] += 1

        if color not in self.stroking_color:
            self.stroking_color[color] = 0
        self.stroking_color[color] += 1

        x0 = ceil(obj["x0"])
        x1 = ceil(obj["x1"])
        y0 = ceil(self.max_y - obj["y0"])
        y1 = ceil(self.max_y - obj["y1"])

        subset = self.array[x0+1:x1, y1:y0]

        if 1 in subset:
            self.overlapping_pixels += np.count_nonzero(subset)
            return True

        self.array[x0:x1, y1:y0] = 1
        return True
