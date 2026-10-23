"""The Memowrite interpreter: runs the tree the parser built."""

import math
import os
import random
import sys
import threading
import time

from .errors import MemoError, Complaint, StopLoop, SkipLoop, GiveBack, StopProgram, suggest
from .parser import Parser, E
from .values import (Task, Builtin, Kind, Instance, to_text, type_name, truthy, is_number, to_number,
                     tidy_number, same, looks_like_number)

MAX_DEPTH = 400

UNIT_SECONDS = {
    "seconds": 1, "second": 1, "secs": 1, "sec": 1, "s": 1,
    "milliseconds": 0.001, "millisecond": 0.001, "ms": 0.001,
    "minutes": 60, "minute": 60, "mins": 60, "min": 60,
    "hours": 3600, "hour": 3600,
    "frames": 1 / 60, "frame": 1 / 60,
}


class Interpreter:
    def __init__(self, script_path=None, out=None, inp=None, argv=None):
        self.script_path = os.path.abspath(script_path) if script_path else None
        self.base_dir = os.path.dirname(self.script_path) if self.script_path else os.getcwd()
        self.out = out or sys.stdout
        self.inp = inp
        self.globals = {}
        self.frames = []
        self.line = 0
        self.file = os.path.basename(script_path) if script_path else None
        self.used_files = set()
        self.start_time = time.time()
        self.argv = argv or []
        self._last_pump = 0.0
        self.random = random.Random()
        # subsystems are loaded lazily so console programs start fast
        self.gui = None
        self._memory = None
        from .stdlib import builtins as bl
        self.builtins = bl.make_builtins(self)
        self.globals["arguments"] = list(self.argv)

    # ------------------------------------------------------------ helpers
    def error(self, message, hint=None):
        return MemoError(message, self.line, self.file, hint)

    def path(self, p):
        p = to_text(p)
        p = os.path.expanduser(os.path.expandvars(p))
        if not os.path.isabs(p):
            p = os.path.join(self.base_dir, p)
        return p

    @property
    def memory(self):
        if self._memory is None:
            from .stdlib.memory import MemoryFile
            self._memory = MemoryFile(os.path.join(self.base_dir, "File.Memory"))
        return self._memory

    def ensure_gui(self):
        if self.gui is None:
            from .stdlib.gui import GUI
            self.gui = GUI(self)
        return self.gui

    def pump(self, force=False):
        """Keep windows alive while long loops run."""
        if self.gui is None:
            return
        now = time.time()
        if force or now - self._last_pump > 0.02:
            self._last_pump = now
            self.gui.pump()

    def write(self, text):
        self.out.write(text)
        try:
            self.out.flush()
        except Exception:
            pass

    # ------------------------------------------------------------ running
    def run_source(self, source, filename=None):
        tree = Parser(source, filename or self.file or "program").parse_program()
        try:
            self.hoist(tree)
            self.exec_block(tree)
        except StopProgram:
            pass
        except (StopLoop, SkipLoop):
            raise self.error("'stop' or 'skip' was used outside of a loop")
        except GiveBack:
            pass
        if self.gui is not None:
            try:
                self.gui.mainloop()
            except StopProgram:
                pass

    def run_file(self, path):
        with open(path, "r", encoding="utf-8-sig") as fh:
            source = fh.read()
        self.run_source(source, os.path.basename(path))

    def hoist(self, tree):
        """Tasks and kinds can be used before the line that makes them."""
        for node in tree:
            if node.kind in ("task", "kind"):
                self.line = node.line
                getattr(self, "x_" + node.kind)(node)

    # ------------------------------------------------------------ variables
    def lookup(self, name):
        if self.frames:
            frame = self.frames[-1]
            if name in frame:
                return frame[name]
            closure = frame.get("\x00closure")
            while closure is not None:
                if name in closure:
                    return closure[name]
                closure = closure.get("\x00closure")
        if name in self.globals:
            return self.globals[name]
        if name in self.builtins:
            return self.builtins[name]
        if self.gui is not None:
            found = self.gui.find_named(name)
            if found is not None:
                return found
        options = list(self.globals) + list(self.builtins) + (list(self.frames[-1]) if self.frames else [])
        guess = suggest(name, [o for o in options if not o.startswith("\x00")])
        hint = f"Did you mean '{guess}'?" if guess else f"Set it first, for example: set {name} to 0"
        raise self.error(f"I don't know what '{name}' is yet", hint)

    def assign(self, name, value):
        if self.frames:
            frame = self.frames[-1]
            if name in frame:
                frame[name] = value
                return
            closure = frame.get("\x00closure")
            while closure is not None:
                if name in closure:
                    closure[name] = value
                    return
                closure = closure.get("\x00closure")
            if name in self.globals:
                self.globals[name] = value
                return
            frame[name] = value
            return
        self.globals[name] = value

    def assign_target(self, target, value):
        kind = target[0]
        if kind == "var":
            self.assign(target[1], value)
        elif kind == "index":
            obj = self.eval(target[1])
            idx = self.eval(target[2])
            self.set_index(obj, idx, value)
        elif kind == "prop":
            obj = self.eval(target[2])
            self.set_prop(obj, target[1], value)
        else:
            raise self.error("I can't put a value there")

    # ------------------------------------------------------------ statements
    def exec_block(self, stmts):
        for node in stmts:
            self.line = node.line
            method = getattr(self, "x_" + node.kind)
            method(node)

    def x_pass(self, n):
        pass

    def x_say(self, n):
        text = " ".join(to_text(self.eval(v)) for v in n.values)
        self.write(text + n.end)

    def x_whisper(self, n):
        sys.stderr.write("[debug line %d] %s\n" % (n.line, " ".join(to_text(self.eval(v), True) for v in n.values)))

    def x_ask(self, n):
        prompt = to_text(self.eval(n.prompt))
        if n.popup or (self.gui is not None and self.gui.has_windows()):
            answer = self.ensure_gui().ask_popup(prompt)
        else:
            if prompt and not prompt.endswith((" ", "\n")):
                prompt += " "
            self.write(prompt)
            if self.inp is not None:
                answer = self.inp.readline()
                if answer == "":
                    raise StopProgram()
                answer = answer.rstrip("\r\n")
            else:
                try:
                    answer = input()
                except EOFError:
                    raise StopProgram()
        if answer is None:
            answer = ""
        conv = n.convert
        if conv in ("text", "words", "string"):
            value = answer
        elif conv in ("number", "integer"):
            if not looks_like_number(answer):
                raise self.error(f"'{answer}' is not a number")
            value = to_number(answer)
        elif looks_like_number(answer) and not (len(answer.strip()) > 1 and answer.strip()[0] == "0" and answer.strip()[1] != "."):
            value = to_number(answer)
        else:
            value = answer
        self.assign_target(n.target, value)

    def x_set(self, n):
        self.assign_target(n.target, self.eval(n.value))

    def x_change(self, n):
        cur = self.eval(n.target)
        amount = self.eval(n.value)
        if n.op == "+" and isinstance(cur, list):
            cur.append(amount)
            return
        if n.op == "+" and isinstance(cur, str) and not looks_like_number(cur):
            self.assign_target(n.target, cur + to_text(amount))
            return
        if cur is None and n.op in ("+", "-"):
            cur = 0
        self.assign_target(n.target, self.binop(n.op, cur, amount))

    def x_addto(self, n):
        value = self.eval(n.value)
        try:
            cur = self.eval(n.target)
        except MemoError:
            if n.target[0] == "var":
                self.assign(n.target[1], value)
                return
            raise
        if isinstance(cur, list):
            cur.append(value)
        elif cur is None:
            self.assign_target(n.target, value)
        elif hasattr(cur, "add_item"):
            cur.add_item(value)
        elif isinstance(cur, dict):
            if isinstance(value, dict):
                cur.update(value)
            else:
                raise self.error("To add to a book, write: set book[\"key\"] to value")
        elif isinstance(cur, str) and not (is_number(value) and looks_like_number(cur)):
            self.assign_target(n.target, cur + to_text(value))
        else:
            self.assign_target(n.target, self.binop("+", cur, value))

    def x_insert(self, n):
        lst = self.eval(n.target)
        if not isinstance(lst, list):
            raise self.error("I can only put things at a position in a list")
        pos = int(to_number(self.eval(n.pos)))
        lst.insert(pos - 1 if pos > 0 else len(lst) + pos + 1, self.eval(n.value))

    def x_remove(self, n):
        container = self.eval(n.target)
        value = self.eval(n.value)
        if isinstance(container, list):
            for i, item in enumerate(container):
                if same(item, value):
                    del container[i]
                    return
            raise self.error(f"{to_text(value, True)} is not in the list")
        if isinstance(container, dict):
            for k in list(container):
                if same(k, value):
                    del container[k]
                    return
            raise self.error(f"The book has no key {to_text(value, True)}")
        if isinstance(container, str):
            self.assign_target(n.target, container.replace(to_text(value), "", 1))
            return
        if hasattr(container, "remove_item"):
            container.remove_item(value)
            return
        raise self.error("I can only remove things from lists, books and text")

    def x_removeat(self, n):
        container = self.eval(n.target)
        idx = self.eval(n.index)
        if isinstance(container, list):
            del container[self.list_index(container, idx)]
        elif isinstance(container, dict):
            container.pop(idx, None)
        else:
            raise self.error("I can only remove items from a list")

    def x_clearlist(self, n):
        c = self.eval(n.target)
        if isinstance(c, (list, dict)):
            c.clear()
        elif hasattr(c, "clear"):
            c.clear()
        else:
            self.assign_target(n.target, "")

    def x_swap(self, n):
        a = self.eval(n.a)
        b = self.eval(n.b)
        self.assign_target(n.a, b)
        self.assign_target(n.b, a)

    def x_sort(self, n):
        lst = self.eval(n.target)
        if not isinstance(lst, list):
            raise self.error("I can only sort a list")
        if n.key is not None:
            key_name = self.eval(n.key)
            if isinstance(key_name, (Task, Builtin)):
                keyf = lambda item: sort_key(self.call(key_name, [item]))
            else:
                keyf = lambda item: sort_key(self.get_prop(item, to_text(key_name)))
        else:
            keyf = sort_key
        lst.sort(key=keyf, reverse=n.reverse)

    def x_listop(self, n):
        lst = self.eval(n.target)
        if isinstance(lst, str) and n.op == "reverse":
            self.assign_target(n.target, lst[::-1])
            return
        if not isinstance(lst, list):
            raise self.error(f"I can only {n.op} a list")
        if n.op == "shuffle":
            self.random.shuffle(lst)
        else:
            lst.reverse()

    # -- decisions
    def x_if(self, n):
        for cond, body in n.branches:
            if truthy(self.eval(cond)):
                self.exec_block(body)
                return
        if n.otherwise is not None:
            self.exec_block(n.otherwise)

    def x_check(self, n):
        subject = self.eval(n.subject)
        for values, body in n.cases:
            for v in values:
                if same(subject, self.eval(v)):
                    self.exec_block(body)
                    return
        if n.default is not None:
            self.exec_block(n.default)

    # -- loops
    def _loop_body(self, body):
        try:
            self.exec_block(body)
        except SkipLoop:
            pass
        self.pump()

    def x_repeat(self, n):
        try:
            if n.mode == "times":
                count = to_number(self.eval(n.value), self.line)
                for _ in range(int(count)):
                    self._loop_body(n.body)
            elif n.mode == "while":
                while truthy(self.eval(n.value)):
                    self._loop_body(n.body)
            elif n.mode == "until":
                while not truthy(self.eval(n.value)):
                    self._loop_body(n.body)
            else:
                while True:
                    self._loop_body(n.body)
        except StopLoop:
            pass

    def x_foreach(self, n):
        seq = self.eval(n.seq)
        if isinstance(seq, dict):
            items = list(seq.keys())
        elif isinstance(seq, str):
            items = list(seq)
        elif is_number(seq):
            items = list(range(1, int(seq) + 1))
        elif hasattr(seq, "items_list"):
            items = seq.items_list()
        elif isinstance(seq, (list, tuple)):
            items = list(seq)
        else:
            raise self.error(f"I can't go through each item of {type_name(seq)}")
        try:
            for i, item in enumerate(items, start=1):
                self.assign(n.name, item)
                if n.index:
                    self.assign(n.index, i)
                self._loop_body(n.body)
        except StopLoop:
            pass

    def x_count(self, n):
        start = to_number(self.eval(n.start), self.line)
        end = to_number(self.eval(n.end), self.line)
        step = to_number(self.eval(n.step), self.line) if n.step is not None else (1 if end >= start and not n.down else -1)
        if n.down and step > 0:
            step = -step
        if step == 0:
            raise self.error("The count step can't be 0")
        i = start
        try:
            while (i <= end + 1e-9) if step > 0 else (i >= end - 1e-9):
                self.assign(n.name, tidy_number(i))
                self._loop_body(n.body)
                i = tidy_number(i + step)
        except StopLoop:
            pass

    def x_break(self, n):
        raise StopLoop()

    def x_skip(self, n):
        raise SkipLoop()

    def x_quit(self, n):
        if self.gui is not None:
            self.gui.quit()
        raise StopProgram()

    # -- tasks
    def x_task(self, n):
        closure = self.frames[-1] if self.frames else None
        self.assign(n.name, Task(n.name, n.params, n.body, closure=closure))

    def x_kind(self, n):
        methods = {}
        for m in n.methods:
            methods[m.name] = Task(m.name, m.params, m.body)
        self.assign(n.name, Kind(n.name, n.fields, methods))

    def x_do(self, n):
        if n.task[0] == "call":
            self.eval(n.task)
            return
        fn = self.eval(n.task)
        args = [self.eval(a) for a in n.args]
        if n.f.get("background"):
            t = threading.Thread(target=self._background, args=(fn, args), daemon=True)
            t.start()
            return
        self.call(fn, args)

    def _background(self, fn, args):
        try:
            self.call(fn, args)
        except MemoError as e:
            sys.stderr.write(str(e) + "\n")

    def x_exprstmt(self, n):
        self.eval(n.expr)

    def x_return(self, n):
        raise GiveBack(self.eval(n.value))

    def x_use(self, n):
        path = self.path(self.eval(n.path))
        if not os.path.splitext(path)[1]:
            path += ".mw"
        if not os.path.exists(path):
            lib = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "library", os.path.basename(path))
            if os.path.exists(lib):
                path = lib
            else:
                raise self.error(f"I can't find the file {path}")
        if path in self.used_files:
            return
        self.used_files.add(path)
        with open(path, encoding="utf-8-sig") as fh:
            tree = Parser(fh.read(), os.path.basename(path)).parse_program()
        old_file, old_line = self.file, self.line
        self.file = os.path.basename(path)
        try:
            self.hoist(tree)
            self.exec_block(tree)
        finally:
            self.file, self.line = old_file, old_line

    def x_runfile(self, n):
        path = self.path(self.eval(n.path))
        with open(path, encoding="utf-8-sig") as fh:
            tree = Parser(fh.read(), os.path.basename(path)).parse_program()
        self.exec_block(tree)

    # -- errors
    def x_try(self, n):
        try:
            self.exec_block(n.body)
        except (StopLoop, SkipLoop, GiveBack, StopProgram):
            raise
        except MemoError as e:
            if n.handler is not None:
                if n.err:
                    self.assign(n.err, e.message)
                self.exec_block(n.handler)
        except Exception as e:  # python problems become friendly messages
            if n.handler is not None:
                if n.err:
                    self.assign(n.err, friendly_python_error(e))
                self.exec_block(n.handler)

    def x_complain(self, n):
        raise Complaint(to_text(self.eval(n.value)), self.line, self.file)

    def x_ensure(self, n):
        if not truthy(self.eval(n.cond)):
            msg = to_text(self.eval(n.msg)) if n.msg is not None else "Something that should be true was not true"
            raise Complaint(msg, self.line, self.file)

    # -- memory
    def x_remember(self, n):
        self.memory.set(to_text(self.eval(n.key)), self.eval(n.value))

    def x_recall(self, n):
        key = to_text(self.eval(n.key))
        if self.memory.has(key):
            value = self.memory.get(key)
        elif n.default is not None:
            value = self.eval(n.default)
        else:
            value = None
        self.assign_target(n.target, value)

    def x_forget(self, n):
        if n.key is None:
            self.memory.clear()
        else:
            self.memory.delete(to_text(self.eval(n.key)))

    # -- files
    def x_filewrite(self, n):
        from .stdlib import files
        files.write_file(self, self.path(self.eval(n.path)), self.eval(n.value), n.mode)

    def x_fileread(self, n):
        from .stdlib import files
        text = files.read_file(self, self.path(self.eval(n.path)))
        self.assign_target(n.target, text.splitlines() if n.lines else text)

    def x_save(self, n):
        from .stdlib import files
        files.save_value(self, self.eval(n.value), self.path(self.eval(n.path)))

    def x_load(self, n):
        from .stdlib import files
        self.assign_target(n.target, files.load_value(self, self.path(self.eval(n.path))))

    def x_filedelete(self, n):
        from .stdlib import files
        files.delete(self, self.path(self.eval(n.path)), n.f.get("folder", False))

    def x_filecopy(self, n):
        from .stdlib import files
        files.copy(self, self.path(self.eval(n.src)), self.path(self.eval(n.dst)), n.move)

    def x_mkdir(self, n):
        os.makedirs(self.path(self.eval(n.path)), exist_ok=True)

    def x_openthing(self, n):
        from .stdlib import system
        what = to_text(self.eval(n.what))
        system.open_thing(self, what)

    def x_download(self, n):
        from .stdlib import files
        url = to_text(self.eval(n.url))
        if n.path is not None:
            files.download(self, url, self.path(self.eval(n.path)))
        else:
            self.assign_target(n.target, files.fetch_text(self, url))

    def x_clipboard(self, n):
        from .stdlib import system
        system.set_clipboard(self, to_text(self.eval(n.value)))

    def x_erase(self, n):
        what = self.eval(n.what)
        if hasattr(what, "delete"):
            what.delete()
        else:
            raise self.error("I can only delete files (delete file \"x.txt\"), shapes and widgets")

    # -- time
    def seconds(self, amount, unit):
        return to_number(amount, self.line) * UNIT_SECONDS.get(unit, 1)

    def x_wait(self, n):
        secs = self.seconds(self.eval(n.amount), n.unit)
        if self.gui is not None and self.gui.has_windows():
            self.gui.sleep(secs)
        else:
            time.sleep(max(0, secs))

    def x_every(self, n):
        gui = self.ensure_gui()
        ms = int(self.seconds(self.eval(n.amount), n.unit) * 1000)
        if n.task:
            fn = self.lookup(n.task)
        else:
            fn = Task("every", [], n.body, closure=self.frames[-1] if self.frames else None)
        gui.every(max(1, ms), fn)

    def x_after(self, n):
        gui = self.ensure_gui()
        ms = int(self.seconds(self.eval(n.amount), n.unit) * 1000)
        fn = self.lookup(n.task) if n.task else Task("after", [], n.body, closure=self.frames[-1] if self.frames else None)
        gui.after(max(1, ms), fn)

    def x_stoptimers(self, n):
        if self.gui is not None:
            self.gui.stop_timers()

    def x_stoptimer(self, n):
        if self.gui is not None:
            self.gui.stop_timers()

    # -- console & sound
    def x_clearscreen(self, n):
        from .stdlib import system
        system.clear_screen(self)

    def x_clearthing(self, n):
        what = self.eval(n.what)
        if isinstance(what, (list, dict)):
            what.clear()
        elif hasattr(what, "clear"):
            what.clear()
        elif isinstance(what, str):
            self.assign_target(n.what, "")
        else:
            raise self.error(f"I don't know how to clear {type_name(what)}")

    def x_consolecolor(self, n):
        from .stdlib import system
        system.console_color(self, to_text(self.eval(n.value)))

    def x_beep(self, n):
        from .stdlib import sound
        sound.beep(self, int(to_number(self.eval(n.times))))

    def x_tone(self, n):
        from .stdlib import sound
        freq = self.eval(n.freq)
        if not (isinstance(freq, str) and not looks_like_number(freq)):
            freq = to_number(freq)
        sound.tone(self, freq, to_number(self.eval(n.dur)))

    def x_sound(self, n):
        from .stdlib import sound
        sound.play(self, self.path(self.eval(n.path)), n.loop)

    def x_stopsound(self, n):
        from .stdlib import sound
        sound.stop(self)

    def x_speak(self, n):
        from .stdlib import sound
        sound.speak(self, to_text(self.eval(n.value)))

    # -- GUI
    def x_window(self, n):
        self.ensure_gui().make_window(n)

    def x_widget(self, n):
        self.ensure_gui().add_widget(n)

    def x_when(self, n):
        self.ensure_gui().when(n)

    def x_show(self, n):
        what = self.eval(n.what)
        if hasattr(what, "show"):
            what.show()
        else:
            self.write(to_text(what) + "\n")

    def x_hide(self, n):
        what = self.eval(n.what)
        if hasattr(what, "hide"):
            what.hide()
        else:
            raise self.error("I can only hide windows, widgets and shapes")

    def x_closewin(self, n):
        what = self.eval(n.what)
        if hasattr(what, "close"):
            what.close()

    def x_popup(self, n):
        title = to_text(self.eval(n.title)) if n.title is not None else None
        self.ensure_gui().popup(to_text(self.eval(n.text)), title, n.style)

    def x_focus(self, n):
        w = self.eval(n.what)
        if hasattr(w, "focus"):
            w.focus()

    def x_enable(self, n):
        w = self.eval(n.what)
        if hasattr(w, "set_enabled"):
            w.set_enabled(n.on)

    def x_menu(self, n):
        self.ensure_gui().add_menu(n)

    # -- graphics
    def x_canvas(self, n):
        from .stdlib import graphics
        graphics.make_canvas(self, n)

    def x_draw(self, n):
        from .stdlib import graphics
        graphics.draw(self, n)

    def x_fillcanvas(self, n):
        c = self.lookup(n.canvas)
        if hasattr(c, "canvas_object") and c.canvas_object() is not None:
            c = c.canvas_object()
        if not hasattr(c, "fill"):
            raise self.error(f"'{n.canvas}' is not a canvas")
        c.fill(to_text(self.eval(n.color)))

    def x_model(self, n):
        from .stdlib import graphics
        graphics.make_model(self, n)

    def x_place(self, n):
        from .stdlib import graphics
        graphics.place(self, n)

    def shapes_of(self, node):
        from .stdlib.graphics import ShapeGroup
        v = self.eval(node)
        if isinstance(v, list) and all(isinstance(x, ShapeGroup) for x in v):
            return v
        if not isinstance(v, ShapeGroup) and not hasattr(v, "move_by"):
            raise self.error(f"I can only move or change shapes, but this is {type_name(v)}")
        return [v]

    def x_moveto(self, n):
        x, y = to_number(self.eval(n.x)), to_number(self.eval(n.y))
        for s in self.shapes_of(n.what):
            s.move_to(x, y)
        self.pump()

    def x_moveby(self, n):
        x, y = to_number(self.eval(n.x)), to_number(self.eval(n.y))
        for s in self.shapes_of(n.what):
            s.move_by(x, y)
        self.pump()

    def x_forward(self, n):
        amount = to_number(self.eval(n.amount))
        for s in self.shapes_of(n.what):
            s.forward(amount)

    def x_towards(self, n):
        tx, ty, amount = (to_number(self.eval(n.x)), to_number(self.eval(n.y)), to_number(self.eval(n.amount)))
        for s in self.shapes_of(n.what):
            s.move_towards(tx, ty, amount)

    def x_rotate(self, n):
        a = to_number(self.eval(n.angle))
        for s in self.shapes_of(n.what):
            if n.absolute:
                s.rotate_to(a)
            else:
                s.rotate_by(a)

    def x_scale(self, n):
        f = to_number(self.eval(n.factor))
        for s in self.shapes_of(n.what):
            s.scale_by(f)

    def x_resize(self, n):
        w, h = to_number(self.eval(n.w)), to_number(self.eval(n.h))
        for s in self.shapes_of(n.what):
            s.resize(w, h)

    def x_flip(self, n):
        for s in self.shapes_of(n.what):
            s.flip(n.axis)

    def x_recolor(self, n):
        c = to_text(self.eval(n.color))
        what = self.eval(n.what)
        if hasattr(what, "recolor"):
            what.recolor(c)
        else:
            raise self.error("I can only recolor shapes and widgets")

    def x_layer(self, n):
        for s in self.shapes_of(n.what):
            s.to_front() if n.where == "front" else s.to_back()

    def x_export(self, n):
        c = self.lookup(n.canvas)
        if hasattr(c, "canvas_object") and c.canvas_object() is not None:
            c = c.canvas_object()
        if not hasattr(c, "export"):
            raise self.error(f"'{n.canvas}' is not a canvas or picture")
        c.export(self.path(self.eval(n.path)))

    def x_savemodel(self, n):
        m = self.eval(n.model)
        if not hasattr(m, "save"):
            raise self.error("That is not a model")
        m.save(self.path(self.eval(n.path)))

    def x_loadmodel(self, n):
        from .stdlib import graphics
        self.assign(n.name, graphics.Model.load(self.path(self.eval(n.path)), n.name))

    def x_animate(self, n):
        x, y = to_number(self.eval(n.x)), to_number(self.eval(n.y))
        secs = self.seconds(self.eval(n.dur), n.unit)
        shapes = self.shapes_of(n.what)
        steps = max(1, int(secs * 60))
        starts = [(s.cx(), s.cy()) for s in shapes]
        for i in range(1, steps + 1):
            t = i / steps
            t = t * t * (3 - 2 * t)  # smooth
            for s, (sx, sy) in zip(shapes, starts):
                s.move_to(sx + (x - sx) * t, sy + (y - sy) * t)
            if self.gui is not None and self.gui.has_windows():
                self.gui.sleep(secs / steps)

    def x_bounce(self, n):
        shapes = self.shapes_of(n.what)
        for s in shapes:
            canvas = self.lookup(n.canvas) if n.canvas else s.canvas
            if hasattr(canvas, "canvas_object") and canvas.canvas_object() is not None:
                canvas = canvas.canvas_object()
            left, top, right, bottom = s.bbox()
            sx, sy = to_number(self.lookup(n.sx)), to_number(self.lookup(n.sy))
            if left < 0 and sx < 0 or right > canvas.width and sx > 0:
                self.assign(n.sx, -sx)
            if top < 0 and sy < 0 or bottom > canvas.height and sy > 0:
                self.assign(n.sy, -sy)

    # ------------------------------------------------------------ calling
    def call(self, fn, args):
        if isinstance(fn, Builtin):
            if len(args) < fn.min_args or (fn.max_args is not None and len(args) > fn.max_args):
                expected = fn.min_args if fn.max_args == fn.min_args else f"{fn.min_args} to {fn.max_args if fn.max_args is not None else 'many'}"
                raise self.error(f"'{fn.name}' needs {expected} value(s) but got {len(args)}")
            try:
                return fn.fn(*args)
            except (MemoError, StopProgram, StopLoop, SkipLoop, GiveBack):
                raise
            except RecursionError:
                raise self.error("A task kept calling itself forever")
            except Exception as e:
                raise self.error(f"'{fn.name}' had a problem: {friendly_python_error(e)}")
        if isinstance(fn, Task):
            if len(args) > len(fn.params):
                raise self.error(f"The task '{fn.name}' takes {len(fn.params)} value(s) but got {len(args)}")
            if len(self.frames) > MAX_DEPTH:
                raise self.error(f"The task '{fn.name}' called itself too many times", hint="Make sure it stops calling itself at some point")
            frame = {p: (args[i] if i < len(args) else None) for i, p in enumerate(fn.params)}
            if fn.closure is not None:
                frame["\x00closure"] = fn.closure
            if fn.owner is not None:
                frame["me"] = fn.owner
            self.frames.append(frame)
            saved_line = self.line
            try:
                self.exec_block(fn.body)
            except GiveBack as g:
                return g.value
            except StopLoop:
                raise self.error("'stop' was used outside of a loop (use 'give back' to leave a task)")
            finally:
                self.frames.pop()
                self.line = saved_line
            return None
        if isinstance(fn, Kind):
            inst = Instance(fn)
            for i, field in enumerate(fn.fields):
                inst.fields[field] = args[i] if i < len(args) else None
            for name, method in fn.methods.items():
                pass
            setup = fn.methods.get("setup") or fn.methods.get("start") or fn.methods.get("create")
            if setup is not None and len(args) > len(fn.fields):
                self.call(setup.bound(inst), args[len(fn.fields):])
            elif setup is not None and not setup.params:
                self.call(setup.bound(inst), [])
            return inst
        if callable(fn):
            return fn(*args)
        raise self.error(f"{to_text(fn, True)} is not a task, so I can't run it")

    # ------------------------------------------------------------ expressions
    def eval(self, node):
        kind = node[0]
        if kind == "num" or kind == "str":
            return node[1]
        if kind == "var":
            return self.lookup(node[1])
        if kind == "interp":
            return "".join(to_text(self.eval(p)) for p in node[1])
        if kind == "bin":
            return self.binop(node[1], self.eval(node[2]), self.eval(node[3]))
        if kind == "cmp":
            return self.compare(node[1], self.eval(node[2]), self.eval(node[3]))
        if kind == "and":
            return truthy(self.eval(node[1])) and truthy(self.eval(node[2]))
        if kind == "or":
            left = self.eval(node[1])
            if truthy(left):
                return True
            return truthy(self.eval(node[2]))
        if kind == "not":
            return not truthy(self.eval(node[1]))
        if kind == "neg":
            return tidy_number(-to_number(self.eval(node[1]), self.line))
        if kind == "bool":
            return node[1]
        if kind == "nothing":
            return None
        if kind == "list":
            return [self.eval(x) for x in node[1]]
        if kind == "book":
            return {to_text(self.eval(k)) if not is_number(self.eval(k)) else self.eval(k): self.eval(v) for k, v in node[1]}
        if kind == "index":
            return self.get_index(self.eval(node[1]), self.eval(node[2]))
        if kind == "slice":
            return self.get_slice(self.eval(node[1]), node[2] and self.eval(node[2]), node[3] and self.eval(node[3]))
        if kind == "call":
            fn = self.eval(node[1])
            args = [self.eval(a) for a in node[2]]
            return self.call(fn, args)
        if kind == "prop":
            return self.prop_or_call(node[1], node[2])
        if kind == "empty":
            v = self.eval(node[1])
            if v is None:
                return True
            if isinstance(v, (str, list, dict)):
                return len(v) == 0 if not isinstance(v, str) else v.strip() == ""
            if hasattr(v, "is_empty"):
                return v.is_empty()
            return False
        if kind == "even":
            return to_number(self.eval(node[1]), self.line) % 2 == 0
        if kind == "between":
            x = to_number(self.eval(node[1]), self.line)
            a = to_number(self.eval(node[2]), self.line)
            b = to_number(self.eval(node[3]), self.line)
            return min(a, b) <= x <= max(a, b)
        if kind == "divisible":
            d = to_number(self.eval(node[2]), self.line)
            return d != 0 and to_number(self.eval(node[1]), self.line) % d == 0
        if kind == "typeis":
            v = self.eval(node[1])
            want = node[2]
            t = type_name(v)
            want = {"string": "text", "word": "text", "yes": "yes/no", "picture": "canvas", "integer": "number"}.get(want, want)
            if node[2] == "integer":
                return is_number(v) and float(v).is_integer()
            if want == "number" and isinstance(v, str):
                return looks_like_number(v)
            return t == want or (want == "shape" and t in ("shape", "model")) or (want == "widget" and hasattr(v, "widget_kind"))
        raise self.error(f"Unknown expression {kind}")

    def prop_or_call(self, word, objnode):
        obj = self.eval(objnode)
        if word in ("my",):
            return obj
        handled, value = self.try_prop(obj, word)
        if handled:
            return value
        fn = self.builtins.get(word)
        if fn is None:
            g = self.globals.get(word)
            if isinstance(g, (Task, Builtin)):
                fn = g
        if fn is not None:
            return self.call(fn, [obj])
        if isinstance(obj, dict):
            raise self.error(f"The book has no '{word}' in it", hint=f"It has: {', '.join(map(to_text, obj.keys())) or 'nothing yet'}")
        guess = suggest(word, list(self.builtins))
        raise self.error(f"I don't know what '{word} of' means for {type_name(obj)}", hint=f"Did you mean '{guess} of'?" if guess else None)

    def try_prop(self, obj, word):
        if isinstance(obj, Instance):
            if word in obj.fields:
                return True, obj.fields[word]
            if word in obj.kind.methods:
                return True, obj.kind.methods[word].bound(obj)
            return False, None
        if isinstance(obj, dict):
            for k in obj:
                if isinstance(k, str) and k.lower() == word:
                    return True, obj[k]
            return False, None
        getter = getattr(obj, "get_prop", None)
        if getter is not None:
            try:
                return True, getter(word)
            except KeyError:
                return False, None
        return False, None

    def get_prop(self, obj, word):
        handled, value = self.try_prop(obj, word)
        if handled:
            return value
        if word in self.builtins:
            return self.call(self.builtins[word], [obj])
        raise self.error(f"{type_name(obj)} has no '{word}'")

    def set_prop(self, obj, word, value):
        if isinstance(obj, Instance):
            obj.fields[word] = value
            return
        if isinstance(obj, dict):
            for k in obj:
                if isinstance(k, str) and k.lower() == word:
                    obj[k] = value
                    return
            obj[word] = value
            return
        setter = getattr(obj, "set_prop", None)
        if setter is not None:
            try:
                setter(word, value)
                return
            except KeyError:
                raise self.error(f"I can't set the '{word}' of a {type_name(obj)}")
        raise self.error(f"I can't set the '{word}' of {type_name(obj)}")

    # -- indexing (lists start at 1, like people count)
    def list_index(self, seq, idx):
        if not is_number(idx):
            if looks_like_number(idx):
                idx = to_number(idx)
            else:
                raise self.error(f"A position in a list must be a number, not {to_text(idx, True)}")
        i = int(idx)
        n = len(seq)
        if i == 0:
            raise self.error("Lists start at position 1, not 0", hint="Use 1 for the first item, -1 for the last")
        real = i - 1 if i > 0 else n + i
        if real < 0 or real >= n:
            raise self.error(f"There is no item {i}; there are only {n} item(s)")
        return real

    def get_index(self, obj, idx):
        if isinstance(obj, (list, str)):
            return obj[self.list_index(obj, idx)]
        if isinstance(obj, dict):
            if idx in obj:
                return obj[idx]
            if isinstance(idx, str):
                for k in obj:
                    if isinstance(k, str) and k.lower() == idx.lower():
                        return obj[k]
            return None
        if isinstance(obj, Instance):
            return obj.fields.get(to_text(idx))
        if hasattr(obj, "get_index"):
            return obj.get_index(idx)
        raise self.error(f"I can't look inside {type_name(obj)} with [ ]")

    def set_index(self, obj, idx, value):
        if isinstance(obj, list):
            if is_number(idx) and int(idx) == len(obj) + 1:
                obj.append(value)
                return
            obj[self.list_index(obj, idx)] = value
        elif isinstance(obj, dict):
            if isinstance(idx, str):
                for k in obj:
                    if isinstance(k, str) and k.lower() == idx.lower():
                        obj[k] = value
                        return
            obj[idx] = value
        elif isinstance(obj, Instance):
            obj.fields[to_text(idx)] = value
        else:
            raise self.error(f"I can't change part of {type_name(obj)}")

    def get_slice(self, obj, a, b):
        if not isinstance(obj, (list, str)):
            raise self.error("I can only take part of a list or text")
        start = 0 if a is None else (int(to_number(a)) - 1 if to_number(a) > 0 else len(obj) + int(to_number(a)))
        end = len(obj) if b is None else (int(to_number(b)) if to_number(b) >= 0 else len(obj) + int(to_number(b)) + 1)
        return obj[max(0, start):max(0, end)]

    # -- operators
    def binop(self, op, a, b):
        try:
            if op == "join":
                return to_text(a) + to_text(b)
            if op == "+":
                if is_number(a) and is_number(b):
                    return tidy_number(a + b)
                if isinstance(a, list):
                    return a + (b if isinstance(b, list) else [b])
                if isinstance(a, dict) and isinstance(b, dict):
                    c = dict(a); c.update(b); return c
                if isinstance(a, str) and isinstance(b, str):
                    if looks_like_number(a) and looks_like_number(b) and False:
                        return tidy_number(to_number(a) + to_number(b))
                    return a + b
                if (isinstance(a, str) or isinstance(b, str)):
                    if (is_number(a) and looks_like_number(b)) or (is_number(b) and looks_like_number(a)):
                        return tidy_number(to_number(a) + to_number(b))
                    return to_text(a) + to_text(b)
                if a is None or b is None:
                    raise self.error("I can't add 'nothing'. One of the values has not been set yet")
                return tidy_number(to_number(a) + to_number(b))
            if op == "*" and isinstance(a, str) and is_number(b) and not looks_like_number(a):
                return a * int(b)
            if op == "*" and isinstance(a, list) and is_number(b):
                return a * int(b)
            x = to_number(a, self.line, "the left side")
            y = to_number(b, self.line, "the right side")
            if op == "-":
                return tidy_number(x - y)
            if op == "*":
                return tidy_number(x * y)
            if op == "/":
                if y == 0:
                    raise self.error("You can't divide by zero")
                return tidy_number(x / y)
            if op == "%":
                if y == 0:
                    raise self.error("You can't divide by zero")
                return tidy_number(x % y)
            if op == "^":
                return tidy_number(x ** y)
        except OverflowError:
            raise self.error("That number got too big")
        raise self.error(f"Unknown operator {op}")

    def compare(self, op, a, b):
        if op == "==":
            return same(a, b)
        if op == "!=":
            return not same(a, b)
        if op == "contains":
            if isinstance(a, str):
                return to_text(b).lower() in a.lower()
            if isinstance(a, list):
                return any(same(x, b) for x in a)
            if isinstance(a, dict):
                return any(same(k, b) for k in a)
            if a is None:
                return False
            if hasattr(a, "contains"):
                return a.contains(b)
            raise self.error(f"I can't look inside {type_name(a)}")
        if op == "startswith":
            return to_text(a).lower().startswith(to_text(b).lower())
        if op == "endswith":
            return to_text(a).lower().endswith(to_text(b).lower())
        if op == "touches":
            if hasattr(a, "touches"):
                return a.touches(b)
            raise self.error("Only shapes can touch each other")
        if (isinstance(a, str) and not looks_like_number(a)) or (isinstance(b, str) and not looks_like_number(b)):
            x, y = to_text(a).lower(), to_text(b).lower()
        else:
            x, y = to_number(a, self.line, "the left side"), to_number(b, self.line, "the right side")
        if op == ">":
            return x > y
        if op == "<":
            return x < y
        if op == ">=":
            return x >= y
        if op == "<=":
            return x <= y
        raise self.error(f"Unknown comparison {op}")


def sort_key(v):
    if is_number(v):
        return (0, v, "")
    if isinstance(v, str):
        if looks_like_number(v):
            return (0, to_number(v), "")
        return (1, 0, v.lower())
    return (2, 0, to_text(v))


def friendly_python_error(e):
    if isinstance(e, MemoError):
        return e.message
    if isinstance(e, FileNotFoundError):
        return f"I can't find the file {getattr(e, 'filename', '')}"
    if isinstance(e, PermissionError):
        return f"I'm not allowed to use {getattr(e, 'filename', 'that file')}"
    if isinstance(e, ZeroDivisionError):
        return "You can't divide by zero"
    if isinstance(e, (ValueError, TypeError)):
        return "A value was the wrong kind: " + str(e)
    return str(e) or type(e).__name__
