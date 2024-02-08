from typing import List, Optional

from selenium.webdriver.remote.webdriver import By, WebElement

from datariot.__spi__.type import Box


class WebBox(Box):

    def __init__(self, element: WebElement):
        x1 = element.location["x"]
        y1 = element.location["y"]
        x2 = element.location["x"] + element.size["width"]
        y2 = element.location["y"] + element.size["height"]

        super().__init__(x1, x2, y1, y2)
        self.element = element

        self.cache = {}

    def get_attribute(self, name: str) -> Optional[str]:
        return self.element.get_attribute(name)

    @property
    def name(self):
        if "name" in self.cache:
            return self.cache["name"]
        self.cache["name"] = self.element.tag_name
        return self.cache["name"]

    @property
    def size(self):
        w = self.x2 - self.x1
        h = self.y2 - self.y1
        return w * h

    def is_strict_within(self, node: 'WebBox', x_tolerance: int = 1, y_tolerance: int = 20):
        # expr1 = (node.x1 - x_tolerance) <= self.x1
        # expr2 = (node.x2 + x_tolerance) >= self.x2
        expr3 = abs(node.y1 - self.y1) <= y_tolerance
        expr4 = abs(node.y2 - self.y2) <= y_tolerance

        return expr3 and expr4

    def is_within(self, node: 'WebBox', x_tolerance: int = 1, y_tolerance: int = 1):
        expr1 = (node.x1 - x_tolerance) <= self.x1
        expr2 = (node.x2 + x_tolerance) >= self.x2
        expr3 = (node.y1 - y_tolerance) <= self.y1
        expr4 = (node.y2 + y_tolerance) >= self.y2

        return expr1 and expr2 and expr3 and expr4

    @property
    def id(self):
        if "id" in self.cache:
            return self.cache["id"]
        self.cache["id"] = self.element.get_attribute("id")
        return self.cache["id"]

    @property
    def classes(self) -> str:
        if "classes" in self.cache:
            return self.cache["classes"]
        self.cache["classes"] = self.element.get_attribute("class").lower()
        return self.cache["classes"]

    @property
    def text(self):
        if "text" in self.cache:
            return self.cache["text"]
        self.cache["text"] = self.element.text
        return self.cache["text"]

    @property
    def is_displayed(self):
        if "is_displayed" in self.cache:
            return self.cache["is_displayed"]
        self.cache["is_displayed"] = self.element.is_displayed()
        return self.cache["is_displayed"]

    @property
    def coords(self):
        return self.x1, self.y1, self.x2, self.y2

    @property
    def font_size(self):
        font_size = self.element.value_of_css_property("fontSize")
        return float(font_size.replace("px", ""))

    def get_parent_node(self):
        if "parent_node" in self.cache:
            return self.cache["parent_node"]
        self.cache["parent_node"] = WebBox(self.element.find_element(By.XPATH, '..'))
        return self.cache["parent_node"]

    @property
    def predecessor_names(self) -> List[str]:
        names = []
        node = self.get_parent_node()
        while node.name not in ["html", "body"]:
            names.append(node.name)
            node = node.get_parent_node()

        return names

    @property
    def predecessor_ids(self) -> List[str]:
        if "predecessor_ids" in self.cache:
            return self.cache["predecessor_ids"]

        names = []
        node = self.get_parent_node()
        while node.name not in ["html", "body"]:
            names.append(node.id)
            node = node.get_parent_node()

        self.cache["predecessor_ids"] = names
        return self.cache["predecessor_ids"]

    def __repr__(self):
        return self.text


class MergedWebNode(Box):

    def __init__(self, init_node: WebBox):
        super().__init__(init_node.x1, init_node.x2, init_node.y1, init_node.y2)
        self.nodes = [init_node]

    def merge(self, node: WebBox):
        self.x1 = min(self.x1, node.x1)
        self.y1 = min(self.y1, node.y1)
        self.x2 = min(self.x2, node.x2)
        self.y2 = min(self.y2, node.y2)
        self.nodes.append(node)
