from typing import List

from tqdm import tqdm

from datariot.parser.web.web_model import WebBox


class DomCollapseBoundingBoxFilter:

    def __init__(self, show_progress: bool = False):
        self.show_progress = show_progress

        self.levels = {
            "h1": 3,
            "h2": 3,
            "h3": 3,
            "h4": 3,
            "h5": 3,
            "h6": 3,
            "p": 2,
            "strong": 1,
            "b": 1,
        }

    def __call__(self, boxes: List[WebBox]):
        keep_nodes = []
        for node1 in tqdm(boxes, disable=not self.show_progress, desc="dom collapse"):
            is_nested_duplicate = False
            for node2 in boxes:
                level1 = self.levels.get(node1.name, 0)
                level2 = self.levels.get(node2.name, 0)

                if node1 is node2:
                    continue
                if (
                        node1.text.strip() in node2.text.strip() and
                        node1.is_within(node2) and
                        (level1 <= level2 or node1.x2 <= node2.x2)
                ):
                    is_nested_duplicate = True
                    break

            if not is_nested_duplicate:
                keep_nodes.append(node1)

        return keep_nodes


class ExcludeListBoundingBoxFilter:

    def __init__(self, show_progress: bool = False):
        self.show_progress = show_progress

    def __call__(self, boxes: List[WebBox]):
        def is_not_excluded(node: WebBox) -> bool:
            ids = node.predecessor_ids
            # FIXME: remove
            if "suiteBar" in ids:
                return False
            # FIXME: remove
            if "titleAreaBox" in ids:
                return False
            return True

        result = []
        for box in tqdm(boxes, disable=not self.show_progress, desc="exclude list"):
            if is_not_excluded(box):
                result.append(box)
        return result
