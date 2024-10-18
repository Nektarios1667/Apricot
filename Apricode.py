import time


class Apricode:
    def __init__(self, name: str, version: float = 0.1, code: str = '', compiled: str = ''):
        self.code = code
        self.compiled = compiled
        self.timestamp = time.time()
        self.version = version
        self.name = name

    def execute(self):
        exec(self.compiled)

    def __str__(self):
        return self.compiled if self.compiled else self.code

    def __repr__(self):
        return f'<Apricode: {self.name} - Version: {self.version}>'
