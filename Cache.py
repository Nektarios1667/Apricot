import time

class Cache:
    def __init__(self):
        self.code = None
        self.apricode = None
        self.timestamp = None

    def store(self, code: str, apricode: str, enviroment: dict):
        self.code = code
        self.apricode = apricode
        self.timestamp = time.time()

    def compare(self, other):    
        # True checks
        if self.code == other:
            return True

        return False

    def grab(self):
        return self.apricode

    def __eq__(self, other):
        return self.code == other.code
