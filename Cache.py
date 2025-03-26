import re
import time
import pickle


class Snapshot:
    def __init__(self):
        self.code = None
        self.apricode = None
        self.timestamp = None

    def save(self, code: str, apricode: str, enviroment: dict):
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

class CacheLoader:
    OUTPUTS = r"""
        \b(open|read|write|close|seek|truncate)\b|
        \b(os\.(remove|rename|replace|rmdir|mkdir|makedirs|removedirs))\b|
        \b(shutil\.(copy|copy2|copytree|move|rmtree))\b|
        \b(socket\.(socket|bind|connect|send|recv|listen|accept|close))\b|
        \b(log|input)\b|
        \b(sys\.(stdout|stderr|stdin))\b|
        \b(os\.(system|kill|popen))\b|
        \b(subprocess\.(run|Popen|call|check_output|check_call))\b|
        \b(os\.environ(\[.*?]|\.get|\.setdefault|\.pop))\b|
        \b(threading\.(Thread|Lock|Event|Semaphore|Timer|Barrier))\b|
        \b(multiprocessing\.(Process|Queue|Pipe|Pool|Manager))\b|
        \b(asyncio\.(run|create_task|sleep|gather|wait|ensure_future))\b
    """

    @staticmethod
    def load():
        try:
            with open('.cache/_cache_.pkl', 'rb') as file:
                cached = pickle.load(file)
                snapshots = cached['snapshots']
                regexes = cached['regexes']
        except Exception:
            with open('.cache/_cache_.pkl', 'wb') as file:
                cached = {'snapshots': [], 'regexes': {'persistents': re.compile(CacheLoader.OUTPUTS, re.VERBOSE)}}
                pickle.dump(cached, file)
                snapshots = []
                regexes = cached['regexes']

        return cached, snapshots, regexes

    @staticmethod
    def store(cached, snapshot):
        snapshots = cached['snapshots']

        with open('.cache/_cache_.pkl', 'wb') as file:
            if not snapshots or snapshot != snapshots[-1]:
                cached['snapshots'] = [*snapshots, snapshot][-5:]
            pickle.dump(cached, file)
