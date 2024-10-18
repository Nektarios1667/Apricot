import sys
import time
from Functions import *
from io import StringIO

def returnCheck(value, instance, line, l):
    if instance is not None and isinstance(value, instance):
        return value
    else:
        error('TypeError', line.strip(), value, l, f'Return type defined as -{"null" if instance is None else instance.__name__}- but value is -{type(value).__name__}-')

class Apricode:
    def __init__(self, name: str, version: float = 0.1, code: str = '', compiled: str = ''):
        self.code = code
        self.compiled = compiled
        self.timestamp = time.time()
        self.version = version
        self.name = name

    def execute(self):
        # Special functions
        def log(*args):
            print('null' if args[0] is None else args[0], *args[1:])

        # Exec
        exec(self.compiled)

    def __str__(self):
        return self.compiled if self.compiled else self.code

    def __repr__(self):
        return f'<Apricode: {self.name} - Version: {self.version}>'
