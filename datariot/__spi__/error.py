class DataRiotException(Exception):

    def __init__(self, msg: str):
        self.msg = msg


class DataRiotImportException(DataRiotException):

    def __init__(self, lib: str):
        self.lib = lib

    def __repr__(self):
        return f"please install datariot[{self.lib}]"
