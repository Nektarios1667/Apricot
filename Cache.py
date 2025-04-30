import os
import pickle
import time

import Console


class Snapshot:
    VERSION = '2.0'

    def __init__(self):
        self.consts = None
        self.code = None
        self.compiled = None
        self.timestamp = None
        self.warnings = None
        self.console = None
        self.version = Snapshot.VERSION

    def save(self, code: str, compiled: str, consts: dict, warnings: list, console: Console.Console):
        self.consts = consts
        self.code = code
        self.compiled = compiled
        self.warnings = warnings
        self.timestamp = time.time()
        self.console = console


class CacheLoader:
    @staticmethod
    def load() -> list[Snapshot]:
        try:
            with open('.cache\\_cache_.pkl', 'rb') as file:
                cached = pickle.load(file)
                cached = [snapshot for snapshot in cached if snapshot.version == Snapshot.VERSION]

        except FileNotFoundError:
            cached = []

        return cached

    @staticmethod
    def find(code: str):
        snapshots = CacheLoader.load()
        for snapshot in snapshots:
            if snapshot == code and snapshot.version == Snapshot.VERSION:
                return snapshot

    @staticmethod
    def store(snapshot):
        snapshots = CacheLoader.load()

        if not os.path.exists('.cache'):
            os.mkdir('.cache')

        with open('.cache/_cache_.pkl', 'wb') as file:
            if not snapshots or snapshot != snapshots[-1]:
                snapshots = [*snapshots, snapshot][-5:]
            pickle.dump(snapshots, file)

    @staticmethod
    def clear():
        if os.path.exists('.cache/_cache_.pkl'):
            os.remove('.cache/_cache_.pkl')
