"""Minimal stub of loguru for offline testing."""
from pathlib import Path


class _Logger:
    def __init__(self):
        self._file = None

    def info(self, msg):
        print(msg)
        if self._file:
            self._file.write(msg + "\n")
            self._file.flush()

    def warning(self, msg):
        self.info(msg)

    def error(self, msg):
        self.info(msg)

    def add(self, sink, *args, **kwargs):
        if isinstance(sink, (str, Path)):
            self._file = open(sink, "a")
        return 0

    def remove(self, *args, **kwargs):
        if self._file:
            self._file.close()
            self._file = None


logger = _Logger()
