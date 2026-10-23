"""Memowrite values and how they turn into text."""

from .errors import MemoError


class Task:
    """A task (function) written in Memowrite."""

    def __init__(self, name, params, body, owner=None, closure=None):
        self.name = name
        self.params = params
        self.body = body
        self.owner = owner          # instance for kind methods
        self.closure = closure      # local frame where it was made (for nested tasks)

    def bound(self, owner):
        return Task(self.name, self.params, self.body, owner, self.closure)

    def __repr__(self):
        return f"task {self.name}"


class Builtin:
    def __init__(self, name, fn, doc="", min_args=0, max_args=None):
        self.name = name
        self.fn = fn
        self.doc = doc
        self.min_args = min_args
        self.max_args = max_args

    def __repr__(self):
        return f"built-in task {self.name}"


class Kind:
    """A blueprint for making things (like a class)."""

    def __init__(self, name, fields, methods):
        self.name = name
        self.fields = fields
        self.methods = methods  # name -> Task

    def __repr__(self):
        return f"kind {self.name}"


class Instance:
    def __init__(self, kind):
        self.kind = kind
        self.fields = {}

    def __repr__(self):
        inside = ", ".join(f"{k}: {to_text(v, True)}" for k, v in self.fields.items())
        return f"{self.kind.name}({inside})"


def is_number(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def tidy_number(v):
    if isinstance(v, float):
        if v != v:
            return v
        if v.is_integer() and abs(v) < 1e15:
            return int(v)
    return v


def number_text(v):
    v = tidy_number(v)
    if isinstance(v, int):
        return str(v)
    if v != v:
        return "not a number"
    if v in (float("inf"), float("-inf")):
        return "infinity" if v > 0 else "minus infinity"
    text = f"{v:.10f}".rstrip("0").rstrip(".")
    if text in ("-0", ""):
        text = "0"
    return text


def to_text(v, nested=False):
    if v is None:
        return "nothing"
    if v is True:
        return "yes"
    if v is False:
        return "no"
    if is_number(v):
        return number_text(v)
    if isinstance(v, str):
        return f'"{v}"' if nested else v
    if isinstance(v, list):
        return "[" + ", ".join(to_text(x, True) for x in v) + "]"
    if isinstance(v, dict):
        return "{" + ", ".join(f"{to_text(k)}: {to_text(x, True)}" for k, x in v.items()) + "}"
    if isinstance(v, tuple):
        return "(" + ", ".join(to_text(x, True) for x in v) + ")"
    return str(v)


def type_name(v):
    if v is None:
        return "nothing"
    if isinstance(v, bool):
        return "yes/no"
    if is_number(v):
        return "number"
    if isinstance(v, str):
        return "text"
    if isinstance(v, list):
        return "list"
    if isinstance(v, dict):
        return "book"
    if isinstance(v, (Task, Builtin)):
        return "task"
    if isinstance(v, Kind):
        return "kind"
    if isinstance(v, Instance):
        return v.kind.name
    name = getattr(v, "TYPE_NAME", None)
    return name or type(v).__name__.lower()


def truthy(v):
    if v is None or v is False:
        return False
    if is_number(v):
        return v != 0
    if isinstance(v, str):
        return v.strip().lower() not in ("", "no", "false", "off", "0")
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def looks_like_number(s):
    if not isinstance(s, str):
        return False
    t = s.strip()
    try:
        float(t)
        return t != "" and t.lower() not in ("nan", "inf", "-inf", "infinity")
    except ValueError:
        return False


def to_number(v, line=None, what="this"):
    if is_number(v):
        return v
    if isinstance(v, bool):
        return 1 if v else 0
    if isinstance(v, str):
        t = v.strip()
        try:
            return int(t)
        except ValueError:
            pass
        try:
            return tidy_number(float(t))
        except ValueError:
            pass
    if v is None:
        raise MemoError(f"I needed a number but {what} is nothing (it has no value yet)", line,
                        hint="Did you forget to set it first?")
    raise MemoError(f"I needed a number but got {to_text(v, True)}", line)


def same(a, b, exact=False):
    if is_number(a) and is_number(b):
        return abs(a - b) < 1e-9 if isinstance(a, float) or isinstance(b, float) else a == b
    if not exact:
        if isinstance(a, str) and isinstance(b, str):
            return a.strip().lower() == b.strip().lower()
        if is_number(a) and looks_like_number(b):
            return same(a, to_number(b))
        if is_number(b) and looks_like_number(a):
            return same(to_number(a), b)
        if isinstance(a, bool) and isinstance(b, str):
            return truthy(b) == a and b.strip().lower() in ("yes", "no", "true", "false", "on", "off")
        if isinstance(b, bool) and isinstance(a, str):
            return same(b, a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y, exact) for x, y in zip(a, b))
    return a == b
