import re
import time
import functools


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

def outputs(apricode: str, persistents):
    # Compile regex patterns once
    stringPattern = re.compile(r'''(["']).*?\1''')
    commentPattern = re.compile(r'//.*')

    # Replace strings and comments
    altered = stringPattern.sub('"There once was a string..."', apricode)
    altered = commentPattern.sub('// There once was a comment...', altered)

    # Check for any persistent pattern match
    answer = bool(persistents.search(altered))
    return answer
