import base64
from io import BytesIO
from typing import Union

from PIL import Image


def map_image_type(image_type: str):
    if image_type == "jpg":
        return "jpeg"
    return image_type


def get_type_from_base64(encoded_image: Union[str, bytes]):
    if type(encoded_image) is str and encoded_image.startswith("data:"):
        return map_image_type(encoded_image[encoded_image.find("/") + 1:encoded_image.find(";")])
    return "jpeg"


def from_base64(encoded_image: Union[str, bytes]):
    if type(encoded_image) is str and encoded_image.startswith("data:"):
        _format = get_type_from_base64(encoded_image)
        encoded_image = encoded_image[encoded_image.find(",") + 1:]
        image = Image.open(BytesIO(base64.b64decode(encoded_image)))
        image.format = _format

        if image.mode != "RGB":
            image = image.convert("RGB")

        return image
    return Image.open(BytesIO(base64.b64decode(encoded_image)))
