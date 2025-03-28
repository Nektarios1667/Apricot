import re
import time
import pickle


class Snapshot:
    def __init__(self):
        self.consts = None
        self.code = None
        self.apricode = None
        self.timestamp = None

    def save(self, code: str, apricode: str, consts: dict):
        self.consts = consts
        self.code = code
        self.apricode = apricode
        self.timestamp = time.time()

    def __eq__(self, other):
        if isinstance(other, Snapshot):
            return self.code == other.code
        else:
            return self.code == other


class CacheLoader:
    @staticmethod
    def load() -> dict:
        try:
            with open('.cache/_cache_.pkl', 'rb') as file:
                cached = pickle.load(file)
        except Exception:
            with open('.cache/_cache_.pkl', 'wb') as file:
                cached = []
                pickle.dump(cached, file)

        return cached

    @staticmethod
    def find(code: str):
        snapshots = CacheLoader.load()
        for snapshot in snapshots:
            if snapshot == code:
                return snapshot

    @staticmethod
    def store(snapshot):
        snapshots = CacheLoader.load()
        with open('.cache/_cache_.pkl', 'wb') as file:
            if not snapshots or snapshot != snapshots[-1]:
                snapshots = [*snapshots, snapshot][-5:]
            pickle.dump(snapshots, file)
