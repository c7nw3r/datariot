import logging
import os
import pathlib

from PIL.Image import Image
from tqdm import tqdm


def get_local_dir(path: str, dir_name: str):
    path = f"{get_dir(path)}/{dir_name}"

    if not os.path.exists(path):
        os.makedirs(path)
    return path


def get_dir(path: str):
    return str(pathlib.Path(path).parent.resolve())


def without_ext(path: str):
    return path[:path.rfind(".")]


def get_files(path: str, ext: str):
    for root, _, files in tqdm(os.walk(path), desc="get files of " + path):
        for file in files:
            if file.endswith(ext):
                yield f"{root}/{file}"


def write_file(path: str, content: str):
    _dir = pathlib.Path(path).parent.resolve()
    if not os.path.exists(_dir):
        os.makedirs(_dir)

    with open(path, "w") as file:
        file.write(content)


def get_filename(path: str):
    name = path[path.rfind("/") + 1:]
    name = name[:name.rfind(".")]
    return name


def save_image(path: str, image: Image, image_quality: int = 10):
    if not os.path.exists(path):
        os.makedirs(path)

    try:
        image.save(path, 'webp', optimize=True, quality=image_quality)
    except OSError:
        try:
            logging.info(f"try to save image as {image.format}")
            image.save(path.replace(".webp", f".{image.format}"), image.format)
        except OSError as ex:
            logging.warning(f"error while saving image of {path}", ex)
