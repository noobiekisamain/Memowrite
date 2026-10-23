"""File.Memory - long-term memory for Memowrite programs.

Every program gets a file called File.Memory in its own folder.
Anything you `remember` is written there, and you can `recall` it
the next time the program runs - even after the computer restarts.

The file is plain JSON so you can open and read it in any editor.
"""

import json
import os
import time

HEADER_KEY = "_about"
HEADER_TEXT = "This is File.Memory - things a Memowrite program remembered. You can edit it, or delete it to forget everything."


class MemoryFile:
    TYPE_NAME = "memory"

    def __init__(self, path):
        self.path = path
        self.data = {}
        self._loaded = False

    def _load(self):
        if self._loaded:
            return
        self._loaded = True
        if os.path.exists(self.path):
            try:
                with open(self.path, encoding="utf-8") as fh:
                    text = fh.read()
                start = text.find("{")
                if start >= 0:
                    self.data = json.loads(text[start:])
            except (OSError, ValueError):
                # a broken memory file is kept as a backup, never lost
                try:
                    os.replace(self.path, self.path + ".broken-" + time.strftime("%Y%m%d%H%M%S"))
                except OSError:
                    pass
                self.data = {}
        self.data.pop(HEADER_KEY, None)

    def _save(self):
        payload = {HEADER_KEY: HEADER_TEXT}
        payload.update(self.data)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False, default=str)
        os.replace(tmp, self.path)

    def set(self, key, value):
        self._load()
        try:
            json.dumps(value)
        except (TypeError, ValueError):
            from ..errors import MemoError
            raise MemoError("I can only remember numbers, text, yes/no, lists and books")
        self.data[key] = value
        self._save()

    def get(self, key):
        self._load()
        if key in self.data:
            return self.data[key]
        for k in self.data:
            if k.lower() == key.lower():
                return self.data[k]
        return None

    def has(self, key):
        self._load()
        return key in self.data or any(k.lower() == key.lower() for k in self.data)

    def delete(self, key):
        self._load()
        for k in list(self.data):
            if k.lower() == key.lower():
                del self.data[k]
        self._save()

    def clear(self):
        self._load()
        self.data = {}
        self._save()

    def keys(self):
        self._load()
        return list(self.data.keys())
