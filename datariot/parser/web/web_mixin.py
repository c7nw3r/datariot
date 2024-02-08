from io import BytesIO
from typing import Optional, List

from PIL import Image, ImageDraw
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.remote.webdriver import By

from datariot.parser.web.web_model import WebBox

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36"
LOAD_TIMEOUT = 300


class WebMixin:
    def get_service(self, driver_location: Optional[str] = None) -> Service:
        if driver_location is None:
            return Service()
        else:
            return Service(driver_location)

    def get_options(self) -> Options:
        options = Options()
        options.headless = True
        options.add_argument(f"user-agent={USER_AGENT}")
        options.add_argument("--window-size=1920x1080")
        # options.add_argument('--headless')
        options.add_argument("--headless=new")
        options.add_argument('--no-sandbox')
        options.add_argument("--disable-gpu")
        # options.add_argument("--window-size=1280x1696")
        options.add_argument("--single-process")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-dev-tools")
        options.add_argument("--no-zygote")
        # options.add_argument(f"--user-data-dir={mkdtemp()}")
        # options.add_argument(f"--data-path={mkdtemp()}")
        # options.add_argument(f"--disk-cache-dir={mkdtemp()}")

        return options

    def accept_cookies(self, driver: Chrome) -> None:
        confirmation_labels = ["zustimmen", "akzeptieren", "accept", "agree", "confirm"]

        for text in confirmation_labels:
            try:
                accept_button = driver.find_element(
                    By.XPATH,
                    "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
                    f"'{text}')]"
                )
                accept_button.click()
                break
            except Exception:
                pass

    def take_screenshot(self, driver, bboxes: List[WebBox]):
        image = driver.get_screenshot_as_png()
        image = Image.open(BytesIO(image)).convert("RGB")

        draw = ImageDraw.Draw(image)
        [draw.rectangle([(n.x1, n.y1), (n.x2, n.y2)], outline="red") for n in bboxes]

        image.save("./screenshot.png")
        return image
