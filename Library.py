import os


class Library:
    def __init__(self, path: str):
        self._name = os.path.basename(path)
        self._path = path

    def __str__(self):
        return f'<Library {self._name}>'

