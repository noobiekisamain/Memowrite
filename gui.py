"""Windows, buttons and other app parts for Memowrite (built on Tk, which ships with Windows Python).

    make window app titled "My App" sized 400 by 300
    add label hello to app saying "Hello!"
    add button go to app saying "Click me" doing clicked
    show app
"""

import os
import sys
import time

from ..errors import MemoError, StopProgram
from ..values import Task, Builtin, to_text, to_number, truthy, is_number, tidy_number, type_name
from . import colors

LIGHT = {"bg": "#f6f7fb", "fg": "#1d1f2b", "muted": "#6b7085", "field": "#ffffff", "border": "#c9cdd9",
         "accent": "#3b5bdb", "accent_fg": "#ffffff", "accent_hover": "#2f4ac0", "panel": "#eceef5", "select": "#d0d9ff"}
DARK = {"bg": "#1c1d24", "fg": "#e9e9f0", "muted": "#9a9db0", "field": "#2a2c36", "border": "#3d4050",
        "accent": "#5c7cfa", "accent_fg": "#ffffff", "accent_hover": "#4c6ef5", "panel": "#24262f", "select": "#34406b"}

FONT = "Segoe UI" if os.name == "nt" else "DejaVu Sans"

KEY_NAMES = {"return": "enter", "kp_enter": "enter", "escape": "escape", "space": "space", "backspace": "backspace",
             "tab": "tab", "delete": "delete", "up": "up", "down": "down", "left": "left", "right": "right",
             "shift_l": "shift", "shift_r": "shift", "control_l": "control", "control_r": "control",
             "alt_l": "alt", "alt_r": "alt", "prior": "pageup", "next": "pagedown", "home": "home", "end": "end"}


def friendly_key(keysym):
    k = (keysym or "").lower()
    return KEY_NAMES.get(k, k)


def wanted_key(name):
    k = to_text(name).strip().lower()
    aliases = {"return": "enter", "esc": "escape", "spacebar": "space", "arrow up": "up", "arrow down": "down",
               "arrow left": "left", "arrow right": "right", "up arrow": "up", "down arrow": "down",
               "left arrow": "left", "right arrow": "right", "ctrl": "control"}
    return aliases.get(k, k)


class Widget:
    TYPE_NAME = "widget"

    def __init__(self, gui, kind, name, tk_widget, var=None, holder=None):
        self.gui = gui
        self.widget_kind = kind
        self.name = name
        self.tk = tk_widget
        self.var = var
        self.holder = holder or tk_widget   # what is packed/placed (may be a wrapper frame)
        self.items = []
        self.extra = {}
        self.pack_info = None
        self.place_info = None
        self.canvas = None
        self.radio_buttons = []
        self.data = {}

    def __repr__(self):
        return f"{self.widget_kind} {self.name or ''}".strip()

    def canvas_object(self):
        return self.canvas

    # ---- value
    def get_value(self):
        k = self.widget_kind
        if k in ("input", "password", "spinner", "dropdown", "radio", "colorpicker"):
            v = self.var.get()
            if k == "spinner":
                try:
                    return tidy_number(float(v))
                except ValueError:
                    return 0
            return v
        if k == "textbox":
            return self.tk.get("1.0", "end-1c")
        if k == "checkbox":
            return bool(self.var.get())
        if k in ("slider", "progress"):
            return tidy_number(round(float(self.var.get()), 6))
        if k == "listbox":
            sel = self.tk.curselection()
            return self.tk.get(sel[0]) if sel else None
        if k == "table":
            sel = self.tk.selection()
            if not sel:
                return None
            return [_parse_cell(v) for v in self.tk.item(sel[0], "values")]
        if k == "tabs":
            try:
                return self.tk.tab(self.tk.select(), "text")
            except Exception:
                return None
        if k in ("label", "heading", "button", "link"):
            return self.tk.cget("text")
        if k == "canvas":
            return self.canvas
        return None

    def set_value(self, value):
        k = self.widget_kind
        if k in ("input", "password", "spinner", "dropdown", "radio", "colorpicker"):
            if getattr(self.tk, "_memo_hint", False):
                self.tk._memo_hint = False
                self.tk.configure(fg=self.extra.get("theme", LIGHT)["fg"])
            self.var.set(to_text(value))
            if k == "colorpicker":
                self._update_swatch()
        elif k == "textbox":
            state = self.tk.cget("state")
            self.tk.configure(state="normal")
            self.tk.delete("1.0", "end")
            self.tk.insert("1.0", to_text(value))
            self.tk.configure(state=state)
        elif k == "checkbox":
            self.var.set(1 if truthy(value) else 0)
        elif k in ("slider", "progress"):
            self.var.set(to_number(value))
        elif k == "listbox":
            for i, item in enumerate(self.tk.get(0, "end")):
                if item == to_text(value):
                    self.tk.selection_clear(0, "end")
                    self.tk.selection_set(i)
                    self.tk.see(i)
        elif k in ("label", "heading", "button", "link"):
            self.tk.configure(text=to_text(value))
        elif k == "image":
            self._set_image(value)
        else:
            raise KeyError("text")

    def _set_image(self, path):
        import tkinter as tk
        p = self.gui.it.path(path)
        if not os.path.exists(p):
            raise MemoError(f"I can't find the picture {os.path.basename(p)}")
        photo = tk.PhotoImage(file=p)
        self.extra["photo"] = photo
        self.tk.configure(image=photo)

    def _update_swatch(self):
        try:
            c = colors.normalize(self.var.get()) or "#ffffff"
            self.tk.configure(bg=c, activebackground=c, text=c)
        except Exception:
            pass

    # ---- list-like widgets
    def items_list(self):
        if self.widget_kind == "listbox":
            return list(self.tk.get(0, "end"))
        if self.widget_kind == "table":
            return [[_parse_cell(v) for v in self.tk.item(i, "values")] for i in self.tk.get_children()]
        return list(self.items)

    def set_items(self, items):
        items = list(items) if isinstance(items, list) else [items]
        k = self.widget_kind
        if k == "listbox":
            self.tk.delete(0, "end")
            for it in items:
                self.tk.insert("end", to_text(it))
        elif k == "dropdown":
            self.items = [to_text(i) for i in items]
            self.tk.configure(values=self.items)
            if self.items and self.var.get() not in self.items:
                self.var.set(self.items[0])
        elif k == "table":
            self.clear()
            for row in items:
                self.add_item(row)
        else:
            raise KeyError("items")

    def add_item(self, value):
        k = self.widget_kind
        if k == "listbox":
            self.tk.insert("end", to_text(value))
            self.tk.see("end")
        elif k == "dropdown":
            self.items.append(to_text(value))
            self.tk.configure(values=self.items)
            if len(self.items) == 1:
                self.var.set(self.items[0])
        elif k == "table":
            if isinstance(value, dict):
                cols = self.extra.get("columns", [])
                row = [value.get(c, value.get(c.lower(), "")) for c in cols]
            elif isinstance(value, list):
                row = value
            else:
                row = [value]
            self.tk.insert("", "end", values=[to_text(v) for v in row])
        elif k == "textbox":
            self.tk.insert("end", ("\n" if self.tk.get("1.0", "end-1c") else "") + to_text(value))
            self.tk.see("end")
        elif k in ("slider", "progress", "spinner"):
            self.set_value(to_number(self.get_value()) + to_number(value))
        else:
            raise MemoError(f"I can't add items to a {k}")

    def remove_item(self, value):
        k = self.widget_kind
        if k == "listbox":
            for i, item in enumerate(self.tk.get(0, "end")):
                if item.lower() == to_text(value).lower():
                    self.tk.delete(i)
                    return
        elif k == "dropdown":
            self.items = [i for i in self.items if i.lower() != to_text(value).lower()]
            self.tk.configure(values=self.items)
        elif k == "table":
            for iid in self.tk.get_children():
                vals = self.tk.item(iid, "values")
                if vals and (to_text(vals[0]).lower() == to_text(value if not isinstance(value, list) else value[0]).lower()):
                    self.tk.delete(iid)
                    return
        else:
            raise MemoError(f"I can't remove items from a {k}")

    def remove_selected(self):
        if self.widget_kind == "listbox":
            for i in reversed(self.tk.curselection()):
                self.tk.delete(i)
        elif self.widget_kind == "table":
            for iid in self.tk.selection():
                self.tk.delete(iid)

    def clear(self):
        k = self.widget_kind
        if k == "listbox":
            self.tk.delete(0, "end")
        elif k == "table":
            for iid in self.tk.get_children():
                self.tk.delete(iid)
        elif k in ("input", "password", "textbox"):
            self.set_value("")
        elif k == "dropdown":
            self.items = []
            self.tk.configure(values=[])
            self.var.set("")
        elif k == "canvas" and self.canvas is not None:
            self.canvas.clear()
        elif k == "checkbox":
            self.var.set(0)

    def contains(self, value):
        return any(to_text(x).lower() == to_text(value).lower() for x in self.items_list())

    def length(self):
        if self.widget_kind in ("listbox", "table", "dropdown"):
            return len(self.items_list())
        v = self.get_value()
        return len(to_text(v)) if v is not None else 0

    def is_empty(self):
        v = self.get_value()
        if self.widget_kind in ("listbox", "table", "dropdown"):
            return len(self.items_list()) == 0
        return v is None or to_text(v).strip() == ""

    # ---- properties
    def get_prop(self, word):
        if word in ("text", "value", "saying", "answer", "selected", "choice", "checked", "ticked", "contents"):
            return self.get_value()
        if word in ("items", "options", "rows"):
            return self.items_list()
        if word in ("number",):
            v = self.get_value()
            try:
                return tidy_number(float(to_text(v)))
            except ValueError:
                raise MemoError(f"The {self.widget_kind} does not have a number in it ('{to_text(v)}')")
        if word in ("width",):
            return self.holder.winfo_width()
        if word in ("height",):
            return self.holder.winfo_height()
        if word in ("x",):
            return self.holder.winfo_x()
        if word in ("y",):
            return self.holder.winfo_y()
        if word in ("enabled",):
            try:
                return str(self.tk.cget("state")) != "disabled"
            except Exception:
                return True
        if word in ("visible",):
            return bool(self.holder.winfo_ismapped())
        if word in ("color", "colour", "foreground"):
            return self.tk.cget("fg") if "fg" in self.tk.keys() else None
        if word in ("background",):
            return self.tk.cget("bg") if "bg" in self.tk.keys() else None
        if word in ("count", "length", "size"):
            return self.length()
        if word in ("kind", "type"):
            return self.widget_kind
        if word == "name":
            return self.name
        if word in ("selected_index", "index"):
            if self.widget_kind == "listbox":
                sel = self.tk.curselection()
                return sel[0] + 1 if sel else 0
            if self.widget_kind == "dropdown":
                v = self.var.get()
                return self.items.index(v) + 1 if v in self.items else 0
        if self.canvas is not None:
            return self.canvas.get_prop(word)
        if word in self.data:
            return self.data[word]
        raise KeyError(word)

    def set_prop(self, word, value):
        if word in ("text", "value", "saying", "selected", "choice", "checked", "ticked", "contents"):
            self.set_value(value)
        elif word in ("items", "options", "rows"):
            self.set_items(value)
        elif word in ("color", "colour", "foreground", "textcolor"):
            c = colors.normalize(value)
            if "fg" in self.tk.keys():
                self.tk.configure(fg=c)
                if self.widget_kind in ("label", "heading", "checkbox"):
                    pass
        elif word in ("background", "fill"):
            c = colors.normalize(value)
            if self.canvas is not None:
                self.canvas.fill(c)
            elif "bg" in self.tk.keys():
                self.tk.configure(bg=c)
                if self.widget_kind == "button":
                    self.extra["bg"] = c
                    self.tk._memo_bg = c
                    self.tk.configure(activebackground=colors.darker(c, 0.15))
        elif word == "enabled":
            self.set_enabled(truthy(value))
        elif word == "visible":
            self.show() if truthy(value) else self.hide()
        elif word == "font":
            self.tk.configure(font=(to_text(value), 11))
        elif word in ("size", "fontsize", "font_size"):
            f = self.tk.cget("font")
            fam = FONT
            self.tk.configure(font=(fam, int(to_number(value))))
        elif word in ("width", "height", "x", "y"):
            info = self.holder.place_info()
            if info:
                kw = {word: int(to_number(value))}
                self.holder.place_configure(**kw)
            elif word in ("width", "height") and self.holder is not self.tk:
                self.holder.configure(**{word: int(to_number(value))})
            else:
                self.tk.configure(**{word: int(to_number(value) / 8) if word == "width" else int(to_number(value) / 20)})
        elif word in ("maximum", "max", "to"):
            self.tk.configure(to=to_number(value)) if self.widget_kind != "progress" else self.tk.configure(maximum=to_number(value))
        elif word in ("minimum", "min", "from"):
            self.tk.configure(from_=to_number(value))
        elif word in ("image", "picture"):
            self._set_image(value)
        elif word in ("title",) and self.widget_kind == "tab":
            parent = self.extra.get("notebook")
            if parent is not None:
                parent.tab(self.tk, text=to_text(value))
        else:
            self.data[word] = value

    # ---- actions
    def show(self):
        if self.place_info:
            self.holder.place(**self.place_info)
        elif self.pack_info:
            self.holder.pack(**self.pack_info)

    def hide(self):
        if self.holder.winfo_manager() == "place":
            self.holder.place_forget()
        else:
            self.holder.pack_forget()

    def delete(self):
        self.holder.destroy()

    def focus(self):
        self.tk.focus_set()

    def set_enabled(self, on):
        try:
            if self.widget_kind in ("dropdown",):
                self.tk.configure(state="readonly" if on else "disabled")
            else:
                self.tk.configure(state="normal" if on else "disabled")
        except Exception:
            pass

    def recolor(self, c):
        self.set_prop("background", c)


def _parse_cell(v):
    try:
        f = float(v)
        return tidy_number(f)
    except (TypeError, ValueError):
        return v


class AppWindow:
    TYPE_NAME = "window"

    def __init__(self, gui, name, tk_win, theme):
        self.gui = gui
        self.name = name
        self.tk = tk_win
        self.theme = theme
        self.body = None
        self.closed = False
        self.data = {}

    def __repr__(self):
        return f"window {self.name}"

    def container(self):
        return self.body

    def show(self):
        self.tk.deiconify()
        self.tk.lift()
        self.gui.pump()

    def hide(self):
        self.tk.withdraw()

    def close(self):
        self.gui.close_window(self)

    def set_enabled(self, on):
        pass

    def get_prop(self, word):
        if word == "title":
            return self.tk.title()
        if word == "width":
            return self.tk.winfo_width()
        if word == "height":
            return self.tk.winfo_height()
        if word == "x":
            return self.tk.winfo_x()
        if word == "y":
            return self.tk.winfo_y()
        if word in ("background", "color", "colour"):
            return self.body.cget("bg")
        if word == "open":
            return not self.closed
        if word in self.data:
            return self.data[word]
        raise KeyError(word)

    def set_prop(self, word, value):
        if word == "title":
            self.tk.title(to_text(value))
        elif word in ("background", "color", "colour"):
            c = colors.normalize(value)
            self.tk.configure(bg=c)
            self.body.configure(bg=c)
            self.theme = dict(self.theme)
            self.theme["bg"] = c
            for child in self.body.winfo_children():
                try:
                    if child.winfo_class() in ("Label", "Frame", "Checkbutton", "Radiobutton"):
                        child.configure(bg=c)
                except Exception:
                    pass
        elif word in ("width", "height"):
            w = self.tk.winfo_width() if word == "height" else int(to_number(value))
            h = self.tk.winfo_height() if word == "width" else int(to_number(value))
            self.tk.geometry(f"{w}x{h}")
        elif word == "fullscreen":
            self.tk.attributes("-fullscreen", truthy(value))
        elif word in ("on_top", "topmost"):
            self.tk.attributes("-topmost", truthy(value))
        elif word in ("opacity", "transparency"):
            v = to_number(value)
            self.tk.attributes("-alpha", v / 100 if v > 1 else v)
        else:
            self.data[word] = value


class GUI:
    def __init__(self, it):
        try:
            import tkinter as tk
            from tkinter import ttk
        except ImportError:
            raise MemoError("Windows and drawing need Tk, which is missing from this Memowrite install")
        self.tk = tk
        self.ttk = ttk
        self.it = it
        self.root = None
        self.root_used = False
        self.windows = []
        self.timers = []
        self.keys_down = set()
        self.mouse = (0, 0)
        self.had_windows = False
        self.quitting = False
        self.style_ready = False

    # ------------------------------------------------------------ root & loop
    def root_or_hidden(self):
        if self.root is None:
            self.root = self.tk.Tk()
            self.root.withdraw()
            self._set_icon(self.root)
            self._bind_global_keys(self.root)
        return self.root

    def _set_icon(self, win, path=None):
        try:
            if path:
                if path.lower().endswith(".ico") and os.name == "nt":
                    win.iconbitmap(path)
                else:
                    win.iconphoto(False, self.tk.PhotoImage(file=path))
                return
            here = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ico = os.path.join(here, "branding", "memowrite.ico")
            png = os.path.join(here, "branding", "memowrite-64.png")
            if os.name == "nt" and os.path.exists(ico):
                win.iconbitmap(default=ico)
            elif os.path.exists(png):
                self._icon_img = self.tk.PhotoImage(file=png)
                win.iconphoto(True, self._icon_img)
        except Exception:
            pass

    def _bind_global_keys(self, root):
        def down(e):
            self.keys_down.add(friendly_key(e.keysym))

        def up(e):
            self.keys_down.discard(friendly_key(e.keysym))
        root.bind_all("<KeyPress>", down, add="+")
        root.bind_all("<KeyRelease>", up, add="+")

    def has_windows(self):
        return any(not w.closed for w in self.windows)

    def pump(self):
        if self.root is None:
            return
        try:
            self.root.update()
        except self.tk.TclError:
            raise StopProgram()
        if self.had_windows and not self.has_windows():
            raise StopProgram()

    def sleep(self, secs):
        end = time.time() + max(0, secs)
        while True:
            self.pump()
            left = end - time.time()
            if left <= 0:
                break
            time.sleep(min(0.01, left))

    def mainloop(self):
        if self.root is None or not self.has_windows():
            return
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass

    def quit(self):
        self.quitting = True
        for t in self.timers:
            try:
                self.root.after_cancel(t[0])
            except Exception:
                pass
        try:
            if self.root is not None:
                self.root.destroy()
        except Exception:
            pass
        self.root = None
        for w in self.windows:
            w.closed = True

    def close_window(self, win):
        if win.closed:
            return
        win.closed = True
        cb = win.data.get("\x00onclose")
        if win.tk is self.root:
            if any(not w.closed for w in self.windows):
                win.tk.withdraw()
            else:
                self.quit()
        else:
            try:
                win.tk.destroy()
            except Exception:
                pass
            if not self.has_windows():
                self.quit()

    # ------------------------------------------------------------ calling tasks safely
    def run_task(self, fn, args=()):
        if fn is None:
            return
        if isinstance(fn, Task):
            args = list(args)[:len(fn.params)]
        try:
            self.it.call(fn, list(args))
        except StopProgram:
            self.quit()
        except MemoError as e:
            sys.stderr.write(str(e) + "\n")
            sys.stderr.flush()
            try:
                from tkinter import messagebox
                messagebox.showerror("Memowrite - something went wrong", str(e))
            except Exception:
                pass
        except Exception as e:
            from ..interpreter import friendly_python_error
            err = MemoError(friendly_python_error(e), self.it.line, self.it.file)
            sys.stderr.write(str(err) + "\n")

    def task_named(self, name):
        if name is None:
            return None
        fn = self.it.lookup(name)
        if not isinstance(fn, (Task, Builtin)):
            raise MemoError(f"'{name}' is not a task. Make it with: make task {name} ... end")
        return fn

    # ------------------------------------------------------------ windows
    def make_window(self, n):
        opts = n.opts
        ev = self.it.eval
        title = None
        for key in ("called", "title"):
            if key in opts:
                title = to_text(ev(opts[key]))
        theme = dict(DARK if opts.get("dark") else LIGHT)
        if "theme" in opts and to_text(ev(opts["theme"])).lower() == "dark":
            theme = dict(DARK)
        if self.root is None or self.root_used:
            win = self.tk.Tk() if self.root is None else self.tk.Toplevel(self.root)
            if self.root is None:
                self.root = win
                self._bind_global_keys(win)
        else:
            win = self.root
            win.deiconify()
        if win is self.root:
            self.root_used = True
            self._set_icon(win)
        self._setup_style(theme)
        w, h = 480, 360
        if "size" in opts:
            a, b = opts["size"]
            w = int(to_number(ev(a)))
            h = int(to_number(ev(b))) if b is not None else w
        win.title(title or n.name.title())
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        x, y = (sw - w) // 2 + 30 * len(self.windows), (sh - h) // 3 + 30 * len(self.windows)
        if "at" in opts:
            x, y = int(to_number(ev(opts["at"][0]))), int(to_number(ev(opts["at"][1])))
        win.geometry(f"{w}x{h}+{max(0, x)}+{max(0, y)}")
        if "color" in opts or "background" in opts:
            theme["bg"] = colors.normalize(ev(opts.get("color") or opts.get("background")))
        win.configure(bg=theme["bg"])
        if opts.get("fixed"):
            win.resizable(False, False)
        if opts.get("fullscreen"):
            win.attributes("-fullscreen", True)
        if "icon" in opts:
            self._set_icon(win, self.it.path(ev(opts["icon"])))
        body = self.tk.Frame(win, bg=theme["bg"])
        body.pack(fill="both", expand=True, padx=10, pady=10)
        app = AppWindow(self, n.name, win, theme)
        app.body = body
        win.protocol("WM_DELETE_WINDOW", lambda a=app: self._on_close(a))
        self.windows.append(app)
        self.had_windows = True
        self.it.assign(n.name, app)
        try:
            win.update()
        except Exception:
            pass
        return app

    def _on_close(self, app):
        cb = app.data.get("\x00onclose")
        if cb is not None:
            self.run_task(cb)
        self.close_window(app)

    def _setup_style(self, theme):
        style = self.ttk.Style(self.root)
        try:
            if "clam" in style.theme_names():
                style.theme_use("clam")
        except Exception:
            pass
        style.configure("TCombobox", fieldbackground=theme["field"], background=theme["field"], foreground=theme["fg"],
                        arrowcolor=theme["fg"], bordercolor=theme["border"], padding=4)
        style.configure("Memo.Horizontal.TProgressbar", troughcolor=theme["panel"], background=theme["accent"],
                        bordercolor=theme["border"], lightcolor=theme["accent"], darkcolor=theme["accent"], thickness=14)
        style.configure("Treeview", background=theme["field"], fieldbackground=theme["field"], foreground=theme["fg"],
                        rowheight=24, font=(FONT, 10), bordercolor=theme["border"])
        style.configure("Treeview.Heading", background=theme["panel"], foreground=theme["fg"], font=(FONT, 10, "bold"), relief="flat")
        style.map("Treeview", background=[("selected", theme["select"])], foreground=[("selected", theme["fg"])])
        style.configure("Memo.Horizontal.TScale", troughcolor=theme["panel"], background=theme["accent"],
                        bordercolor=theme["border"], lightcolor=theme["accent"], darkcolor=theme["accent"], gripcount=0)
        style.configure("TNotebook", background=theme["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", padding=(14, 6), font=(FONT, 10), background=theme["panel"], foreground=theme["fg"])
        style.map("TNotebook.Tab", background=[("selected", theme["field"])])

    def window_of(self, name_or_obj):
        obj = name_or_obj
        if isinstance(obj, str):
            obj = self.it.lookup(obj)
        if isinstance(obj, AppWindow):
            return obj
        if isinstance(obj, Widget):
            return obj.extra.get("window")
        return None

    def find_named(self, name):
        return None

    # ------------------------------------------------------------ widgets
    def parent_container(self, parent_name):
        parent = self.it.lookup(parent_name)
        if isinstance(parent, AppWindow):
            return parent.body, parent.theme, parent, "column"
        if isinstance(parent, Widget) and parent.widget_kind in ("panel", "row", "tab"):
            return parent.tk, parent.extra.get("theme", LIGHT), parent.extra.get("window"), parent.widget_kind
        if isinstance(parent, Widget) and parent.widget_kind == "tabs":
            return parent.tk, parent.extra.get("theme", LIGHT), parent.extra.get("window"), "tabs"
        raise MemoError(f"'{parent_name}' is not a window or panel, so I can't add things to it",
                        hint=f"Make it first with: make window {parent_name}")

    def add_widget(self, n):
        tk = self.tk
        ev = self.it.eval
        opts = n.opts
        container, theme, window, layout = self.parent_container(n.parent)
        kind = n.wkind
        text = to_text(ev(opts["saying"])) if "saying" in opts else None
        if text is None and "title" in opts:
            text = to_text(ev(opts["title"]))
        bg = theme["bg"] if layout != "row" or True else theme["bg"]
        try:
            bg = container.cget("bg")
        except Exception:
            bg = theme["bg"]
        fg = colors.normalize(ev(opts["color"])) if "color" in opts else theme["fg"]
        font_size = 10
        if opts.get("big"):
            font_size = 14
        if opts.get("small"):
            font_size = 8
        font = (to_text(ev(opts["font"])) if "font" in opts else FONT, font_size, "bold" if opts.get("bold") else "normal")
        var = None
        holder = None
        command_task = self.task_named(opts.get("doing")) if opts.get("doing") else None
        w = None

        if kind == "label":
            w = tk.Label(container, text=text or "", bg=bg, fg=fg, font=font, justify="left", anchor="w")
            if opts.get("wrap"):
                w.configure(wraplength=300)
        elif kind == "heading":
            w = tk.Label(container, text=text or "", bg=bg, fg=fg, font=(font[0], 16 if not opts.get("small") else 13, "bold"), anchor="w")
        elif kind == "button":
            bbg = colors.normalize(ev(opts["background"])) if "background" in opts else theme["accent"]
            bfg = colors.normalize(ev(opts["color"])) if "color" in opts else theme["accent_fg"]
            w = tk.Button(container, text=text or "Button", bg=bbg, fg=bfg, activebackground=colors.darker(bbg, 0.15),
                          activeforeground=bfg, relief="flat", bd=0, padx=14, pady=6, cursor="hand2",
                          font=(font[0], font_size, "bold"), highlightthickness=0)
            w.bind("<Enter>", lambda e, b=w: b.configure(bg=colors.darker(b._memo_bg, 0.1)) if getattr(b, "_memo_bg", None) else None)
            w.bind("<Leave>", lambda e, b=w: b.configure(bg=b._memo_bg) if getattr(b, "_memo_bg", None) else None)
            w._memo_bg = bbg
            if command_task is not None:
                # a task with one value gets the button's text, so many buttons can share one task
                w.configure(command=lambda f=command_task, b=w: self.run_task(f, [b.cget("text")]))
        elif kind in ("input", "password"):
            var = tk.StringVar(value=to_text(ev(opts["value"])) if "value" in opts else "")
            w = tk.Entry(container, textvariable=var, bg=theme["field"], fg=theme["fg"], insertbackground=theme["fg"],
                         relief="solid", bd=1, font=(font[0], 11), highlightthickness=1, highlightcolor=theme["accent"],
                         highlightbackground=theme["border"])
            if kind == "password":
                w.configure(show="•")
            if "placeholder" in opts or "hint" in opts:
                self._placeholder(w, var, to_text(ev(opts.get("placeholder") or opts.get("hint"))), theme)
            if text and kind == "input" and not var.get():
                # "saying" on an input works as a label in front of it
                holder = tk.Frame(container, bg=bg)
                tk.Label(holder, text=text, bg=bg, fg=theme["muted"], font=(font[0], 9)).pack(anchor="w")
                w.destroy()
                w = tk.Entry(holder, textvariable=var, bg=theme["field"], fg=theme["fg"], insertbackground=theme["fg"],
                             relief="solid", bd=1, font=(font[0], 11), highlightthickness=1,
                             highlightcolor=theme["accent"], highlightbackground=theme["border"],
                             show="•" if kind == "password" else "")
                w.pack(fill="x", ipady=3)
            if command_task is not None:
                w.bind("<Return>", lambda e, f=command_task: self.run_task(f))
        elif kind == "textbox":
            rows = int(to_number(ev(opts["rows"]))) if "rows" in opts else 6
            w = tk.Text(container, height=rows, width=40, bg=theme["field"], fg=theme["fg"], insertbackground=theme["fg"],
                        relief="solid", bd=1, font=(font[0], 11), wrap="word", highlightthickness=1,
                        highlightcolor=theme["accent"], highlightbackground=theme["border"], padx=6, pady=4, undo=True)
            if text:
                w.insert("1.0", text)
            if opts.get("readonly"):
                w.configure(state="disabled")
        elif kind == "checkbox":
            var = tk.IntVar(value=1 if ("value" in opts and truthy(ev(opts["value"]))) else 0)
            w = tk.Checkbutton(container, text=text or "", variable=var, bg=bg, fg=fg, selectcolor=theme["field"],
                               activebackground=bg, activeforeground=fg, font=font, anchor="w", cursor="hand2",
                               highlightthickness=0, bd=0)
            if command_task is not None:
                w.configure(command=lambda f=command_task: self.run_task(f, [bool(var.get())]))
        elif kind == "slider":
            lo, hi = (0, 100)
            if "from" in opts:
                lo, hi = to_number(ev(opts["from"][0])), to_number(ev(opts["from"][1]))
            var = tk.DoubleVar(value=to_number(ev(opts["value"])) if "value" in opts else lo)
            step = to_number(ev(opts["step"])) if "step" in opts else 1
            holder = tk.Frame(container, bg=bg)
            top = tk.Frame(holder, bg=bg)
            top.pack(fill="x")
            if text:
                tk.Label(top, text=text, bg=bg, fg=fg, font=(font[0], 9)).pack(side="left")
            shown = tk.Label(top, text=to_text(tidy_number(var.get())), bg=bg, fg=theme["muted"], font=(font[0], 9, "bold"))
            shown.pack(side="right")

            def moved(v, var=var, step=step, lo=lo, shown=shown, f=command_task):
                value = tidy_number(round((float(v) - lo) / step) * step + lo) if step else tidy_number(float(v))
                if abs(var.get() - value) > 1e-9:
                    var.set(value)
                shown.configure(text=to_text(value))
                if f is not None:
                    self.run_task(f, [value])
            w = self.ttk.Scale(holder, from_=lo, to=hi, orient="horizontal", variable=var, length=240,
                               style="Memo.Horizontal.TScale", command=moved)
            w.pack(fill="x")
            var.trace_add("write", lambda *a, var=var, shown=shown: shown.configure(text=to_text(tidy_number(round(var.get(), 6)))))
        elif kind == "dropdown":
            var = tk.StringVar()
            items = ev(opts["with"]) if "with" in opts else (ev(opts["options"]) if "options" in opts else [])
            items = [to_text(i) for i in (items if isinstance(items, list) else [items])]
            w = self.ttk.Combobox(container, textvariable=var, values=items, state="readonly", font=(font[0], 10))
            if items:
                var.set(items[0])
            if command_task is not None:
                w.bind("<<ComboboxSelected>>", lambda e, f=command_task: self.run_task(f, [var.get()]))
        elif kind == "listbox":
            rows = int(to_number(ev(opts["rows"]))) if "rows" in opts else 6
            holder = tk.Frame(container, bg=bg)
            w = tk.Listbox(holder, height=rows, bg=theme["field"], fg=theme["fg"], selectbackground=theme["select"],
                           selectforeground=theme["fg"], relief="solid", bd=1, font=(font[0], 11), activestyle="none",
                           highlightthickness=0, exportselection=False)
            sb = tk.Scrollbar(holder, command=w.yview)
            w.configure(yscrollcommand=sb.set)
            w.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            if "with" in opts:
                for item in (ev(opts["with"]) or []):
                    w.insert("end", to_text(item))
            if command_task is not None:
                w.bind("<<ListboxSelect>>", lambda e, f=command_task, lb=w: self.run_task(f, [lb.get(lb.curselection()[0])] if lb.curselection() else []))
        elif kind == "table":
            cols = [to_text(ev(c)) for c in opts["columns"]] if "columns" in opts else []
            if not cols and "with" in opts:
                cols = [to_text(c) for c in ev(opts["with"])]
            if not cols:
                cols = ["Name", "Value"]
            holder = tk.Frame(container, bg=bg)
            w = self.ttk.Treeview(holder, columns=cols, show="headings", height=int(to_number(ev(opts["rows"]))) if "rows" in opts else 8)
            for c in cols:
                w.heading(c, text=c)
                w.column(c, width=110, anchor="w")
            sb = tk.Scrollbar(holder, command=w.yview)
            w.configure(yscrollcommand=sb.set)
            w.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            if command_task is not None:
                w.bind("<<TreeviewSelect>>", lambda e, f=command_task: self.run_task(f))
        elif kind == "canvas":
            from .graphics import Canvas
            cw, ch = 400, 300
            if "size" in opts:
                a, b = opts["size"]
                cw = to_number(ev(a))
                ch = to_number(ev(b)) if b is not None else cw
            cbg = colors.normalize(ev(opts["background"])) if "background" in opts else (colors.normalize(ev(opts["color"])) if "color" in opts else "#ffffff")
            canvas = Canvas(n.name or "canvas", cw, ch, cbg)
            w = tk.Canvas(container, width=cw, height=ch, highlightthickness=0, bd=0)
            canvas.attach(w)
            self._bind_canvas_mouse(w, canvas)
            self.it.current_canvas = canvas
        elif kind == "image":
            w = tk.Label(container, bg=bg)
            wid = Widget(self, kind, n.name, w)
            if "with" in opts or "image" in opts or "saying" in opts:
                wid._set_image(ev(opts.get("with") or opts.get("image") or opts.get("saying")))
            return self._finish(wid, container, opts, layout, n, window, theme)
        elif kind == "progress":
            var = tk.DoubleVar(value=to_number(ev(opts["value"])) if "value" in opts else 0)
            maximum = 100
            if "from" in opts:
                maximum = to_number(ev(opts["from"][1]))
            w = self.ttk.Progressbar(container, variable=var, maximum=maximum, length=240, style="Memo.Horizontal.TProgressbar")
        elif kind == "spinner":
            lo, hi = (0, 100)
            if "from" in opts:
                lo, hi = to_number(ev(opts["from"][0])), to_number(ev(opts["from"][1]))
            var = tk.StringVar(value=to_text(ev(opts["value"])) if "value" in opts else to_text(lo))
            step = to_number(ev(opts["step"])) if "step" in opts else 1
            w = tk.Spinbox(container, from_=lo, to=hi, increment=step, textvariable=var, width=8, bg=theme["field"],
                           fg=theme["fg"], relief="solid", bd=1, font=(font[0], 11), buttonbackground=theme["panel"])
            if command_task is not None:
                w.configure(command=lambda f=command_task: self.run_task(f, [tidy_number(float(var.get() or 0))]))
        elif kind in ("panel", "row"):
            pbg = colors.normalize(ev(opts["background"])) if "background" in opts else (theme["panel"] if opts.get("filling") else bg)
            if text:
                w = tk.LabelFrame(container, text=text, bg=pbg, fg=theme["fg"], font=(font[0], 10, "bold"), bd=1,
                                  relief="groove", padx=8, pady=6)
            else:
                w = tk.Frame(container, bg=pbg)
        elif kind == "tabs":
            w = self.ttk.Notebook(container)
        elif kind == "tab":
            if layout != "tabs":
                raise MemoError("A tab must be added to tabs. First: add tabs book to app")
            w = tk.Frame(container, bg=theme["bg"], padx=10, pady=10)
            container.add(w, text=text or (n.name or "Tab").title())
            wid = Widget(self, kind, n.name, w)
            wid.extra.update(theme=theme, window=window, notebook=container)
            if n.name:
                self.it.assign(n.name, wid)
            return wid
        elif kind == "separator":
            w = tk.Frame(container, height=1, bg=theme["border"])
            wid = Widget(self, kind, n.name, w)
            w.pack(fill="x", pady=8)
            wid.pack_info = {"fill": "x", "pady": 8}
            return wid
        elif kind == "space":
            size = to_number(ev(opts["size"][0])) if "size" in opts else 12
            w = tk.Frame(container, height=size, width=size, bg=bg)
        elif kind == "radio":
            var = tk.StringVar()
            items = ev(opts["with"]) if "with" in opts else ["Yes", "No"]
            w = tk.Frame(container, bg=bg)
            if text:
                tk.Label(w, text=text, bg=bg, fg=fg, font=font).pack(anchor="w")
            buttons = []
            for item in items:
                rb = tk.Radiobutton(w, text=to_text(item), value=to_text(item), variable=var, bg=bg, fg=fg,
                                    selectcolor=theme["field"], activebackground=bg, font=font, anchor="w", cursor="hand2")
                rb.pack(anchor="w", side="left" if opts.get("going") else "top")
                if command_task is not None:
                    rb.configure(command=lambda f=command_task: self.run_task(f, [var.get()]))
                buttons.append(rb)
            if items:
                var.set(to_text(items[0]))
        elif kind == "link":
            url = to_text(ev(opts["with"])) if "with" in opts else (text or "")
            w = tk.Label(container, text=text or url, bg=bg, fg=theme["accent"], cursor="hand2", font=(font[0], font_size, "underline"))
            import webbrowser
            w.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        elif kind == "colorpicker":
            var = tk.StringVar(value=colors.normalize(ev(opts["value"])) if "value" in opts else "#3b5bdb")
            w = tk.Button(container, text=var.get(), relief="flat", bd=0, padx=14, pady=6, cursor="hand2", fg="#ffffff")
            wid_holder = {}

            def pick(v=var, f=command_task):
                from tkinter import colorchooser
                got = colorchooser.askcolor(color=v.get(), title="Pick a color")
                if got and got[1]:
                    v.set(got[1])
                    wid_holder["w"]._update_swatch()
                    if f is not None:
                        self.run_task(f, [got[1]])
            w.configure(command=pick)
            wid = Widget(self, kind, n.name, w, var)
            wid_holder["w"] = wid
            wid._update_swatch()
            return self._finish(wid, container, opts, layout, n, window, theme)
        else:
            raise MemoError(f"I don't know how to add a {kind}")

        wid = Widget(self, kind, n.name, w, var, holder)
        if kind == "canvas":
            wid.canvas = canvas
            canvas.widget = wid
        if kind in ("panel", "row"):
            wid.extra["theme"] = theme
        if kind == "tabs":
            wid.extra["theme"] = theme
        if "tip" in opts:
            self._tooltip(w, to_text(ev(opts["tip"])), theme)
        return self._finish(wid, container, opts, layout, n, window, theme)

    def _finish(self, wid, container, opts, layout, n, window, theme):
        ev = self.it.eval
        wid.extra["window"] = window
        wid.extra.setdefault("theme", theme)
        holder = wid.holder
        if "at" in opts and layout != "tabs":
            x, y = to_number(ev(opts["at"][0])), to_number(ev(opts["at"][1]))
            info = {"x": int(x), "y": int(y)}
            if "size" in opts:
                a, b = opts["size"]
                info["width"] = int(to_number(ev(a)))
                if b is not None:
                    info["height"] = int(to_number(ev(b)))
            holder.place(**info)
            wid.place_info = info
        else:
            if "size" in opts and wid.widget_kind not in ("canvas", "space"):
                a, b = opts["size"]
                frame = self.tk.Frame(container, width=int(to_number(ev(a))),
                                      height=int(to_number(ev(b))) if b is not None else 34, bg=container.cget("bg") if hasattr(container, "cget") else None)
                frame.pack_propagate(False)
                holder.pack(in_=frame, fill="both", expand=True)
                holder.lift(frame)
                holder = frame
                wid.holder = frame
            if layout == "row":
                info = {"side": "left", "padx": 4, "pady": 4}
            elif layout == "tabs":
                container.add(holder, text=to_text(n.name or wid.widget_kind).title())
                info = None
            else:
                fill = "x" if wid.widget_kind in ("input", "password", "textbox", "listbox", "table", "progress", "panel", "row", "dropdown", "tabs") else None
                expand = wid.widget_kind in ("textbox", "listbox", "table", "tabs")
                anchor = "center" if opts.get("centered") else "w"
                info = {"anchor": anchor, "padx": 4, "pady": 4}
                if fill:
                    info["fill"] = "both" if expand else fill
                    info["expand"] = expand
                if wid.widget_kind == "canvas":
                    info = {"padx": 2, "pady": 2}
            if info is not None:
                holder.pack(**info)
                wid.pack_info = info
        if n.name:
            self.it.assign(n.name, wid)
        try:
            self.root.update_idletasks()
        except Exception:
            pass
        return wid

    def attach_canvas(self, canvas, parent_name, opts):
        container, theme, window, layout = self.parent_container(parent_name)
        w = self.tk.Canvas(container, width=canvas.width, height=canvas.height, highlightthickness=0, bd=0)
        canvas.attach(w)
        self._bind_canvas_mouse(w, canvas)
        wid = Widget(self, "canvas", canvas.name, w)
        wid.canvas = canvas
        canvas.widget = wid
        wid.extra["window"] = window
        if "at" in opts:
            x, y = to_number(self.it.eval(opts["at"][0])), to_number(self.it.eval(opts["at"][1]))
            w.place(x=int(x), y=int(y))
            wid.place_info = {"x": int(x), "y": int(y)}
        else:
            info = {"padx": 2, "pady": 2} if layout != "row" else {"side": "left", "padx": 2}
            w.pack(**info)
            wid.pack_info = info
        try:
            self.root.update()
        except Exception:
            pass

    def auto_canvas(self):
        from .graphics import Canvas
        from ..parser import Node
        n = Node("window", 0, name="drawing", opts={})
        app = self.make_window(n)
        app.tk.title("Memowrite Drawing")
        app.tk.geometry("720x520")
        app.body.pack_configure(padx=0, pady=0)
        canvas = Canvas("drawing", 720, 520, "#ffffff")
        w = self.tk.Canvas(app.body, width=720, height=520, highlightthickness=0, bd=0)
        w.pack(fill="both", expand=True)
        canvas.attach(w)
        self._bind_canvas_mouse(w, canvas)
        wid = Widget(self, "canvas", "drawing", w)
        wid.canvas = canvas
        canvas.widget = wid
        self.it.current_canvas = canvas
        self.it.globals["drawing"] = canvas
        return canvas

    def _bind_canvas_mouse(self, w, canvas):
        def motion(e):
            self.mouse = (e.x, e.y)
        w.bind("<Motion>", motion, add="+")
        w.bind("<B1-Motion>", motion, add="+")

    def _placeholder(self, entry, var, text, theme):
        def show_hint(*_):
            if not var.get():
                entry.configure(fg=theme["muted"])
                entry.insert(0, text)
                entry._memo_hint = True

        def hide_hint(*_):
            if getattr(entry, "_memo_hint", False):
                entry.delete(0, "end")
                entry.configure(fg=theme["fg"])
                entry._memo_hint = False
        entry.bind("<FocusIn>", hide_hint, add="+")
        entry.bind("<FocusOut>", show_hint, add="+")
        show_hint()
        orig_get = var.get

        def clean_get():
            return "" if getattr(entry, "_memo_hint", False) else orig_get()
        var.get = clean_get

    def _tooltip(self, w, text, theme):
        tip = {}

        def enter(e):
            t = self.tk.Toplevel(w)
            t.wm_overrideredirect(True)
            t.wm_geometry(f"+{e.x_root + 12}+{e.y_root + 12}")
            self.tk.Label(t, text=text, bg="#2b2d38", fg="#ffffff", font=(FONT, 9), padx=8, pady=4).pack()
            tip["t"] = t

        def leave(e):
            if tip.get("t"):
                tip["t"].destroy()
                tip["t"] = None
        w.bind("<Enter>", enter, add="+")
        w.bind("<Leave>", leave, add="+")

    # ------------------------------------------------------------ events
    def when(self, n):
        if n.task:
            fn = self.task_named(n.task)
        else:
            fn = Task("when", [], n.body, closure=self.it.frames[-1] if self.it.frames else None)
            # inline blocks can use x, y, key and value
            fn.params = ["x", "y"] if n.event.startswith("mouse") else (["key"] if n.event.startswith("key") or n.event == "anykey" else ["value"])
        ev = n.event
        if ev == "start":
            self.root_or_hidden().after(1, lambda: self.run_task(fn))
            return
        target = None
        if n.target is not None:
            target = self.it.lookup(n.target)
        if ev in ("keypressed", "keyreleased", "anykey"):
            win = self.window_of(target) if target is not None else (self.windows[-1] if self.windows else None)
            tkwin = win.tk if win is not None else self.root_or_hidden()
            want = wanted_key(self.it.eval(n.key)) if n.key is not None else None

            def on_key(e, f=fn, want=want):
                k = friendly_key(e.keysym)
                if want is None or k == want or (len(want) == 1 and e.char and e.char.lower() == want):
                    self.run_task(f, [k])
            seq = "<KeyRelease>" if ev == "keyreleased" else "<KeyPress>"
            tkwin.bind(seq, on_key, add="+")
            return
        if ev.startswith("mouse"):
            if target is None:
                target_tk = (self.it.current_canvas.tk if getattr(self.it, "current_canvas", None) is not None and self.it.current_canvas.tk is not None
                             else (self.windows[-1].tk if self.windows else self.root_or_hidden()))
            elif hasattr(target, "canvas") and getattr(target, "canvas", None) is not None and getattr(target.canvas, "tk", None) is not None and not hasattr(target, "shapes"):
                target_tk = target.canvas.tk
            elif hasattr(target, "tk") and target.tk is not None and not hasattr(target, "shapes"):
                target_tk = target.tk
            elif hasattr(target, "shapes"):
                # clicking a shape
                shape_group = target
                canvas_tk = shape_group.canvas.tk

                def on_shape(e, f=fn, g=shape_group):
                    if g.contains_point(e.x, e.y):
                        self.run_task(f, [e.x, e.y])
                canvas_tk.bind("<Button-1>", on_shape, add="+")
                return
            else:
                raise MemoError("I can only listen to the mouse on windows, canvases and shapes")
            seq = {"mouseclick": "<Button-1>", "mousemove": "<Motion>", "mouserelease": "<ButtonRelease-1>",
                   "mousedrag": "<B1-Motion>", "mouseright": "<Button-3>"}[ev]
            target_tk.bind(seq, lambda e, f=fn: self.run_task(f, [e.x, e.y]), add="+")
            return
        if target is None:
            raise MemoError("What should I listen to? Write: when go is clicked do play")
        if isinstance(target, AppWindow):
            if ev == "closing":
                target.data["\x00onclose"] = fn
            elif ev == "resized":
                target.tk.bind("<Configure>", lambda e, f=fn: self.run_task(f, [e.width, e.height]) if e.widget is target.tk else None, add="+")
            elif ev == "opened":
                target.tk.after(1, lambda: self.run_task(fn))
            elif ev == "clicked":
                target.tk.bind("<Button-1>", lambda e, f=fn: self.run_task(f, [e.x, e.y]), add="+")
            else:
                raise MemoError(f"A window can't be '{ev}'. Try: closed, resized, clicked")
            return
        if hasattr(target, "shapes"):
            canvas_tk = target.canvas.tk if target.canvas is not None else None
            if canvas_tk is None:
                raise MemoError("That shape is not on a window yet")

            def on_shape(e, f=fn, g=target):
                if g.contains_point(e.x, e.y):
                    self.run_task(f, [e.x, e.y])
            canvas_tk.bind("<Button-1>", on_shape, add="+")
            return
        if not isinstance(target, Widget):
            raise MemoError(f"I can't listen for events on {type_name(target)}")
        k = target.widget_kind
        w = target.tk
        if ev == "clicked":
            if k == "button" or k == "colorpicker":
                old = w.cget("command")
                if k == "button":
                    w.configure(command=lambda f=fn, b=w: self.run_task(f, [b.cget("text")]))
                else:
                    w.bind("<ButtonRelease-1>", lambda e, f=fn: self.run_task(f), add="+")
            elif k == "canvas":
                w.bind("<Button-1>", lambda e, f=fn: self.run_task(f, [e.x, e.y]), add="+")
            else:
                w.bind("<Button-1>", lambda e, f=fn: self.run_task(f), add="+")
        elif ev == "doubleclicked":
            w.bind("<Double-Button-1>", lambda e, f=fn: self.run_task(f, [target.get_value()]), add="+")
        elif ev == "changed":
            if target.var is not None:
                target.var.trace_add("write", lambda *a, f=fn: self.run_task(f, [target.get_value()]))
            elif k == "textbox":
                w.bind("<<Modified>>", lambda e, f=fn: (w.edit_modified(False), self.run_task(f, [target.get_value()])) if w.edit_modified() else None, add="+")
            elif k == "listbox":
                w.bind("<<ListboxSelect>>", lambda e, f=fn: self.run_task(f, [target.get_value()]), add="+")
            elif k == "table":
                w.bind("<<TreeviewSelect>>", lambda e, f=fn: self.run_task(f, [target.get_value()]), add="+")
            elif k == "tabs":
                w.bind("<<NotebookTabChanged>>", lambda e, f=fn: self.run_task(f, [target.get_value()]), add="+")
            else:
                raise MemoError(f"A {k} can't change")
        elif ev == "submit":
            w.bind("<Return>", lambda e, f=fn: self.run_task(f, [target.get_value()]), add="+")
        elif ev == "hover":
            w.bind("<Enter>", lambda e, f=fn: self.run_task(f), add="+")
        else:
            raise MemoError(f"I don't know the event '{ev}'. Try: clicked, changed, submitted, double clicked")

    def add_menu(self, n):
        win = self.window_of(n.window)
        if win is None:
            raise MemoError("Menus go on windows")
        menubar = win.data.get("\x00menubar")
        if menubar is None:
            menubar = self.tk.Menu(win.tk)
            win.tk.configure(menu=menubar)
            win.data["\x00menubar"] = menubar
        sub = self.tk.Menu(menubar, tearoff=0)
        for label, task_name in n.items:
            fn = self.task_named(task_name)
            sub.add_command(label=to_text(self.it.eval(label)), command=lambda f=fn: self.run_task(f))
        menubar.add_cascade(label=to_text(self.it.eval(n.title)), menu=sub)

    # ------------------------------------------------------------ timers
    def every(self, ms, fn):
        root = self.root_or_hidden()
        entry = [None, True]

        def tick():
            if not entry[1] or self.quitting:
                return
            start = time.time()
            self.run_task(fn)
            if entry[1] and not self.quitting and self.root is not None:
                spent = int((time.time() - start) * 1000)
                entry[0] = self.root.after(max(1, ms - spent), tick)
        entry[0] = root.after(ms, tick)
        self.timers.append(entry)
        if not self.windows:
            self.had_windows = False

    def after(self, ms, fn):
        root = self.root_or_hidden()
        entry = [None, True]

        def fire():
            if entry[1]:
                self.run_task(fn)
        entry[0] = root.after(ms, fire)
        self.timers.append(entry)

    def stop_timers(self):
        for t in self.timers:
            t[1] = False
            try:
                self.root.after_cancel(t[0])
            except Exception:
                pass
        self.timers = []

    # ------------------------------------------------------------ popups
    def popup(self, text, title=None, kind="info"):
        from tkinter import messagebox
        self.root_or_hidden()
        parent = self.windows[-1].tk if self.has_windows() else None
        fn = {"info": messagebox.showinfo, "warning": messagebox.showwarning, "error": messagebox.showerror}[kind]
        fn(title or "Memowrite", text, parent=parent)

    def ask_popup(self, prompt):
        from tkinter import simpledialog
        root = self.root_or_hidden()
        parent = self.windows[-1].tk if self.has_windows() else root
        return simpledialog.askstring("Memowrite", prompt, parent=parent)

    def ask_yes_no(self, question):
        from tkinter import messagebox
        self.root_or_hidden()
        parent = self.windows[-1].tk if self.has_windows() else None
        return messagebox.askyesno("Memowrite", question, parent=parent)

    def pick_file(self, save=False):
        from tkinter import filedialog
        self.root_or_hidden()
        if save:
            return filedialog.asksaveasfilename() or ""
        return filedialog.askopenfilename() or ""

    def pick_folder(self):
        from tkinter import filedialog
        self.root_or_hidden()
        return filedialog.askdirectory() or ""


def extra_builtins(it):
    def key_down(name):
        gui = it.ensure_gui()
        return wanted_key(name) in gui.keys_down

    def mouse_x():
        return it.ensure_gui().mouse[0]

    def mouse_y():
        return it.ensure_gui().mouse[1]

    def confirm(question):
        return it.ensure_gui().ask_yes_no(to_text(question))

    def pick_file():
        return it.ensure_gui().pick_file()

    def pick_save_file():
        return it.ensure_gui().pick_file(save=True)

    def pick_folder():
        return it.ensure_gui().pick_folder()

    def keys_pressed():
        return sorted(it.ensure_gui().keys_down)

    def windows_open():
        return it.gui is not None and it.gui.has_windows()

    return {
        "key_down": (key_down, 1, 1, "Is this key held down right now?"),
        "mouse_x": (mouse_x, 0, 0, "Where the mouse is (left-right) on the canvas"),
        "mouse_y": (mouse_y, 0, 0, "Where the mouse is (up-down) on the canvas"),
        "confirm": (confirm, 1, 1, "Asks a yes/no question in a popup"),
        "pick_file": (pick_file, 0, 0, "Lets the user choose a file"),
        "pick_save_file": (pick_save_file, 0, 0, "Lets the user choose where to save"),
        "pick_folder": (pick_folder, 0, 0, "Lets the user choose a folder"),
        "keys_pressed": (keys_pressed, 0, 0, "All keys held down right now"),
        "window_is_open": (windows_open, 0, 0, "Is any window still open?"),
    }
