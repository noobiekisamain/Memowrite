"""Files and folders, saving and loading, and the internet."""

import json
import os
import shutil

from ..errors import MemoError
from ..values import to_text, Builtin, tidy_number, looks_like_number, to_number


def write_file(it, path, value, mode):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if isinstance(value, list) and all(not isinstance(x, (list, dict)) for x in value):
        text = "\n".join(to_text(x) for x in value)
    elif isinstance(value, (list, dict)):
        text = json.dumps(value, indent=2, ensure_ascii=False, default=to_text)
    else:
        text = to_text(value)
    if mode == "a" and os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "rb") as fh:
            fh.seek(-1, os.SEEK_END)
            if fh.read(1) not in (b"\n", b"\r"):
                text = "\n" + text
    with open(path, mode, encoding="utf-8", newline="") as fh:
        fh.write(text)


def read_file(it, path):
    if not os.path.exists(path):
        raise MemoError(f"I can't find the file '{os.path.basename(path)}'", hint=f"I looked in {os.path.dirname(path)}")
    with open(path, encoding="utf-8-sig", errors="replace") as fh:
        return fh.read()


def save_value(it, value, path):
    if hasattr(value, "export"):
        value.export(path)
        return
    if hasattr(value, "save"):
        value.save(path)
        return
    ext = os.path.splitext(path)[1].lower()
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if ext == ".csv" and isinstance(value, list):
        from .builtins import _tocsv
        text = _tocsv(it, value)
    elif ext in (".json", ".mwdata") or isinstance(value, (list, dict, bool, int, float)) or value is None:
        text = json.dumps(value, indent=2, ensure_ascii=False, default=to_text)
    else:
        text = to_text(value)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def load_value(it, path):
    text = read_file(it, path)
    ext = os.path.splitext(path)[1].lower()
    if ext == ".csv":
        from .builtins import _fromcsv
        return _fromcsv(it, text)
    if ext == ".mwmodel":
        from .graphics import Model
        return Model.load(path, os.path.splitext(os.path.basename(path))[0])
    stripped = text.strip()
    if stripped[:1] in ("[", "{") or stripped in ("true", "false", "null") or looks_like_number(stripped):
        try:
            return json.loads(stripped)
        except ValueError:
            pass
    return text


def delete(it, path, folder=False):
    if not os.path.exists(path):
        return
    if os.path.isdir(path):
        if not folder:
            raise MemoError("That is a folder. Use: delete folder \"name\"")
        shutil.rmtree(path)
    else:
        os.remove(path)


def copy(it, src, dst, move):
    if not os.path.exists(src):
        raise MemoError(f"I can't find '{os.path.basename(src)}'")
    folder = os.path.dirname(dst)
    if folder:
        os.makedirs(folder, exist_ok=True)
    if move:
        shutil.move(src, dst)
    elif os.path.isdir(src):
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        shutil.copy2(src, dst)


def _urlopen(url, timeout=20):
    import urllib.request
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    req = urllib.request.Request(url, headers={"User-Agent": "Memowrite/1.0"})
    return urllib.request.urlopen(req, timeout=timeout)


def fetch_text(it, url):
    try:
        with _urlopen(url) as r:
            data = r.read()
            charset = r.headers.get_content_charset() or "utf-8"
            return data.decode(charset, errors="replace")
    except Exception as e:
        raise MemoError(f"I couldn't get {url}: {e}")


def download(it, url, path):
    try:
        with _urlopen(url, 60) as r, open(path, "wb") as fh:
            shutil.copyfileobj(r, fh)
    except Exception as e:
        raise MemoError(f"I couldn't download {url}: {e}")


def extra_builtins(it):
    def file_exists(p):
        return os.path.isfile(it.path(p))

    def folder_exists(p):
        return os.path.isdir(it.path(p))

    def files_in(p="."):
        folder = it.path(p)
        if not os.path.isdir(folder):
            raise MemoError(f"There is no folder called {to_text(p)}")
        return sorted(f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)))

    def folders_in(p="."):
        folder = it.path(p)
        return sorted(f for f in os.listdir(folder) if os.path.isdir(os.path.join(folder, f)))

    def read(p):
        return read_file(it, it.path(p))

    def file_size(p):
        return os.path.getsize(it.path(p))

    def file_extension(p):
        return os.path.splitext(to_text(p))[1].lstrip(".")

    def file_name(p):
        return os.path.basename(to_text(p))

    def full_path(p):
        return it.path(p)

    def home_folder():
        return os.path.expanduser("~")

    def desktop_folder():
        return os.path.join(os.path.expanduser("~"), "Desktop")

    def documents_folder():
        return os.path.join(os.path.expanduser("~"), "Documents")

    def downloads_folder():
        return os.path.join(os.path.expanduser("~"), "Downloads")

    def fetch(url):
        return fetch_text(it, to_text(url))

    def fetch_json(url):
        return json.loads(fetch_text(it, to_text(url)))

    def file_modified(p):
        import datetime
        return datetime.datetime.fromtimestamp(os.path.getmtime(it.path(p))).strftime("%Y-%m-%d %H:%M:%S")

    def count_lines(p):
        return len(read_file(it, it.path(p)).splitlines())

    def search_files(pattern, p="."):
        import fnmatch
        out = []
        for root, _dirs, names in os.walk(it.path(p)):
            for n in names:
                if fnmatch.fnmatch(n.lower(), to_text(pattern).lower()):
                    out.append(os.path.relpath(os.path.join(root, n), it.path(p)))
        return sorted(out)

    return {
        "file_exists": (file_exists, 1, 1, "Is there a file with this name?"),
        "folder_exists": (folder_exists, 1, 1, "Is there a folder with this name?"),
        "files_in": (files_in, 0, 1, "List of files in a folder"),
        "folders_in": (folders_in, 0, 1, "List of folders in a folder"),
        "read_file": (read, 1, 1, "The text inside a file"),
        "file_size": (file_size, 1, 1, "Size of a file in bytes"),
        "file_extension": (file_extension, 1, 1, "The end of a file name, like txt"),
        "file_name": (file_name, 1, 1, "Just the name part of a path"),
        "full_path": (full_path, 1, 1, "The full path of a file"),
        "home_folder": (home_folder, 0, 0, "Your home folder"),
        "desktop_folder": (desktop_folder, 0, 0, "Your Desktop folder"),
        "documents_folder": (documents_folder, 0, 0, "Your Documents folder"),
        "downloads_folder": (downloads_folder, 0, 0, "Your Downloads folder"),
        "fetch": (fetch, 1, 1, "Gets the text of a web page"),
        "fetch_json": (fetch_json, 1, 1, "Gets JSON data from the internet"),
        "file_modified": (file_modified, 1, 1, "When a file was last changed"),
        "count_lines": (count_lines, 1, 1, "How many lines a file has"),
        "search_files": (search_files, 1, 2, "Finds files matching a pattern like *.txt"),
    }
