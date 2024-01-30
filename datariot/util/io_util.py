import os
import pathlib

from tqdm import tqdm


def get_local_dir(dir_name: str):
    root = pathlib.Path(__file__).parent.parent.parent.resolve()
    path = f"{root}/{dir_name}"

    if not os.path.exists(path):
        os.makedirs(path)
    return path


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
