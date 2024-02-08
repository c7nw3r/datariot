from typing import List

from tqdm import tqdm

from datariot.parser.web.web_model import WebBox, MergedWebNode


class CoordinatesBoundingBoxMerger:

    def __init__(self, x_tolerance: int = 0, y_tolerance: int = 50, show_progress: bool = False):
        self.x_tolerance = x_tolerance
        self.y_tolerance = y_tolerance
        self.show_progress = show_progress

    def __call__(self, b_boxes: List[WebBox]):
        return b_boxes

    def _merge_nodes(self, nodes: List[WebBox]) -> List[WebBox]:
        merged_nodes = []
        added_nodes = set()
        for node1 in tqdm(nodes, disable=not self.show_progress):
            if node1 in added_nodes:
                continue
            mn = MergedWebNode(node1)
            for node2 in nodes:
                if node1 is node2 or node2 in added_nodes:
                    continue
                if (
                        node2.x1 - self.x_tolerance <= node1.x1 <= node2.x1 + self.x_tolerance and
                        (
                                node2.y1 - self.y_tolerance <= node1.y2 <= node2.y1 + self.y_tolerance or
                                node1.y1 - self.y_tolerance <= node2.y2 <= node1.y1 + self.y_tolerance
                        )
                ):
                    mn.nodes.extend(node2.nodes)
                    added_nodes.add(node2)

            merged_nodes.append(mn)
            added_nodes.add(node1)

        return merged_nodes
