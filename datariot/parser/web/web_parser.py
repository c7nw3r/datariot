import logging
from typing import List

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.remote.webdriver import By, WebDriver
from webdriver_manager.chrome import ChromeDriverManager

from datariot.__spi__ import Parsed
from datariot.__util__.array_util import flatten
from datariot.__util__.io_util import get_files
from datariot.parser.web.bbox.bbox_filter import DomCollapseBoundingBoxFilter, ExcludeListBoundingBoxFilter
from datariot.parser.web.bbox.bbox_sorter import CoordinatesBoundingBoxSorter
from datariot.parser.web.web_mixin import WebMixin, USER_AGENT
from datariot.parser.web.web_model import WebBox


class WebParser(WebMixin):
    def __init__(self, root: str = "//"):
        self._driver = None

        self.xpaths = [
            f"{root}h1",
            f"{root}h2",
            f"{root}h3",
            f"{root}h4",
            f"{root}p",
            f"{root}article",
            f"{root}small",
            f"{root}span",
            f"{root}ul",
            f"{root}a",
            f"{root}table",
            f"{root}strong",
            # FIXME: remove
            f'{root}div[contains(@class, "ms-rteFontSize-2")]',
            # FIXME: remove
            f'{root}div[contains(@style, "font-size:9pt")]',
        ]

    def __call__(self, url: str, handle_cookies: bool = True) -> Parsed:
        self._driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()),
                                        options=self.get_options())
        # self._driver = webdriver.Chrome(service=self.get_service(), options=self.get_options())
        # self._driver.set_page_load_timeout(LOAD_TIMEOUT)
        self._driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": USER_AGENT})
        # self._driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        self._driver.implicitly_wait(1)
        self._driver.get(url)

        # body = self._driver.find_elements(By.XPATH, "//html")[0]
        # body = body.get_attribute('outerHTML')

        if handle_cookies:
            self.accept_cookies(self._driver)

        # total_height = self._driver.execute_script("return document.body.scrollHeight")
        total_height = 1000
        width = self._driver.get_window_size()["width"]
        self._driver.set_window_size(width=1500, height=3000)

        # soup = BeautifulSoup(webpage.content, "html.parser")
        # dom = etree.HTML(str(soup))
        # print(dom.xpath('//*[@id="firstHeading"]')[0].text)

        boxes = self._find_candidates(self._driver)
        boxes = self._filter_candidates(boxes)

        box_sorter = CoordinatesBoundingBoxSorter()
        box_filter = DomCollapseBoundingBoxFilter(show_progress=True)
        box_ignore = ExcludeListBoundingBoxFilter(show_progress=True)
        boxes = box_sorter(boxes)
        boxes = box_filter(boxes)
        boxes = box_ignore(boxes)

        self.take_screenshot(self._driver, boxes)

        return Parsed(url, boxes)

    def _find_candidates(self, driver: WebDriver):
        candidates = flatten([driver.find_elements(By.XPATH, xpath) for xpath in self.xpaths])
        return [WebBox(e) for e in candidates]

    @staticmethod
    def _filter_candidates(candidates: List[WebBox]):
        def is_empty(wn: WebBox) -> bool:
            return bool(wn.text.strip())

        def is_displayed(wn: WebBox) -> bool:
            # _class = wn.classes
            # if "noindex" in _class or "hidden" in _class:
            #     return False

            return wn.is_displayed

        def is_not_nav(wn: WebBox) -> bool:
            return "nav" not in wn.predecessor_names

        def is_not_header(wn: WebBox) -> bool:
            return not ("header" in wn.predecessor_names and wn.y1 < 150)

        def is_not_footer(wn: WebBox) -> bool:
            return not ("footer" in wn.predecessor_names)

        def is_not_link(wn: WebBox) -> bool:
            return not ("a" in wn.predecessor_names)

        filters = [
            is_empty,
            is_displayed,
            # is_not_nav,
            # is_not_header,
            # is_not_footer,
            # is_not_link
            # is_not_excluded
        ]

        candidates = [wn for wn in candidates if all(f(wn) for f in filters)]
        return candidates

    @staticmethod
    def parse_folder(path: str, root: str = "//"):
        parser = WebParser(root=root)

        for file in get_files(path, "html", recursive=False):
            try:
                yield parser(f"file:////{file}")
            except OSError as ex:
                logging.warning(ex)
