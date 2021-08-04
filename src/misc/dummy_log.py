import sys

from datetime import datetime as dt


class DummyLogWriter:
    def __init__(self, name=""):
        self.name = name if name else "DummyLogger"

    def debug(self, msg):
        print(f"{dt.now()} {self.name} DEBUG: {msg}")

    def info(self, msg):
        print(f"{dt.now()} {self.name} INFO: {msg}")

    def warning(self, msg):
        print(f"{dt.now()} {self.name} WARNING: {msg}", file=sys.stderr)

    def error(self, msg):
        print(f"{dt.now()} {self.name} ERROR: {msg}", file=sys.stderr)

    def critical(self, msg):
        print(f"{dt.now()} {self.name} CRITICAL: {msg}", file=sys.stderr)
