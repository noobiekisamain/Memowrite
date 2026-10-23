"""The memowrite command.

    memowrite                     start the interactive Memowrite shell
    memowrite hello.mw            run a program
    memowrite run hello.mw        run a program
    memowrite check hello.mw      check a program for mistakes without running it
    memowrite new MyGame          make a new project folder
    memowrite words               list every built-in word with a short description
    memowrite studio [file]       open Memowrite Studio (the editor)
    memowrite version             show the version
"""

import io
import os
import sys
import traceback

from . import __version__
from .errors import MemoError, StopProgram
from .interpreter import Interpreter, friendly_python_error

RED = "\x1b[31m"
GREEN = "\x1b[32m"
BLUE = "\x1b[94m"
DIM = "\x1b[90m"
RESET = "\x1b[0m"


def _setup_console():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if os.name == "nt":
        os.system("")


def color(text, code):
    if os.environ.get("NO_COLOR") or (not sys.stderr.isatty() and not os.environ.get("MEMOWRITE_STUDIO")):
        return text
    return f"{code}{text}{RESET}"


def run_file(path, argv=(), pause=False):
    if not os.path.exists(path) and os.path.exists(path + ".mw"):
        path += ".mw"
    if not os.path.exists(path):
        sys.stderr.write(color(f"Oops! I can't find the file {path}\n", RED))
        return 2
    it = Interpreter(path, argv=list(argv))
    code = 0
    try:
        it.run_file(path)
    except MemoError as e:
        if not e.file:
            e.file = os.path.basename(path)
        sys.stderr.write(color(str(e), RED) + "\n")
        code = 1
    except StopProgram:
        pass
    except KeyboardInterrupt:
        sys.stderr.write("\nStopped.\n")
        code = 130
    except RecursionError:
        sys.stderr.write(color(f"Oops! line {it.line}: a task kept calling itself forever\n", RED))
        code = 1
    except Exception as e:
        sys.stderr.write(color(f"Oops! line {it.line}: {friendly_python_error(e)}\n", RED))
        if os.environ.get("MEMOWRITE_DEBUG"):
            traceback.print_exc()
        code = 1
    finally:
        sys.stdout.flush()
    if pause:
        try:
            input(color("\nPress Enter to close...", DIM))
        except EOFError:
            pass
    return code


def check_file(path):
    from .parser import Parser
    try:
        with open(path, encoding="utf-8-sig") as fh:
            Parser(fh.read(), os.path.basename(path)).parse_program()
    except MemoError as e:
        if not e.file:
            e.file = os.path.basename(path)
        print(color(str(e), RED))
        return 1
    print(color(f"Looks good! No mistakes found in {os.path.basename(path)}.", GREEN))
    return 0


BLOCK_STARTERS = ("if", "repeat", "while", "until", "forever", "for", "count", "make task", "to ", "task", "function",
                  "try", "check", "make model", "make kind", "every", "after", "when", "unless", "define", "loop")


def repl():
    print(color(f"Memowrite {__version__} shell", BLUE) + " - type Memowrite lines and press Enter.")
    print(color("Try: say \"hello\"   |   type 'help' for tips, 'quit' to leave.", DIM))
    it = Interpreter(os.path.join(os.getcwd(), "shell.mw"))
    from .parser import Parser
    buf = []
    while True:
        try:
            line = input(color("... " if buf else "mw> ", BLUE))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        stripped = line.strip().lower()
        if not buf and stripped in ("quit", "exit", "bye"):
            break
        if not buf and stripped == "help":
            print(HELP_TEXT)
            continue
        buf.append(line)
        source = "\n".join(buf)
        try:
            tree = Parser(source, "shell").parse_program()
        except MemoError as e:
            if "never closed" in e.message:
                continue
            print(color(str(e), RED))
            buf = []
            continue
        buf = []
        try:
            # show the value of a lone expression like: 2 + 2
            if len(tree) == 1 and tree[0].kind in ("exprstmt", "do") and not source.strip().lower().startswith(("do ", "call ", "run ")):
                node = tree[0]
                if node.kind == "do" and not node.args:
                    value = it.eval(node.task)
                    from .values import Task, Builtin, to_text
                    if isinstance(value, (Task, Builtin)):
                        result = it.call(value, [])
                        if result is not None:
                            print(color("= " + to_text(result, True), GREEN))
                    else:
                        print(color("= " + to_text(value, True), GREEN))
                    continue
            it.exec_block(tree)
            if it.gui is not None:
                it.gui.pump()
        except StopProgram:
            break
        except MemoError as e:
            print(color(str(e), RED))
        except Exception as e:
            print(color("Oops! " + friendly_python_error(e), RED))


HELP_TEXT = """
  say "hello"                      show something
  set score to 10                  remember a value in a name
  ask "Your name?" into name       ask a question
  if score is more than 5 then say "big"
  repeat 3 times ... end           do something again and again
  make task greet with who ... end make your own command
  draw circle at 100, 100 size 40 color "red"
  remember "best" as 99            save forever in File.Memory
  words                            (in the terminal: memowrite words) list every built-in word
"""


def list_words():
    it = Interpreter()
    seen = set()
    rows = []
    for name, b in sorted(it.builtins.items()):
        if id(b) in seen:
            continue
        seen.add(id(b))
        aliases = sorted(n for n, x in it.builtins.items() if x is b and n != b.name)
        rows.append((b.name, b.doc, aliases))
    for name, doc, aliases in sorted(rows):
        extra = f"  (also: {', '.join(aliases)})" if aliases else ""
        print(f"{name:<20} {doc}{color(extra, DIM)}")
    print(f"\n{len(rows)} built-in words. Use them like: length of \"hello\"  or  length(\"hello\")")


NEW_PROJECT = '''# {name} - made with Memowrite
# Run it with F5 in Memowrite Studio, or type: memowrite main.mw

say "Hello from {name}!"

recall "times run" into runs or 0
add 1 to runs
remember "times run" as runs
say "This program has run {{runs}} time(s). (Saved in File.Memory)"
'''


def new_project(name):
    folder = os.path.abspath(name)
    os.makedirs(folder, exist_ok=True)
    main = os.path.join(folder, "main.mw")
    if not os.path.exists(main):
        with open(main, "w", encoding="utf-8") as fh:
            fh.write(NEW_PROJECT.format(name=os.path.basename(folder)))
    print(color(f"Made a new Memowrite project in {folder}", GREEN))
    print(f"Open {main} in Memowrite Studio or Visual Studio Code, then run it.")
    return 0


def open_studio(args):
    from .studio import main as studio_main
    studio_main(args)
    return 0


def main(argv=None):
    _setup_console()
    argv = list(sys.argv[1:] if argv is None else argv)
    pause = False
    if "--pause" in argv:
        argv.remove("--pause")
        pause = True
    if not argv:
        repl()
        return 0
    cmd = argv[0].lower()
    if cmd in ("-v", "--version", "version"):
        print(f"Memowrite {__version__}")
        return 0
    if cmd in ("-h", "--help", "help", "/?"):
        print(__doc__)
        return 0
    if cmd == "run" and len(argv) > 1:
        return run_file(argv[1], argv[2:], pause)
    if cmd == "check" and len(argv) > 1:
        return check_file(argv[1])
    if cmd == "new" and len(argv) > 1:
        return new_project(argv[1])
    if cmd in ("words", "builtins", "library"):
        list_words()
        return 0
    if cmd in ("studio", "edit", "editor"):
        return open_studio(argv[1:])
    if cmd in ("shell", "repl"):
        repl()
        return 0
    return run_file(argv[0], argv[1:], pause)


if __name__ == "__main__":
    sys.exit(main())
