"""Memowrite Studio - a friendly editor for writing and running Memowrite programs.

F5 run   |   Shift+F5 stop   |   F7 check for mistakes   |   Ctrl+S save   |   Ctrl+F find
"""

import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from . import __version__
from .parser import KNOWN_COMMANDS

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

C = {
    "bg": "#16171d", "panel": "#1f2029", "panel2": "#262833", "fg": "#e4e6f0", "muted": "#8a8fa6", "gutter": "#5a5f78",
    "line": "#1d1e26", "select": "#33406e", "accent": "#5c7cfa", "accent2": "#4c6ef5", "border": "#30323f",
    "kw": "#c792ea", "str": "#c3e88d", "num": "#f78c6c", "comment": "#676e95", "builtin": "#82aaff",
    "shape": "#ffcb6b", "bool": "#ff9cac", "error": "#ff6b81", "ok": "#7ee2a8", "out": "#d6d8e4",
}

KEYWORDS = sorted(set(KNOWN_COMMANDS) | {
    "end", "done", "otherwise", "else", "then", "times", "with", "into", "to", "from", "by", "each", "in", "of", "is",
    "not", "and", "or", "more", "less", "than", "at", "least", "most", "as", "called", "titled", "sized", "saying",
    "doing", "back", "fails", "it", "task", "list", "book", "window", "model", "canvas", "picture", "kind", "file",
    "forever", "while", "until", "every", "seconds", "second", "milliseconds", "contains", "empty", "between", "on",
    "when", "clicked", "pressed", "key", "mouse", "color", "colour", "size", "outline", "width", "the", "a", "an",
    "background", "program", "memory", "everything", "equal", "same", "plus", "minus", "divided", "mod", "power",
})
VALUES = ["yes", "no", "true", "false", "nothing", "pi"]
SHAPES_WORDS = ["circle", "rectangle", "square", "line", "triangle", "polygon", "star", "text", "dot", "arc", "heart",
                "image", "arrow", "hexagon", "pentagon", "diamond", "path", "grid", "ring", "ellipse", "oval", "box",
                "button", "label", "input", "slider", "checkbox", "dropdown", "textbox", "listbox", "table", "panel",
                "row", "tabs", "tab", "heading", "progress", "spinner", "radio", "link", "separator", "space", "colorpicker"]

SNIPPETS = {
    "Hello world": 'say "Hello, world!"\n',
    "Ask a question": 'ask "What is your name?" into name\nsay "Nice to meet you, {name}!"\n',
    "If / otherwise": 'if score is more than 10 then\n    say "Great!"\notherwise\n    say "Keep going"\nend\n',
    "Repeat loop": 'repeat 5 times\n    say "again!"\nend\n',
    "Count loop": 'count i from 1 to 10\n    say i\nend\n',
    "For each": 'make list fruits with "apple", "banana", "cherry"\nfor each fruit in fruits\n    say fruit\nend\n',
    "Task": 'make task greet with who\n    say "Hello, " + who\nend\n\ndo greet with "Sam"\n',
    "Window app": ('make window app titled "My App" sized 420 by 320\n'
                   'add heading title to app saying "My App"\n'
                   'add input box nameBox to app placeholder "Type your name"\n'
                   'add button go to app saying "Say hi" doing hello\n'
                   'add label answer to app saying ""\n\n'
                   'make task hello\n    set text of answer to "Hi " + text of nameBox + "!"\nend\n'),
    "2D drawing": ('make window art titled "Drawing" sized 520 by 400\n'
                   'add canvas board to art sized 500 by 380 background "sky"\n'
                   'draw rectangle on board at 0, 300 size 500 by 80 color "grass"\n'
                   'draw circle on board at 420, 70 size 40 color "sun"\n'
                   'draw star on board at 120, 80 size 25 color "white"\n'),
    "2D model": ('make model tree\n    rectangle at -8, 0 size 16 by 50 color "wood"\n'
                 '    circle at 0, -15 size 35 color "leaf"\nend\n\n'
                 'place model tree on board at 100, 250 called tree1\n'),
    "Game loop": ('set speed to 4\nevery 16 milliseconds do update\n\n'
                  'make task update\n    if key_down("left") then move player by -speed, 0\n'
                  '    if key_down("right") then move player by speed, 0\nend\n'),
    "File.Memory": ('recall "high score" into best or 0\nsay "Best so far: {best}"\n'
                    'remember "high score" as best + 1\n'),
    "Try / if it fails": 'try\n    read file "notes.txt" into notes\nif it fails as problem\n    say "Could not read: " + problem\nend\n',
    "Kind (blueprint)": ('make kind pet with name, sound\n    make task speak\n        say my name + " says " + my sound\n    end\nend\n\n'
                         'set rex to pet("Rex", "woof")\nrex.speak()\n'),
}


def python_console_exe():
    exe = sys.executable
    if exe.lower().endswith("pythonw.exe"):
        alt = exe[:-len("pythonw.exe")] + "python.exe"
        if os.path.exists(alt):
            return alt
    return exe


class LineNumbers(tk.Canvas):
    def __init__(self, master, text, **kw):
        super().__init__(master, **kw)
        self.text = text

    def redraw(self, *_):
        self.delete("all")
        i = self.text.index("@0,0")
        current = self.text.index("insert").split(".")[0]
        while True:
            d = self.text.dlineinfo(i)
            if d is None:
                break
            y = d[1]
            n = str(i).split(".")[0]
            self.create_text(self.winfo_width() - 10, y + 2, anchor="ne", text=n, font=self.text.font_small,
                             fill=C["fg"] if n == current else C["gutter"])
            i = self.text.index(f"{i}+1line")
            if i == self.text.index(f"{i} lineend+1c") and False:
                break
            if self.text.compare(i, ">=", "end"):
                break


class Editor(tk.Text):
    def __init__(self, master, **kw):
        super().__init__(master, **kw)
        self.font_small = ("Consolas" if os.name == "nt" else "DejaVu Sans Mono", 10)


class Studio:
    def __init__(self, root, path=None):
        self.root = root
        self.path = None
        self.proc = None
        self.out_queue = queue.Queue()
        self.dirty = False
        self.highlight_job = None
        root.title("Memowrite Studio")
        root.geometry("1120x720")
        root.minsize(760, 480)
        root.configure(bg=C["bg"])
        self._set_icon()
        self._style()
        self._build()
        self._bind_keys()
        if path and os.path.exists(path):
            self.open_path(path)
        else:
            self.editor.insert("1.0", WELCOME)
            self.highlight()
            self.dirty = False
            self._title()
        root.after(40, self._poll_output)
        root.protocol("WM_DELETE_WINDOW", self.quit)

    # ------------------------------------------------------------ setup
    def _set_icon(self):
        try:
            ico = os.path.join(HERE, "branding", "memowrite.ico")
            png = os.path.join(HERE, "branding", "memowrite-64.png")
            if os.name == "nt" and os.path.exists(ico):
                self.root.iconbitmap(default=ico)
            elif os.path.exists(png):
                self._icon = tk.PhotoImage(file=png)
                self.root.iconphoto(True, self._icon)
            logo = os.path.join(HERE, "branding", "memowrite-32.png")
            self.logo_img = tk.PhotoImage(file=logo) if os.path.exists(logo) else None
        except Exception:
            self.logo_img = None

    def _style(self):
        st = ttk.Style(self.root)
        try:
            st.theme_use("clam")
        except Exception:
            pass
        st.configure("Vertical.TScrollbar", background=C["panel2"], troughcolor=C["bg"], bordercolor=C["bg"],
                     arrowcolor=C["muted"], lightcolor=C["panel2"], darkcolor=C["panel2"])
        st.configure("TPanedwindow", background=C["border"])
        st.configure("Studio.Treeview", background=C["panel"], fieldbackground=C["panel"], foreground=C["fg"],
                     bordercolor=C["panel"], rowheight=24, font=(self.ui_font(), 10))
        st.map("Studio.Treeview", background=[("selected", C["select"])])

    def ui_font(self):
        return "Segoe UI" if os.name == "nt" else "DejaVu Sans"

    def mono(self):
        return "Consolas" if os.name == "nt" else "DejaVu Sans Mono"

    def _button(self, parent, text, cmd, accent=False, tip=None):
        bg = C["accent"] if accent else C["panel2"]
        b = tk.Button(parent, text=text, command=cmd, bg=bg, fg="#ffffff" if accent else C["fg"], relief="flat", bd=0,
                      padx=12, pady=5, activebackground=C["accent2"] if accent else C["border"],
                      activeforeground="#ffffff", font=(self.ui_font(), 9, "bold" if accent else "normal"), cursor="hand2",
                      highlightthickness=0)
        b.pack(side="left", padx=(0, 6), pady=8)
        return b

    def _build(self):
        top = tk.Frame(self.root, bg=C["panel"], height=46)
        top.pack(fill="x")
        if self.logo_img is not None:
            tk.Label(top, image=self.logo_img, bg=C["panel"]).pack(side="left", padx=(12, 6))
        tk.Label(top, text="Memowrite Studio", bg=C["panel"], fg=C["fg"], font=(self.ui_font(), 12, "bold")).pack(side="left", padx=(0, 18))
        self.run_btn = self._button(top, "▶  Run  (F5)", self.run, accent=True)
        self._button(top, "■  Stop", self.stop)
        self._button(top, "✓  Check", self.check)
        self._button(top, "New", self.new_file)
        self._button(top, "Open", self.open_file)
        self._button(top, "Save", self.save)
        examples_btn = self._button(top, "Examples ▾", lambda: None)
        insert_btn = self._button(top, "Insert ▾", lambda: None)
        help_btn = self._button(top, "Help", self.open_help)

        ex_menu = tk.Menu(self.root, tearoff=0, bg=C["panel2"], fg=C["fg"], activebackground=C["accent"], bd=0)
        ex_dir = os.path.join(HERE, "examples")
        if os.path.isdir(ex_dir):
            for f in sorted(os.listdir(ex_dir)):
                if f.endswith(".mw"):
                    ex_menu.add_command(label=f[:-3].replace("_", " "), command=lambda p=os.path.join(ex_dir, f): self.open_path(p))
        examples_btn.configure(command=lambda: ex_menu.tk_popup(examples_btn.winfo_rootx(), examples_btn.winfo_rooty() + examples_btn.winfo_height()))
        in_menu = tk.Menu(self.root, tearoff=0, bg=C["panel2"], fg=C["fg"], activebackground=C["accent"], bd=0)
        for name, code in SNIPPETS.items():
            in_menu.add_command(label=name, command=lambda c=code: self.insert_snippet(c))
        insert_btn.configure(command=lambda: in_menu.tk_popup(insert_btn.winfo_rootx(), insert_btn.winfo_rooty() + insert_btn.winfo_height()))

        paned = tk.PanedWindow(self.root, orient="vertical", bg=C["border"], sashwidth=4, bd=0)
        paned.pack(fill="both", expand=True)

        edit_frame = tk.Frame(paned, bg=C["bg"])
        self.editor = Editor(edit_frame, bg=C["bg"], fg=C["fg"], insertbackground="#ffffff", selectbackground=C["select"],
                             font=(self.mono(), 12), undo=True, wrap="none", relief="flat", bd=0, padx=10, pady=8,
                             tabs=("1c",), highlightthickness=0, autoseparators=True, maxundo=-1)
        self.lines = LineNumbers(edit_frame, self.editor, width=52, bg=C["panel"], highlightthickness=0, bd=0)
        ys = ttk.Scrollbar(edit_frame, orient="vertical", command=self._yview)
        self.editor.configure(yscrollcommand=lambda a, b: (ys.set(a, b), self.lines.redraw()))
        self.lines.pack(side="left", fill="y")
        ys.pack(side="right", fill="y")
        self.editor.pack(side="left", fill="both", expand=True)
        paned.add(edit_frame, stretch="always", minsize=200)

        out_frame = tk.Frame(paned, bg=C["panel"])
        head = tk.Frame(out_frame, bg=C["panel"])
        head.pack(fill="x")
        tk.Label(head, text="OUTPUT", bg=C["panel"], fg=C["muted"], font=(self.ui_font(), 8, "bold")).pack(side="left", padx=12, pady=4)
        clear = tk.Label(head, text="clear", bg=C["panel"], fg=C["muted"], cursor="hand2", font=(self.ui_font(), 8))
        clear.pack(side="right", padx=12)
        clear.bind("<Button-1>", lambda e: self.clear_output())
        self.output = tk.Text(out_frame, bg=C["panel"], fg=C["out"], font=(self.mono(), 11), relief="flat", bd=0, padx=12,
                              pady=6, height=10, wrap="word", highlightthickness=0, insertbackground="#fff")
        self.output.pack(fill="both", expand=True)
        self.output.tag_configure("err", foreground=C["error"])
        self.output.tag_configure("ok", foreground=C["ok"])
        self.output.tag_configure("info", foreground=C["muted"])
        self.output.tag_configure("link", underline=True)
        for name, col in (("red", "#ff6b81"), ("green", "#7ee2a8"), ("yellow", "#ffd166"), ("blue", "#82aaff"),
                          ("purple", "#c792ea"), ("cyan", "#89ddff"), ("white", "#ffffff"), ("gray", "#8a8fa6")):
            self.output.tag_configure("c_" + name, foreground=col)
        self.output.configure(state="disabled")
        self.output.tag_bind("err", "<Button-1>", self._jump_to_error)
        inrow = tk.Frame(out_frame, bg=C["panel2"])
        inrow.pack(fill="x")
        tk.Label(inrow, text="›", bg=C["panel2"], fg=C["accent"], font=(self.mono(), 13, "bold")).pack(side="left", padx=(10, 4))
        self.input = tk.Entry(inrow, bg=C["panel2"], fg=C["fg"], insertbackground="#fff", relief="flat",
                              font=(self.mono(), 11), highlightthickness=0)
        self.input.pack(side="left", fill="x", expand=True, ipady=6)
        self.input.bind("<Return>", self.send_input)
        self._input_hint()
        paned.add(out_frame, stretch="never", minsize=120, height=230)

        status = tk.Frame(self.root, bg=C["accent"], height=22)
        status.pack(fill="x")
        self.status = tk.Label(status, text="Ready", bg=C["accent"], fg="#ffffff", font=(self.ui_font(), 9), anchor="w")
        self.status.pack(side="left", padx=10)
        self.pos = tk.Label(status, text="Ln 1, Col 1", bg=C["accent"], fg="#ffffff", font=(self.ui_font(), 9))
        self.pos.pack(side="right", padx=10)
        tk.Label(status, text=f"Memowrite {__version__}", bg=C["accent"], fg="#dfe4ff", font=(self.ui_font(), 9)).pack(side="right", padx=10)

        ed = self.editor
        ed.tag_configure("kw", foreground=C["kw"])
        ed.tag_configure("str", foreground=C["str"])
        ed.tag_configure("num", foreground=C["num"])
        ed.tag_configure("comment", foreground=C["comment"], font=(self.mono(), 12, "italic"))
        ed.tag_configure("builtin", foreground=C["builtin"])
        ed.tag_configure("shape", foreground=C["shape"])
        ed.tag_configure("bool", foreground=C["bool"])
        ed.tag_configure("interp", foreground=C["fg"])
        ed.tag_configure("errline", background="#3a1d27")
        ed.tag_configure("found", background="#5c4d10")
        ed.tag_raise("sel")

    def _input_hint(self):
        hint = "type here to answer an 'ask' question, then press Enter"

        def on(e=None):
            if self.input.get() == hint:
                self.input.delete(0, "end")
                self.input.configure(fg=C["fg"])

        def off(e=None):
            if not self.input.get():
                self.input.insert(0, hint)
                self.input.configure(fg=C["muted"])
        self.input.bind("<FocusIn>", on)
        self.input.bind("<FocusOut>", off)
        off()
        self._hint_text = hint

    def _yview(self, *args):
        self.editor.yview(*args)
        self.lines.redraw()

    def _bind_keys(self):
        r = self.root
        r.bind("<F5>", lambda e: self.run())
        r.bind("<Shift-F5>", lambda e: self.stop())
        r.bind("<F7>", lambda e: self.check())
        r.bind("<Control-s>", lambda e: self.save())
        r.bind("<Control-S>", lambda e: self.save_as())
        r.bind("<Control-o>", lambda e: self.open_file())
        r.bind("<Control-n>", lambda e: self.new_file())
        r.bind("<Control-f>", lambda e: self.find())
        r.bind("<Control-slash>", lambda e: self.toggle_comment())
        r.bind("<Control-plus>", lambda e: self.zoom(1))
        r.bind("<Control-equal>", lambda e: self.zoom(1))
        r.bind("<Control-minus>", lambda e: self.zoom(-1))
        ed = self.editor
        ed.bind("<<Modified>>", self._modified)
        ed.bind("<KeyRelease>", self._moved)
        ed.bind("<ButtonRelease-1>", self._moved)
        ed.bind("<Return>", self._newline)
        ed.bind("<Tab>", lambda e: (ed.insert("insert", "    "), "break")[1])
        ed.bind("<Configure>", lambda e: self.lines.redraw())

    # ------------------------------------------------------------ editing
    def _modified(self, e=None):
        if self.editor.edit_modified():
            self.dirty = True
            self._title()
            self.editor.edit_modified(False)
            if self.highlight_job:
                self.root.after_cancel(self.highlight_job)
            self.highlight_job = self.root.after(120, self.highlight)

    def _moved(self, e=None):
        line, col = self.editor.index("insert").split(".")
        self.pos.configure(text=f"Ln {line}, Col {int(col) + 1}")
        self.lines.redraw()

    def _newline(self, e):
        ed = self.editor
        line = ed.get("insert linestart", "insert")
        indent = re.match(r"[ \t]*", line).group(0)
        low = line.strip().lower()
        opens = (low.startswith(("if ", "repeat", "while ", "until ", "for each", "count ", "make task", "to ", "try",
                                 "make model", "make kind", "otherwise", "else", "every ", "after ", "when ", "check ",
                                 "forever", "is ", "unless ", "if it fails", "define ", "function ", "task "))
                 and not re.search(r"\bthen\s+\S", low) and not re.search(r"\bdo\s+\w+\s*$", low))
        if low.startswith(("when ", "every ", "after ")) and re.search(r"\b(do|doing|run)\s+\w+\s*$", low):
            opens = False
        if low.startswith("if ") and not low.endswith("then") and " then " in low:
            opens = False
        ed.insert("insert", "\n" + indent + ("    " if opens else ""))
        ed.see("insert")
        return "break"

    def insert_snippet(self, code):
        self.editor.insert("insert", code)
        self.highlight()

    def toggle_comment(self):
        ed = self.editor
        try:
            first = int(ed.index("sel.first").split(".")[0])
            last = int(ed.index("sel.last").split(".")[0])
        except tk.TclError:
            first = last = int(ed.index("insert").split(".")[0])
        lines = [ed.get(f"{i}.0", f"{i}.end") for i in range(first, last + 1)]
        uncomment = all(l.lstrip().startswith("#") or not l.strip() for l in lines)
        for i, l in zip(range(first, last + 1), lines):
            if uncomment:
                new = re.sub(r"^(\s*)# ?", r"\1", l, count=1)
            else:
                new = "# " + l if l.strip() else l
            ed.delete(f"{i}.0", f"{i}.end")
            ed.insert(f"{i}.0", new)
        self.highlight()
        return "break"

    def zoom(self, d):
        family, size = self.mono(), self.editor.cget("font").split()[-1] if isinstance(self.editor.cget("font"), str) else 12
        try:
            size = int(size)
        except ValueError:
            size = 12
        size = max(8, min(32, size + d))
        self.editor.configure(font=(self.mono(), size))
        self.editor.tag_configure("comment", font=(self.mono(), size, "italic"))

    def highlight(self):
        self.highlight_job = None
        ed = self.editor
        for t in ("kw", "str", "num", "comment", "builtin", "shape", "bool", "errline", "found"):
            ed.tag_remove(t, "1.0", "end")
        text = ed.get("1.0", "end-1c")
        builtins = BUILTIN_WORDS
        for lineno, line in enumerate(text.split("\n"), start=1):
            stripped = line.lstrip()
            low = stripped.lower()
            if low.startswith("#") or low.startswith("//") or low == "note" or low.startswith("note ") or low.startswith("note:"):
                ed.tag_add("comment", f"{lineno}.0", f"{lineno}.end")
                continue
            i = 0
            n = len(line)
            first_word = True
            while i < n:
                c = line[i]
                if c in "\"'":
                    j = i + 1
                    while j < n and line[j] != c:
                        j += 2 if line[j] == "\\" else 1
                    ed.tag_add("str", f"{lineno}.{i}", f"{lineno}.{min(j + 1, n)}")
                    i = j + 1
                    first_word = False
                    continue
                if c == "#":
                    ed.tag_add("comment", f"{lineno}.{i}", f"{lineno}.end")
                    break
                if c.isdigit():
                    j = i
                    while j < n and (line[j].isdigit() or line[j] == "."):
                        j += 1
                    ed.tag_add("num", f"{lineno}.{i}", f"{lineno}.{j}")
                    i = j
                    continue
                if c.isalpha() or c == "_":
                    j = i
                    while j < n and (line[j].isalnum() or line[j] == "_"):
                        j += 1
                    word = line[i:j].lower()
                    tag = None
                    if word in VALUES:
                        tag = "bool"
                    elif word in KEYWORD_SET and (first_word or word not in builtins):
                        tag = "kw"
                    elif word in SHAPE_SET:
                        tag = "shape"
                    elif word in builtins and j < n and (line[j] == "(" or line[j:j + 3] == " of"):
                        tag = "builtin"
                    elif word in builtins and word in ("random", "length", "sqrt", "uppercase", "lowercase"):
                        tag = "builtin"
                    if tag:
                        ed.tag_add(tag, f"{lineno}.{i}", f"{lineno}.{j}")
                    first_word = False
                    i = j
                    continue
                i += 1
        self.lines.redraw()

    # ------------------------------------------------------------ files
    def _title(self):
        name = os.path.basename(self.path) if self.path else "untitled.mw"
        self.root.title(f"{'● ' if self.dirty else ''}{name} - Memowrite Studio")

    def confirm_discard(self):
        if not self.dirty:
            return True
        answer = messagebox.askyesnocancel("Memowrite Studio", "Save your changes first?")
        if answer is None:
            return False
        if answer:
            return self.save()
        return True

    def new_file(self):
        if not self.confirm_discard():
            return
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", "# My new Memowrite program\n\nsay \"Hello!\"\n")
        self.path = None
        self.dirty = False
        self.highlight()
        self._title()

    def open_file(self):
        if not self.confirm_discard():
            return
        p = filedialog.askopenfilename(filetypes=[("Memowrite programs", "*.mw"), ("All files", "*.*")])
        if p:
            self.open_path(p, ask=False)

    def open_path(self, p, ask=True):
        if ask and not self.confirm_discard():
            return
        with open(p, encoding="utf-8-sig") as fh:
            text = fh.read()
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.editor.edit_reset()
        ex_dir = os.path.join(HERE, "examples")
        # examples are templates: running or saving them never changes the originals
        self.path = None if os.path.dirname(os.path.abspath(p)) == os.path.abspath(ex_dir) else p
        self.example_source = p
        self.dirty = False
        self.highlight()
        self._title()
        self.status.configure(text=f"Opened {os.path.basename(p)}")

    def save(self):
        if not self.path:
            return self.save_as()
        try:
            with open(self.path, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(self.editor.get("1.0", "end-1c"))
        except OSError as e:
            messagebox.showerror("Memowrite Studio", f"I couldn't save the file:\n{e}")
            return False
        self.dirty = False
        self._title()
        self.status.configure(text=f"Saved {os.path.basename(self.path)}")
        return True

    def save_as(self):
        start = os.path.join(os.path.expanduser("~"), "Documents", "Memowrite")
        os.makedirs(start, exist_ok=True)
        p = filedialog.asksaveasfilename(defaultextension=".mw", initialdir=start,
                                         filetypes=[("Memowrite programs", "*.mw")])
        if not p:
            return False
        self.path = p
        return self.save()

    def open_help(self):
        doc = os.path.join(HERE, "Examples.md")
        if os.path.exists(doc):
            if os.name == "nt":
                os.startfile(doc)  # noqa
            else:
                subprocess.Popen(["xdg-open", doc])

    # ------------------------------------------------------------ running
    def _program_path(self):
        if self.path:
            if self.dirty:
                self.save()
            return self.path
        folder = os.path.join(os.path.expanduser("~"), "Documents", "Memowrite")
        os.makedirs(folder, exist_ok=True)
        base = os.path.splitext(os.path.basename(getattr(self, "example_source", "") or "untitled.mw"))[0]
        p = os.path.join(folder, base + ".mw")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(self.editor.get("1.0", "end-1c"))
        return p

    def run(self):
        self.stop(quiet=True)
        path = self._program_path()
        self.clear_output()
        self.write_out(f"▶ Running {os.path.basename(path)}\n", "info")
        env = dict(os.environ)
        env["MEMOWRITE_STUDIO"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONPATH"] = HERE + os.pathsep + env.get("PYTHONPATH", "")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self.proc = subprocess.Popen([python_console_exe(), "-m", "memowrite", path], cwd=os.path.dirname(path),
                                         stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                         env=env, creationflags=flags)
        except OSError as e:
            self.write_out(f"I couldn't start the program: {e}\n", "err")
            return
        self.status.configure(text="Running...")
        self.run_btn.configure(text="⟳  Restart (F5)")
        for stream, tag in ((self.proc.stdout, None), (self.proc.stderr, "err")):
            threading.Thread(target=self._reader, args=(stream, tag, self.proc), daemon=True).start()
        threading.Thread(target=self._waiter, args=(self.proc,), daemon=True).start()
        self.input.focus_set()

    def _reader(self, stream, tag, proc):
        while True:
            data = stream.read1(4096) if hasattr(stream, "read1") else stream.read(1)
            if not data:
                break
            self.out_queue.put((data.decode("utf-8", errors="replace"), tag, proc))

    def _waiter(self, proc):
        code = proc.wait()
        self.out_queue.put((None, code, proc))

    def _poll_output(self):
        try:
            while True:
                text, tag, proc = self.out_queue.get_nowait()
                if text is None:
                    if proc is self.proc:
                        self.proc = None
                        self.run_btn.configure(text="▶  Run  (F5)")
                        if tag == 0:
                            self.write_out("\n✓ Finished\n", "ok")
                            self.status.configure(text="Finished")
                        elif tag in (1, 2):
                            self.status.configure(text="Stopped with a problem - click the red line to jump to it")
                        else:
                            self.status.configure(text="Stopped")
                    continue
                self.write_ansi(text, tag)
        except queue.Empty:
            pass
        self.root.after(30, self._poll_output)

    def write_ansi(self, text, base_tag):
        parts = re.split(r"(\x1b\[[0-9;]*[A-Za-z])", text)
        for part in parts:
            if not part:
                continue
            m = re.fullmatch(r"\x1b\[([0-9;]*)([A-Za-z])", part)
            if m:
                code, letter = m.groups()
                if letter == "J":
                    self.clear_output()
                elif letter == "m":
                    num = int(code.split(";")[-1] or 0)
                    names = {31: "red", 91: "red", 32: "green", 92: "green", 33: "yellow", 93: "yellow", 34: "blue", 94: "blue",
                             35: "purple", 95: "purple", 36: "cyan", 96: "cyan", 37: "white", 97: "white", 90: "gray"}
                    self.current_color = names.get(num)
                continue
            tag = base_tag or (("c_" + self.current_color) if getattr(self, "current_color", None) else None)
            self.write_out(part, tag)

    def write_out(self, text, tag=None):
        self.output.configure(state="normal")
        self.output.insert("end", text, tag or ())
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")
        self.current_color = None

    def send_input(self, e=None):
        text = self.input.get()
        if text == getattr(self, "_hint_text", None):
            text = ""
        self.input.delete(0, "end")
        if self.proc is None or self.proc.stdin is None:
            self.write_out("(no program is waiting for an answer)\n", "info")
            return
        self.write_out(text + "\n", "c_cyan")
        try:
            self.proc.stdin.write((text + "\n").encode("utf-8"))
            self.proc.stdin.flush()
        except OSError:
            pass

    def stop(self, quiet=False):
        if self.proc is not None:
            try:
                self.proc.kill()
            except OSError:
                pass
            self.proc = None
            if not quiet:
                self.write_out("\n■ Stopped\n", "info")
            self.run_btn.configure(text="▶  Run  (F5)")

    def check(self):
        from .parser import Parser
        from .errors import MemoError
        self.editor.tag_remove("errline", "1.0", "end")
        try:
            Parser(self.editor.get("1.0", "end-1c"), "program").parse_program()
        except MemoError as e:
            self.clear_output()
            self.write_out(str(e) + "\n", "err")
            if e.line:
                self.goto_line(e.line, error=True)
            self.status.configure(text="Found a mistake")
            return
        self.clear_output()
        self.write_out("✓ No mistakes found. Press F5 to run it!\n", "ok")
        self.status.configure(text="No mistakes found")

    def _jump_to_error(self, e):
        idx = self.output.index(f"@{e.x},{e.y}")
        line_text = self.output.get(f"{idx} linestart", f"{idx} lineend")
        m = re.search(r"line (\d+)", line_text)
        if m:
            self.goto_line(int(m.group(1)), error=True)

    def goto_line(self, n, error=False):
        self.editor.tag_remove("errline", "1.0", "end")
        self.editor.mark_set("insert", f"{n}.0")
        self.editor.see(f"{n}.0")
        if error:
            self.editor.tag_add("errline", f"{n}.0", f"{n}.end+1c")
        self.editor.focus_set()
        self._moved()

    def find(self):
        win = tk.Toplevel(self.root, bg=C["panel"])
        win.title("Find")
        win.transient(self.root)
        win.geometry(f"+{self.root.winfo_rootx() + 300}+{self.root.winfo_rooty() + 80}")
        entry = tk.Entry(win, bg=C["panel2"], fg=C["fg"], insertbackground="#fff", relief="flat", font=(self.mono(), 11), width=30)
        entry.pack(side="left", padx=10, pady=10, ipady=4)
        entry.focus_set()

        def go(e=None):
            self.editor.tag_remove("found", "1.0", "end")
            word = entry.get()
            if not word:
                return
            start = "1.0"
            first = None
            while True:
                pos = self.editor.search(word, start, nocase=True, stopindex="end")
                if not pos:
                    break
                end = f"{pos}+{len(word)}c"
                self.editor.tag_add("found", pos, end)
                first = first or pos
                start = end
            if first:
                self.editor.see(first)
        entry.bind("<Return>", go)
        entry.bind("<Escape>", lambda e: win.destroy())
        tk.Button(win, text="Find", command=go, bg=C["accent"], fg="#fff", relief="flat", padx=10).pack(side="left", padx=(0, 10))

    def quit(self):
        if not self.confirm_discard():
            return
        self.stop(quiet=True)
        self.root.destroy()


def _builtin_words():
    from .interpreter import Interpreter
    try:
        return set(Interpreter().builtins)
    except Exception:
        return set()


KEYWORD_SET = set(KEYWORDS)
SHAPE_SET = set(SHAPES_WORDS)
BUILTIN_WORDS = set()

WELCOME = '''# Welcome to Memowrite Studio!
# Memowrite is a programming language written in plain English words.
# Press F5 to run this program. Open "Examples" above for lots more.

say "Hello! What's your name?"
ask "Type your name below and press Enter:" into name
say "Nice to meet you, {name}!"

repeat 3 times
    say "Memowrite is fun!"
end

recall "visits" into visits or 0
add 1 to visits
remember "visits" as visits
say "You have run this program {visits} time(s). I saved that in File.Memory."
'''


def main(args=None):
    global BUILTIN_WORDS
    args = list(args or [])
    BUILTIN_WORDS = _builtin_words()
    root = tk.Tk()
    Studio(root, args[0] if args else None)
    root.mainloop()


if __name__ == "__main__":
    main(sys.argv[1:])
