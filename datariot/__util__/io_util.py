import logging
import os
import pathlib

from tqdm import tqdm

from datariot.__util__.text_util import create_uuid_from_string


def get_local_dir(path: str, dir_name: str):
    path = f"{get_dir(path)}/{dir_name}"

    if not os.path.exists(path):
        os.makedirs(path)
    return path


def without_ext(path: str) -> str:
    return path[:path.rfind(".")]


def get_dir(path: str):
    return str(pathlib.Path(path).parent.resolve())


def get_files(path: str, ext: str, recursive: bool = True):
    if not recursive:
        for file in tqdm(os.listdir(path), desc="get files of " + path):
            if file.endswith(ext):
                yield f"{path}/{file}"

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


def save_image(path: str, box, image_quality: int = 10):
    if not os.path.exists(path):
        os.makedirs(path)

    _, file = box.get_file()
    try:
        name = create_uuid_from_string(box.to_hash(fast=True))
    except OSError as ex:
        logging.warning(str(ex))
        return

    try:
        file.save(f"{path}/{name}.webp", 'webp', optimize=True, quality=image_quality)
    except OSError:
        try:
            logging.info(f"try to save image as {file.format}")
            file.save(f"{path}/{name}.{file.format}", file.format)
        except OSError as ex:
            logging.warning(f"error while saving image of {path}", str(ex))
            return
