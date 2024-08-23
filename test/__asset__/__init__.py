from pathlib import Path


def load_test_file(name: str):
    path = Path(__file__).parent
    with open(path.as_posix() + "/" + name, "r") as file:
        return file


def get_test_path(name: str):
    return Path(__file__).parent.as_posix() + f"/{name}"
