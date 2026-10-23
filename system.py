"""Talking to the computer: opening files and websites, the clipboard, the console."""

import getpass
import os
import platform
import subprocess
import sys
import webbrowser

from ..errors import MemoError
from ..values import to_text

ANSI = {
    "black": 30, "red": 31, "green": 32, "yellow": 33, "blue": 34, "purple": 35, "magenta": 35, "pink": 95,
    "cyan": 36, "white": 37, "gray": 90, "grey": 90, "orange": 33, "brightred": 91, "brightgreen": 92,
    "brightyellow": 93, "brightblue": 94, "brightcyan": 96, "normal": 0, "default": 0, "reset": 0,
}

_ansi_ready = False


def _enable_ansi():
    global _ansi_ready
    if not _ansi_ready and os.name == "nt":
        os.system("")  # turns on colour support in the Windows console
    _ansi_ready = True


def console_color(it, name):
    _enable_ansi()
    code = ANSI.get(name.lower().replace(" ", ""))
    if code is None:
        raise MemoError(f"I know these text colors: {', '.join(sorted(ANSI))}")
    it.write(f"\x1b[{code}m")


def clear_screen(it):
    if os.environ.get("MEMOWRITE_STUDIO"):
        it.write("\x1b[2J")
        return
    if it.out is not sys.stdout:
        it.write("\n" * 3)
        return
    os.system("cls" if os.name == "nt" else "clear")


def open_thing(it, what):
    if what.startswith(("http://", "https://", "www.")):
        webbrowser.open(what if not what.startswith("www.") else "https://" + what)
        return
    path = it.path(what)
    if not os.path.exists(path):
        raise MemoError(f"I can't find '{what}' to open it")
    if os.name == "nt":
        try:
            os.startfile(path)  # noqa
        except OSError:
            raise MemoError(f"Windows has no app set up to open '{os.path.basename(path)}'")
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def set_clipboard(it, text):
    gui = it.ensure_gui()
    gui.root_or_hidden().clipboard_clear()
    gui.root_or_hidden().clipboard_append(text)
    gui.root_or_hidden().update()


def get_clipboard(it):
    gui = it.ensure_gui()
    try:
        return gui.root_or_hidden().clipboard_get()
    except Exception:
        return ""


def extra_builtins(it):
    def username():
        try:
            return getpass.getuser()
        except Exception:
            return "friend"

    def computer_name():
        return platform.node()

    def operating_system():
        return f"{platform.system()} {platform.release()}"

    def screen_width():
        return it.ensure_gui().root_or_hidden().winfo_screenwidth()

    def screen_height():
        return it.ensure_gui().root_or_hidden().winfo_screenheight()

    def environment(name):
        return os.environ.get(to_text(name), "")

    def clipboard():
        return get_clipboard(it)

    def python_version():
        return platform.python_version()

    def cpu_count():
        return os.cpu_count() or 1

    def language():
        import locale
        return (locale.getlocale()[0] or "unknown")

    return {
        "username": (username, 0, 0, "Your user name on this computer"),
        "computer_name": (computer_name, 0, 0, "The name of this computer"),
        "operating_system": (operating_system, 0, 0, "Windows 11, etc."),
        "screen_width": (screen_width, 0, 0, "Width of the screen in pixels"),
        "screen_height": (screen_height, 0, 0, "Height of the screen in pixels"),
        "environment": (environment, 1, 1, "Reads an environment setting"),
        "clipboard": (clipboard, 0, 0, "The text on the clipboard"),
        "engine_version": (python_version, 0, 0, "The version of the engine Memowrite runs on"),
        "cpu_count": (cpu_count, 0, 0, "How many processor cores the computer has"),
        "language": (language, 0, 0, "The computer's language setting"),
    }
