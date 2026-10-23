"""Memowrite parser.

Reads a whole program (a list of lines) and builds a tree of statements.
Each statement is a Node with a `kind` and some fields.

The language is line based. Blocks (if, repeat, task, model, try ...)
are closed with `end` (or `done`, or `end if`, `end repeat` ...).
"""

from .errors import MemoError
from .lexer import tokenize, is_comment_line


class Node:
    __slots__ = ("kind", "line", "f")

    def __init__(self, kind, line, **fields):
        self.kind = kind
        self.line = line
        self.f = fields

    def __getattr__(self, name):
        try:
            return self.f[name]
        except KeyError:
            raise AttributeError(name)

    def __repr__(self):
        return f"<{self.kind} {self.f}>"


def E(kind, *args):
    """Expression node (plain tuple for speed)."""
    return (kind,) + args


# ---------------------------------------------------------------- word lists

BLOCK_END = {"end", "done", "endif", "endrepeat", "endtask", "finish"}

COLOR_WORDS = {"color", "colour", "fill", "filled"}

OPTION_WORDS = {
    "at", "size", "sized", "color", "colour", "fill", "outline", "border", "width", "thickness",
    "called", "named", "saying", "doing", "with", "points", "font", "titled", "title", "from",
    "to", "on", "in", "angle", "by", "then", "times", "into", "as", "every", "radius",
    "text", "image", "height", "step", "tip", "placeholder", "bold", "rounded", "speed", "start",
    "extent", "style", "background", "foreground", "icon", "spin", "wrap", "or", "do",
}

MULTIWORD_FUNCS = {
    ("square", "root"): "sqrt",
    ("upper", "case"): "uppercase",
    ("lower", "case"): "lowercase",
    ("title", "case"): "titlecase",
    ("absolute", "value"): "abs",
    ("number", "of", "items", "in"): "length",
    ("number", "of", "letters", "in"): "length",
    ("type", "of"): "typeof",
    ("current", "time"): "time",
    ("current", "date"): "today",
    ("the", "time"): "time",
    ("the", "date"): "today",
    ("mouse", "x"): "mouse_x",
    ("mouse", "y"): "mouse_y",
    ("file", "exists"): "file_exists",
    ("folder", "exists"): "folder_exists",
    ("files", "in"): "files_in",
    ("words", "in"): "words",
    ("lines", "in"): "lines",
    ("letters", "in"): "letters",
    ("keys", "in"): "keys",
    ("values", "in"): "values",
    ("biggest", "in"): "max",
    ("smallest", "in"): "min",
    ("sum", "of"): "sum",
    ("average", "of"): "average",
    ("key", "is", "down"): "key_down",
}


class TokenStream:
    def __init__(self, tokens, line):
        self.t = tokens
        self.i = 0
        self.line = line

    def peek(self, k=0):
        j = self.i + k
        return self.t[j] if j < len(self.t) else None

    def next(self):
        tok = self.peek()
        if tok is None:
            raise MemoError("This line ended too early", self.line)
        self.i += 1
        return tok

    def done(self):
        return self.i >= len(self.t)

    def at_word(self, *words, k=0):
        tok = self.peek(k)
        return tok is not None and tok.kind == "WORD" and tok.value in words

    def at_op(self, *ops, k=0):
        tok = self.peek(k)
        return tok is not None and tok.kind == "OP" and tok.value in ops

    def accept_word(self, *words):
        if self.at_word(*words):
            return self.next().value
        return None

    def accept_op(self, *ops):
        if self.at_op(*ops):
            return self.next().value
        return None

    def accept_phrase(self, *words):
        for k, w in enumerate(words):
            if not self.at_word(w, k=k):
                return False
        self.i += len(words)
        return True

    def expect_word(self, *words):
        tok = self.peek()
        if tok is None or tok.kind != "WORD" or tok.value not in words:
            got = "the end of the line" if tok is None else repr(tok.value)
            raise MemoError(f"I expected the word '{words[0]}' here but found {got}", self.line)
        self.i += 1
        return tok.value

    def expect_op(self, op):
        tok = self.peek()
        if tok is None or tok.kind != "OP" or tok.value != op:
            got = "the end of the line" if tok is None else repr(tok.value)
            raise MemoError(f"I expected '{op}' here but found {got}", self.line)
        self.i += 1

    def name(self, what="a name"):
        tok = self.peek()
        if tok is None or tok.kind != "WORD":
            got = "the end of the line" if tok is None else repr(tok.value)
            raise MemoError(f"I expected {what} here but found {got}", self.line)
        self.i += 1
        return tok.value

    def expect_end(self):
        if not self.done():
            tok = self.peek()
            raise MemoError(f"I didn't expect {tok.value!r} here. Is something extra on this line?", self.line)


# ------------------------------------------------------------- expressions

class ExprParser:
    """Turns tokens into expression trees. English operators are allowed:
    plus, minus, times, divided by, is, is not, is more than, and, or, not ..."""

    def __init__(self, ts, stops=()):
        self.ts = ts
        self.stops = set(stops)

    @property
    def line(self):
        return self.ts.line

    def stopped(self, k=0):
        tok = self.ts.peek(k)
        return tok is None or (tok.kind == "WORD" and tok.value in self.stops)

    def word_op(self, *words, k=0):
        return (not self.stopped(k)) and self.ts.at_word(*words, k=k)

    def parse(self):
        if self.ts.done():
            raise MemoError("I expected a value here (like a number, some text or a name)", self.line)
        return self.parse_or()

    def parse_or(self):
        left = self.parse_and()
        while self.word_op("or") or self.ts.at_op("||"):
            self.ts.next()
            left = E("or", left, self.parse_and())
        return left

    def parse_and(self):
        left = self.parse_not()
        while self.word_op("and"):
            self.ts.next()
            left = E("and", left, self.parse_not())
        return left

    def parse_not(self):
        if self.word_op("not"):
            self.ts.next()
            return E("not", self.parse_not())
        return self.parse_compare()

    def parse_compare(self):
        left = self.parse_add()
        ts = self.ts
        while True:
            if ts.at_op("==", "="):
                ts.next(); left = E("cmp", "==", left, self.parse_add()); continue
            if ts.at_op("!="):
                ts.next(); left = E("cmp", "!=", left, self.parse_add()); continue
            if ts.at_op(">", "<", ">=", "<="):
                op = ts.next().value; left = E("cmp", op, left, self.parse_add()); continue
            if self.word_op("equals"):
                ts.next(); left = E("cmp", "==", left, self.parse_add()); continue
            if self.word_op("contains", "has"):
                ts.next(); left = E("cmp", "contains", left, self.parse_add()); continue
            if self.word_op("touches"):
                ts.next(); left = E("cmp", "touches", left, self.parse_add()); continue
            if self.word_op("does") and ts.at_word("not", k=1):
                ts.next(); ts.next()
                w = ts.next()
                if w.value in ("contain", "have"):
                    left = E("not", E("cmp", "contains", left, self.parse_add())); continue
                if w.value in ("touch",):
                    left = E("not", E("cmp", "touches", left, self.parse_add())); continue
                if w.value in ("equal",):
                    left = E("cmp", "!=", left, self.parse_add()); continue
                if w.value in ("start",):
                    ts.expect_word("with"); left = E("not", E("cmp", "startswith", left, self.parse_add())); continue
                if w.value in ("end",):
                    ts.expect_word("with"); left = E("not", E("cmp", "endswith", left, self.parse_add())); continue
                raise MemoError(f"I don't know how to say 'does not {w.value}'", self.line)
            if self.word_op("starts", "begins") and ts.at_word("with", k=1):
                ts.next(); ts.next(); left = E("cmp", "startswith", left, self.parse_add()); continue
            if self.word_op("ends") and ts.at_word("with", k=1):
                ts.next(); ts.next(); left = E("cmp", "endswith", left, self.parse_add()); continue
            if self.word_op("is", "are", "was"):
                left = self.parse_is(left)
                continue
            return left

    def parse_is(self, left):
        ts = self.ts
        ts.next()  # is
        negate = False
        if ts.accept_word("not"):
            negate = True
        result = None
        if ts.accept_word("empty"):
            result = E("empty", left)
        elif ts.accept_word("nothing"):
            result = E("cmp", "==", left, E("nothing"))
        elif ts.accept_word("even"):
            result = E("even", left)
        elif ts.accept_word("odd"):
            result = E("not", E("even", left))
        elif ts.at_word("more", "greater", "bigger", "higher", "larger", "over", "above", "after") and (ts.at_word("than", k=1) or ts.at_word("over", "above", "after")):
            w = ts.next().value
            if w not in ("over", "above", "after"):
                ts.expect_word("than")
            result = E("cmp", ">", left, self.parse_add())
        elif ts.at_word("less", "smaller", "lower", "fewer", "under", "below", "before") and (ts.at_word("than", k=1) or ts.at_word("under", "below", "before")):
            w = ts.next().value
            if w not in ("under", "below", "before"):
                ts.expect_word("than")
            result = E("cmp", "<", left, self.parse_add())
        elif ts.at_word("at") and ts.at_word("least", "most", k=1):
            ts.next()
            w = ts.next().value
            result = E("cmp", ">=" if w == "least" else "<=", left, self.parse_add())
        elif ts.at_word("equal", "same") :
            ts.next()
            ts.accept_word("to", "as")
            result = E("cmp", "==", left, self.parse_add())
        elif ts.at_word("between"):
            ts.next()
            low = ExprParser(ts, self.stops | {"and"}).parse_add()
            ts.expect_word("and")
            high = self.parse_add()
            result = E("between", left, low, high)
        elif ts.at_word("divisible"):
            ts.next(); ts.expect_word("by")
            result = E("divisible", left, self.parse_add())
        elif ts.at_word("in", "inside"):
            ts.next()
            result = E("cmp", "contains", self.parse_add(), left)
        elif ts.at_word("a", "an") and ts.peek(1) is not None and ts.peek(1).kind == "WORD" and ts.peek(1).value in TYPE_NAMES:
            ts.next()
            result = E("typeis", left, ts.next().value)
        elif ts.at_word("yes", "true", "no", "false", "on", "off") :
            result = E("cmp", "==", left, self.parse_add())
        else:
            result = E("cmp", "==", left, self.parse_add())
        return E("not", result) if negate else result

    def parse_add(self):
        left = self.parse_mul()
        ts = self.ts
        while True:
            if ts.at_op("+"):
                ts.next(); left = E("bin", "+", left, self.parse_mul())
            elif ts.at_op("-"):
                ts.next(); left = E("bin", "-", left, self.parse_mul())
            elif ts.at_op("&"):
                ts.next(); left = E("bin", "join", left, self.parse_mul())
            elif self.word_op("plus", "add"):
                ts.next(); left = E("bin", "+", left, self.parse_mul())
            elif self.word_op("minus"):
                ts.next(); left = E("bin", "-", left, self.parse_mul())
            elif self.word_op("joined", "followed") and ts.at_word("with", "by", k=1):
                ts.next(); ts.next(); left = E("bin", "join", left, self.parse_mul())
            else:
                return left

    def parse_mul(self):
        left = self.parse_power()
        ts = self.ts
        while True:
            if ts.at_op("*"):
                ts.next(); left = E("bin", "*", left, self.parse_power())
            elif ts.at_op("/"):
                ts.next(); left = E("bin", "/", left, self.parse_power())
            elif ts.at_op("%"):
                ts.next(); left = E("bin", "%", left, self.parse_power())
            elif self.word_op("times", "multiplied"):
                w = ts.next().value
                if w == "multiplied":
                    ts.expect_word("by")
                left = E("bin", "*", left, self.parse_power())
            elif self.word_op("divided") and ts.at_word("by", k=1):
                ts.next(); ts.next(); left = E("bin", "/", left, self.parse_power())
            elif self.word_op("over") and not self.stops:
                ts.next(); left = E("bin", "/", left, self.parse_power())
            elif self.word_op("mod", "modulo", "remainder"):
                w = ts.next().value
                if w == "remainder":
                    ts.accept_word("of", "after")
                left = E("bin", "%", left, self.parse_power())
            else:
                return left

    def parse_power(self):
        base = self.parse_unary()
        ts = self.ts
        if ts.at_op("^"):
            ts.next()
            return E("bin", "^", base, self.parse_unary())
        if self.word_op("to") and ts.at_word("the", k=1) and ts.at_word("power", k=2):
            ts.next(); ts.next(); ts.next(); ts.accept_word("of")
            return E("bin", "^", base, self.parse_unary())
        if self.word_op("squared"):
            ts.next()
            return E("bin", "^", base, E("num", 2))
        if self.word_op("cubed"):
            ts.next()
            return E("bin", "^", base, E("num", 3))
        return base

    def parse_unary(self):
        ts = self.ts
        if ts.at_op("-"):
            ts.next()
            return E("neg", self.parse_unary())
        if ts.at_op("+"):
            ts.next()
            return self.parse_unary()
        return self.parse_postfix(self.parse_primary())

    def parse_postfix(self, node):
        ts = self.ts
        while True:
            if ts.at_op("["):
                ts.next()
                if ts.at_op(":"):
                    ts.next()
                    end = ExprParser(ts).parse()
                    ts.expect_op("]")
                    node = E("slice", node, None, end)
                    continue
                idx = ExprParser(ts).parse()
                if ts.accept_op(":"):
                    end = None if ts.at_op("]") else ExprParser(ts).parse()
                    ts.expect_op("]")
                    node = E("slice", node, idx, end)
                    continue
                ts.expect_op("]")
                node = E("index", node, idx)
            elif ts.at_op("(") and node[0] in ("var", "prop", "index"):
                ts.next()
                args = self.parse_args(")")
                node = E("call", node, args)
            elif ts.at_op(".") and ts.peek(1) is not None and ts.peek(1).kind == "WORD":
                ts.next()
                field = ts.next().value
                node = E("prop", field, node)
            elif self.word_op("as") and ts.at_word("number", "text", "list", "whole", "decimal", "yes", "integer", k=1):
                ts.next()
                w = ts.next().value
                if w == "whole":
                    ts.accept_word("number")
                    w = "integer"
                if w == "decimal":
                    ts.accept_word("number")
                    w = "number"
                if w == "yes":
                    ts.expect_word("or"); ts.expect_word("no")
                    w = "bool"
                node = E("call", E("var", {"number": "number", "text": "text", "list": "list", "integer": "integer", "bool": "bool"}[w]), [node])
            else:
                return node

    def parse_args(self, closer):
        args = []
        if self.ts.accept_op(closer):
            return args
        while True:
            args.append(ExprParser(self.ts).parse())
            if self.ts.accept_op(","):
                continue
            self.ts.expect_op(closer)
            return args

    def parse_primary(self):
        ts = self.ts
        tok = ts.peek()
        if tok is None:
            raise MemoError("I expected a value here but the line ended", self.line)
        if tok.kind == "NUM":
            ts.next()
            # 5 seconds / 30 percent: units after numbers are fine to skip in some spots
            if self.word_op("percent"):
                ts.next()
                return E("num", tok.value / 100)
            return E("num", tok.value)
        if tok.kind == "STR":
            ts.next()
            return parse_text(tok.value, self.line)
        if tok.kind == "OP":
            if tok.value == "(":
                ts.next()
                inner = ExprParser(ts).parse()
                ts.expect_op(")")
                return inner
            if tok.value == "[":
                ts.next()
                return E("list", self.parse_args("]"))
            if tok.value == "{":
                ts.next()
                pairs = []
                if ts.accept_op("}"):
                    return E("book", pairs)
                while True:
                    k = ExprParser(ts).parse()
                    if not ts.accept_op(":"):
                        ts.expect_op("=")
                    v = ExprParser(ts).parse()
                    pairs.append((k, v))
                    if ts.accept_op(","):
                        continue
                    ts.expect_op("}")
                    return E("book", pairs)
            raise MemoError(f"I didn't expect '{tok.value}' here", self.line)
        # words
        w = tok.value
        if w in self.stops and not ts.at_word("of", k=1):
            raise MemoError(f"I expected a value before '{w}'", self.line)
        if w in ("yes", "true", "on"):
            ts.next(); return E("bool", True)
        if w in ("no", "false", "off"):
            ts.next(); return E("bool", False)
        if w in ("nothing", "none", "null", "empty") and not ts.at_word("list", "book", k=1):
            ts.next(); return E("nothing")
        if w == "my" and ts.peek(1) is not None and ts.peek(1).kind == "WORD":
            ts.next()
            field = ts.next().value
            return E("prop", field, E("var", "me"))
        if w == "pi":
            ts.next(); return E("num", 3.141592653589793)
        # "an empty list" / "a new list" / "empty book"
        if w in ("a", "an", "new", "empty"):
            j = 0
            while ts.at_word("a", "an", "new", "empty", k=j):
                j += 1
            if ts.at_word("list", k=j):
                ts.i += j + 1; return E("list", [])
            if ts.at_word("book", "dictionary", "record", k=j):
                ts.i += j + 1; return E("book", [])
            if w in ("a", "an") and ts.at_word("random", k=1):
                ts.next()
                return self.parse_primary()
        if w == "the" and ts.peek(1) is not None and ts.peek(1).kind == "WORD":
            # "the length of x", "the first item of list", "the time"
            for phrase, fn in MULTIWORD_FUNCS.items():
                if phrase[0] == "the" and self._match_phrase(phrase):
                    ts.i += len(phrase)
                    return E("call", E("var", fn), [])
            ts.next()
            return self.parse_primary()
        if w == "random":
            ts.next()
            if ts.accept_word("number", "whole"):
                ts.accept_word("number")
                if ts.accept_word("from", "between"):
                    sub = ExprParser(ts, self.stops | {"to", "and"})
                    a = sub.parse_add()
                    ts.expect_word("to", "and")
                    b = self.parse_add()
                    return E("call", E("var", "random"), [a, b])
                return E("call", E("var", "random"), [])
            if ts.accept_word("item", "thing", "one", "choice", "element"):
                ts.expect_word("from", "of", "in")
                return E("call", E("var", "pick"), [self.parse_unary()])
            if ts.accept_word("color", "colour"):
                return E("call", E("var", "random_color"), [])
            if ts.at_op("("):
                return self.parse_postfix(E("var", "random"))
            return E("var", "random")
        if w in ("item", "letter", "character", "word", "line") and ts.peek(1) is not None and not ts.at_word("of", k=1) and not ts.at_op("(", "=", k=1) and (ts.peek(1).kind in ("NUM", "WORD", "OP")) and w not in self.stops:
            # item 2 of fruits / letter 1 of name
            save = ts.i
            ts.next()
            try:
                idx = ExprParser(ts, self.stops | {"of", "from", "in"}).parse_add()
                if ts.accept_word("of", "from", "in"):
                    obj = self.parse_unary()
                    kind = {"item": "index", "letter": "index", "character": "index"}.get(w)
                    if kind:
                        return E("index", obj, idx)
                    return E("call", E("var", w + "_at"), [obj, idx])
            except MemoError:
                pass
            ts.i = save
        if w in ("first", "last") and ts.at_word("item", "letter", "one", "character", "word", "line", k=1) and ts.at_word("of", "in", "from", k=2):
            ts.next(); kind = ts.next().value; ts.next()
            obj = self.parse_unary()
            if kind in ("word", "line"):
                return E("call", E("var", f"{w}_{kind}"), [obj])
            return E("index", obj, E("num", 1 if w == "first" else -1))
        # multi-word built in names: "square root of", "upper case of"
        for phrase, fn in MULTIWORD_FUNCS.items():
            if phrase[0] == w and self._match_phrase(phrase):
                ts.i += len(phrase)
                if fn in ("time", "today", "mouse_x", "mouse_y"):
                    return E("call", E("var", fn), [])
                ts.accept_word("of")
                if ts.at_op("("):
                    ts.next()
                    return E("call", E("var", fn), self.parse_args(")"))
                arg = self.parse_unary()
                return E("call", E("var", fn), [arg])
        ts.next()
        # word of something  ->  builtin call or property
        if ts.at_word("of") and "of" not in self.stops and ts.peek(1) is not None and not (ts.peek(1).kind == "WORD" and ts.peek(1).value in self.stops and not ts.at_word("of", k=2)):
            ts.next()
            obj = self.parse_unary()
            return E("prop", w, obj)
        return E("var", w)

    def _match_phrase(self, phrase):
        for k, word in enumerate(phrase):
            if not self.ts.at_word(word, k=k):
                return False
        # "number of items in" must be followed by something
        return True


TYPE_NAMES = {"number", "text", "list", "book", "task", "word", "string", "yes", "shape", "window", "picture", "widget", "nothing", "integer"}


def parse_text(value, line):
    """Turn "Hello {name}!" into an interpolation node."""
    if "{" not in value:
        return E("str", value.replace("\x01", "{").replace("\x02", "}"))
    parts = []
    buf = []
    i = 0
    while i < len(value):
        c = value[i]
        if c == "{":
            if value.startswith("{{", i):
                buf.append("{"); i += 2; continue
            j = value.find("}", i)
            if j < 0:
                raise MemoError("A '{' in your text has no matching '}'", line)
            inner = value[i + 1:j].strip()
            if not inner:
                buf.append("{}")
                i = j + 1
                continue
            if buf:
                parts.append(E("str", "".join(buf).replace("\x01", "{").replace("\x02", "}")))
                buf = []
            ts = TokenStream(tokenize(inner, line), line)
            node = ExprParser(ts).parse()
            ts.expect_end()
            parts.append(node)
            i = j + 1
            continue
        if c == "}" and value.startswith("}}", i):
            buf.append("}"); i += 2; continue
        buf.append(c)
        i += 1
    if buf:
        parts.append(E("str", "".join(buf).replace("\x01", "{").replace("\x02", "}")))
    return E("interp", parts)


# ------------------------------------------------------------- statements

class Parser:
    def __init__(self, source, filename="program"):
        self.filename = filename
        self.lines = []
        # join lines ending with "..." (continuation)
        pending = None
        pending_no = 0
        for no, raw in enumerate(source.splitlines(), start=1):
            text = raw.rstrip()
            if pending is not None:
                text = pending + " " + text.strip()
                no = pending_no
                pending = None
            if text.endswith("..."):
                pending = text[:-3]
                pending_no = no
                continue
            stripped = text.strip()
            if is_comment_line(stripped):
                continue
            # "note" comments at the end of a line are not supported (use #)
            toks = tokenize(stripped, no)
            if not toks:
                continue
            self.lines.append((no, toks, stripped))
        self.pos = 0

    # -- block helpers
    def parse_program(self):
        body = self.parse_block(top=True)
        return body

    def current(self):
        return self.lines[self.pos] if self.pos < len(self.lines) else None

    def first_word(self, entry):
        toks = entry[1]
        return toks[0].value if toks and toks[0].kind == "WORD" else None

    def is_end(self, entry):
        toks = entry[1]
        if not toks or toks[0].kind != "WORD":
            return False
        w = toks[0].value
        if w in BLOCK_END:
            return True
        return False

    def parse_block(self, top=False, stop_words=()):
        body = []
        while self.pos < len(self.lines):
            entry = self.lines[self.pos]
            fw = self.first_word(entry)
            if self.is_end(entry):
                if top:
                    raise MemoError("This 'end' doesn't close anything", entry[0])
                return body
            if fw in stop_words and self._is_stop_line(entry, fw, stop_words):
                if top:
                    raise MemoError(f"'{fw}' must come inside a block", entry[0])
                return body
            self.pos += 1
            stmt = self.parse_statement(entry)
            if stmt is not None:
                body.append(stmt)
        if not top:
            raise MemoError("A block was never closed. Add 'end' at the end of it.", self.lines[-1][0] if self.lines else 1)
        return body

    def _is_stop_line(self, entry, fw, stop_words=()):
        toks = entry[1]
        if fw == "if":
            return len(toks) >= 3 and toks[1].is_word("it", "that") and toks[2].is_word("fails", "failed", "breaks", "goes")
        if fw == "when" and "is" not in stop_words:
            return len(toks) > 1 and toks[1].is_word("it", "that")
        return True

    def close_block(self, start_line):
        entry = self.current()
        if entry is None:
            raise MemoError("This block was never closed. Add 'end' at the end of it.", start_line)
        self.pos += 1

    # -- main dispatcher
    def parse_statement(self, entry):
        no, toks, raw = entry
        ts = TokenStream(toks, no)
        first = toks[0]
        if first.kind == "WORD":
            handler = getattr(self, "st_" + first.value, None)
            if handler is None:
                alias = STATEMENT_ALIASES.get(first.value)
                if alias:
                    handler = getattr(self, "st_" + alias)
            if handler is not None:
                save = ts.i
                ts.next()
                result = handler(ts, no)
                if result is not NOT_MINE:
                    if result is not None and not isinstance(result, list):
                        ts.expect_end()
                    return result
                ts.i = save
        # fallback: expression statement (task call like greet("bob")) or x = 5
        if len(toks) >= 2 and toks[0].kind == "WORD" and toks[1].is_op("="):
            ts.next(); ts.next()
            value = ExprParser(ts).parse()
            ts.expect_end()
            return Node("set", no, target=E("var", toks[0].value), value=value)
        if toks[0].kind == "WORD" and len(toks) >= 2 and toks[1].is_op("[", "."):
            # list[1] = 5   /  person.name = "Bob"
            target = ExprParser(ts, {"to"}).parse_unary()
            if ts.accept_op("=") or ts.accept_word("to"):
                value = ExprParser(ts).parse()
                ts.expect_end()
                return Node("set", no, target=target, value=value)
            ts.i = 0
        if (toks[0].kind == "WORD" and len(toks) > 1 and not toks[1].is_op("(", "=", "[", ".")
                and not (toks[1].kind == "WORD" and toks[1].value in ("of", "is", "plus", "and", "or"))):
            from .errors import suggest
            guess = suggest(toks[0].value, KNOWN_COMMANDS, 0.6)
            hint = f"Did you mean '{guess}'?" if guess else "Every line starts with a command word like say, set, if, repeat, draw, add ..."
            raise MemoError(f"I don't know the command '{toks[0].value}'", no, hint=hint)
        expr = ExprParser(ts).parse()
        ts.expect_end()
        if expr[0] not in ("call",):
            if expr[0] == "var":
                # a bare task name runs it: "greet"
                return Node("do", no, task=expr, args=[])
            raise MemoError(f"I don't know what to do with this line. Did you mean: say {raw}", no,
                            hint="Every line should start with a command word like say, set, if, repeat, draw ...")
        return Node("exprstmt", no, expr=expr)

    def expr(self, ts, stops=()):
        return ExprParser(ts, stops).parse()

    def exprs(self, ts, stops=()):
        """comma separated expressions"""
        items = [self.expr(ts, stops)]
        while ts.accept_op(","):
            items.append(self.expr(ts, stops))
        return items

    def target(self, ts, stops):
        """something you can assign to: name, name[1], name.field, text of label"""
        p = ExprParser(ts, stops)
        node = p.parse_unary()
        if node[0] not in ("var", "index", "prop"):
            raise MemoError("I can only put values into names (like: set score to 5)", ts.line)
        return node

    def options(self, ts, allowed):
        """Parse trailing options like: at 10, 20 size 30 color "red" called ball"""
        opts = {}
        stops = OPTION_WORDS
        while not ts.done():
            tok = ts.peek()
            if tok.kind != "WORD" or tok.value not in allowed:
                raise MemoError(f"I didn't expect {tok.value!r} here. I know these words here: {', '.join(sorted(set(allowed)))}", ts.line)
            word = ts.next().value
            kind = allowed[word]
            key = OPTION_KEY.get(word, word)
            if kind == "pair":       # at X, Y
                a = self.expr(ts, stops)
                ts.accept_op(",") or ts.accept_word("and")
                b = self.expr(ts, stops)
                opts[key] = (a, b)
            elif kind == "size":     # size A [by B]
                a = self.expr(ts, stops)
                b = None
                if ts.accept_word("by") or ts.accept_op(","):
                    b = self.expr(ts, stops)
                opts[key] = (a, b)
            elif kind == "name":
                opts[key] = ts.name()
            elif kind == "flag":
                opts[key] = True
            elif kind == "range":    # from A to B
                a = self.expr(ts, stops)
                ts.expect_word("to")
                b = self.expr(ts, stops)
                opts[key] = (a, b)
            elif kind == "list":
                opts[key] = self.exprs(ts, stops)
            else:
                opts[key] = self.expr(ts, stops)
        return opts

    # ================================================================ output
    def st_say(self, ts, no):
        if ts.done():
            return Node("say", no, values=[E("str", "")], end="\n")
        values = self.exprs(ts, {"without"})
        end = "\n"
        if ts.accept_word("without"):
            ts.expect_word("newline", "new", "enter", "a", "line")
            ts.accept_word("line", "newline")
            end = ""
        return Node("say", no, values=values, end=end)

    def st_whisper(self, ts, no):     # debug output to the error stream
        return Node("whisper", no, values=self.exprs(ts))

    def st_ask(self, ts, no):
        prompt = self.expr(ts, {"into", "and", "in", "as", "for"})
        popup = False
        if ts.accept_word("in"):
            ts.accept_word("a")
            ts.expect_word("popup", "box", "window", "dialog")
            popup = True
        ts.accept_word("and")
        ts.accept_word("put", "save", "store", "keep")
        ts.accept_word("the")
        ts.accept_word("answer", "it", "reply")
        ts.expect_word("into", "in", "as")
        target = self.target(ts, {"as"})
        convert = None
        if ts.accept_word("as"):
            convert = ts.name()
        return Node("ask", no, prompt=prompt, target=target, popup=popup, convert=convert)

    # ================================================================ variables
    def st_set(self, ts, no):
        # set x to 5 / set text of label to "hi" / set list[2] to 3 / set the score to 5
        ts.accept_word("the")
        if ts.peek() is not None and ts.peek().kind == "WORD" and ts.peek().value in ("title", "background", "color", "colour") and ts.at_word("of", k=1):
            pass
        target = self.target(ts, {"to", "as", "be"})
        if not ts.accept_word("to", "as", "be"):
            ts.expect_op("=")
        value = self.expr(ts)
        return Node("set", no, target=target, value=value)

    def st_let(self, ts, no):
        name = ts.name()
        if not ts.accept_word("be", "equal"):
            ts.expect_op("=")
        ts.accept_word("to")
        return Node("set", no, target=E("var", name), value=self.expr(ts))

    def st_change(self, ts, no):
        target = self.target(ts, {"by", "to"})
        if ts.accept_word("to"):
            return Node("set", no, target=target, value=self.expr(ts))
        ts.expect_word("by")
        return Node("change", no, target=target, op="+", value=self.expr(ts))

    def st_increase(self, ts, no):
        target = self.target(ts, {"by"})
        value = self.expr(ts) if ts.accept_word("by") else E("num", 1)
        return Node("change", no, target=target, op="+", value=value)

    def st_decrease(self, ts, no):
        target = self.target(ts, {"by"})
        value = self.expr(ts) if ts.accept_word("by") else E("num", 1)
        return Node("change", no, target=target, op="-", value=value)

    def st_add(self, ts, no):
        # add 5 to score / add "x" to list / add button b to window ...
        if ts.at_word(*WIDGET_KINDS) or (ts.at_word("a", "an", "new") and ts.at_word(*WIDGET_KINDS, k=1)):
            save = ts.i
            try:
                node = self.parse_add_widget(ts, no)
                if node.name or node.opts or ts.t[save].value in ("a", "an", "new", "button", "label", "heading", "slider", "separator", "space", "spacer", "divider"):
                    return node
            except MemoError:
                pass
            ts.i = save
        value = self.expr(ts, {"to", "into", "at"})
        ts.expect_word("to", "into")
        if ts.at_word("file"):
            ts.next()
            path = self.expr(ts)
            return Node("filewrite", no, value=value, path=path, mode="a")
        target = self.target(ts, {"at"})
        if ts.accept_word("at"):
            ts.accept_word("position", "place", "spot")
            pos = self.expr(ts)
            return Node("insert", no, value=value, target=target, pos=pos)
        return Node("addto", no, value=value, target=target)

    def st_subtract(self, ts, no):
        value = self.expr(ts, {"from"})
        ts.expect_word("from")
        return Node("change", no, target=self.target(ts, ()), op="-", value=value)

    def st_take(self, ts, no):
        if ts.at_word("away"):
            ts.next()
        return self.st_subtract(ts, no)

    def st_multiply(self, ts, no):
        target = self.target(ts, {"by"})
        ts.expect_word("by")
        return Node("change", no, target=target, op="*", value=self.expr(ts))

    def st_divide(self, ts, no):
        target = self.target(ts, {"by"})
        ts.expect_word("by")
        return Node("change", no, target=target, op="/", value=self.expr(ts))

    def st_swap(self, ts, no):
        a = self.target(ts, {"and", "with"})
        ts.expect_word("and", "with")
        b = self.target(ts, ())
        return Node("swap", no, a=a, b=b)

    def st_put(self, ts, no):
        value = self.expr(ts, {"into", "in", "at"})
        ts.expect_word("into", "in")
        ts.accept_word("the")
        if ts.at_word("file"):
            ts.next()
            return Node("filewrite", no, value=value, path=self.expr(ts), mode="a")
        target = self.target(ts, {"at"})
        if ts.accept_word("at"):
            ts.accept_word("position", "place", "spot")
            return Node("insert", no, value=value, target=target, pos=self.expr(ts))
        return Node("addto", no, value=value, target=target)

    def st_remove(self, ts, no):
        # remove "x" from list / remove item 2 from list / remove key "a" from book
        if ts.at_word("item", "position") and ts.peek(1) is not None and not ts.at_word("from", k=1):
            ts.next()
            idx = self.expr(ts, {"from"})
            ts.expect_word("from")
            return Node("removeat", no, index=idx, target=self.target(ts, ()))
        if ts.accept_word("everything", "all"):
            ts.accept_word("items")
            ts.expect_word("from")
            return Node("clearlist", no, target=self.target(ts, ()))
        if ts.at_word("first", "last") and ts.at_word("item", k=1):
            w = ts.next().value; ts.next(); ts.expect_word("from")
            return Node("removeat", no, index=E("num", 1 if w == "first" else -1), target=self.target(ts, ()))
        if ts.accept_word("key"):
            pass
        value = self.expr(ts, {"from"})
        ts.expect_word("from")
        return Node("remove", no, value=value, target=self.target(ts, ()))

    def st_sort(self, ts, no):
        target = self.target(ts, {"by", "backwards", "from", "in"})
        reverse = False
        key = None
        if ts.accept_word("backwards") or ts.accept_phrase("from", "biggest") or ts.accept_phrase("in", "reverse"):
            reverse = True
            ts.accept_word("to", "order"); ts.accept_word("smallest")
        elif ts.accept_phrase("from", "smallest"):
            ts.accept_word("to"); ts.accept_word("biggest")
        if ts.accept_word("by"):
            key = self.expr(ts, {"backwards"})
            if ts.accept_word("backwards"):
                reverse = True
        return Node("sort", no, target=target, reverse=reverse, key=key)

    def st_shuffle(self, ts, no):
        return Node("listop", no, op="shuffle", target=self.target(ts, ()))

    def st_reverse(self, ts, no):
        return Node("listop", no, op="reverse", target=self.target(ts, ()))

    def st_empty(self, ts, no):
        return Node("clearlist", no, target=self.target(ts, ()))

    # ================================================================ decisions
    def st_if(self, ts, no):
        cond = self.expr(ts, {"then"})
        ts.accept_word("then")
        if not ts.done():
            # one-line if:  if x is 5 then say "five"
            rest = ts.t[ts.i:]
            ts.i = len(ts.t)
            inner = self.parse_statement((no, rest, ""))
            return Node("if", no, branches=[(cond, [inner])], otherwise=None)
        branches = [(cond, self.parse_block(stop_words=("otherwise", "else", "elif")))]
        otherwise = None
        while True:
            entry = self.current()
            if entry is None:
                raise MemoError("This 'if' was never closed. Add 'end' after it.", no)
            fw = self.first_word(entry)
            if fw in ("otherwise", "else", "elif"):
                self.pos += 1
                ets = TokenStream(entry[1], entry[0])
                ets.next()
                if fw == "elif" or ets.accept_word("if"):
                    c = self.expr(ets, {"then"})
                    ets.accept_word("then")
                    ets.expect_end()
                    branches.append((c, self.parse_block(stop_words=("otherwise", "else", "elif"))))
                    continue
                ets.accept_op(":")
                ets.expect_end()
                otherwise = self.parse_block(stop_words=())
                self.close_block(no)
                break
            self.close_block(no)
            break
        return Node("if", no, branches=branches, otherwise=otherwise)

    def st_unless(self, ts, no):
        cond = self.expr(ts, {"then"})
        ts.accept_word("then")
        body = self.parse_block()
        self.close_block(no)
        return Node("if", no, branches=[(E("not", cond), body)], otherwise=None)

    def st_check(self, ts, no):
        # check value:  is 1 ... end  (a friendly switch)
        subject = self.expr(ts)
        ts.accept_op(":")
        cases = []
        default = None
        while True:
            entry = self.current()
            if entry is None:
                raise MemoError("This 'check' was never closed", no)
            if self.is_end(entry):
                self.pos += 1
                break
            self.pos += 1
            cts = TokenStream(entry[1], entry[0])
            if cts.accept_word("otherwise", "else", "default"):
                cts.accept_op(":")
                cts.expect_end()
                default = self.parse_block(stop_words=("is", "when", "case", "otherwise", "else", "default"))
                continue
            cts.expect_word("is", "when", "case")
            values = self.exprs(cts, {"then"})
            cts.accept_word("then")
            cts.accept_op(":")
            cts.expect_end()
            cases.append((values, self.parse_block(stop_words=("is", "when", "case", "otherwise", "else", "default"))))
        return Node("check", no, subject=subject, cases=cases, default=default)

    # ================================================================ loops
    def st_repeat(self, ts, no):
        if ts.accept_word("forever"):
            kind, a = "forever", None
        elif ts.accept_word("while"):
            kind, a = "while", self.expr(ts)
        elif ts.accept_word("until"):
            kind, a = "until", self.expr(ts)
        elif ts.accept_word("for"):
            ts.expect_word("each", "every")
            return self._for_each(ts, no)
        else:
            a = self.expr(ts, {"times", "time"})
            ts.expect_word("times", "time")
            kind = "times"
        ts.accept_op(":")
        body = self.parse_block()
        self.close_block(no)
        return Node("repeat", no, mode=kind, value=a, body=body)

    def st_while(self, ts, no):
        cond = self.expr(ts, {"do"})
        ts.accept_word("do")
        body = self.parse_block()
        self.close_block(no)
        return Node("repeat", no, mode="while", value=cond, body=body)

    def st_until(self, ts, no):
        cond = self.expr(ts, {"do"})
        ts.accept_word("do")
        body = self.parse_block()
        self.close_block(no)
        return Node("repeat", no, mode="until", value=cond, body=body)

    def st_forever(self, ts, no):
        body = self.parse_block()
        self.close_block(no)
        return Node("repeat", no, mode="forever", value=None, body=body)

    def st_loop(self, ts, no):
        return self.st_forever(ts, no)

    def st_for(self, ts, no):
        ts.expect_word("each", "every")
        return self._for_each(ts, no)

    def _for_each(self, ts, no):
        name = ts.name("a name for each item")
        index_name = None
        if ts.accept_op(",") or ts.accept_word("and"):
            index_name = name
            name = ts.name()
        ts.expect_word("in", "of", "from")
        seq = self.expr(ts)
        body = self.parse_block()
        self.close_block(no)
        return Node("foreach", no, name=name, index=index_name, seq=seq, body=body)

    def st_count(self, ts, no):
        name = ts.name("a counter name")
        ts.expect_word("from")
        start = self.expr(ts, {"to", "down", "by", "up"})
        down = False
        if ts.accept_word("down"):
            down = True
        ts.accept_word("up")
        ts.expect_word("to")
        end = self.expr(ts, {"by", "step"})
        step = None
        if ts.accept_word("by", "step"):
            step = self.expr(ts)
        body = self.parse_block()
        self.close_block(no)
        return Node("count", no, name=name, start=start, end=end, step=step, down=down, body=body)

    def st_stop(self, ts, no):
        if ts.done():
            return Node("break", no)
        if ts.accept_word("the", "this"):
            pass
        if ts.accept_word("program", "everything", "app", "running"):
            return Node("quit", no)
        if ts.accept_word("loop", "repeating", "counting"):
            return Node("break", no)
        if ts.accept_word("all", "every"):
            ts.expect_word("timers", "timer", "timers")
            return Node("stoptimers", no)
        if ts.accept_word("music", "sound", "sounds"):
            return Node("stopsound", no)
        if ts.accept_word("timer"):
            return Node("stoptimers", no)
        return Node("stoptimer", no, which=self.expr(ts))

    def st_break(self, ts, no):
        return Node("break", no)

    def st_skip(self, ts, no):
        ts.accept_word("to"); ts.accept_word("the"); ts.accept_word("next"); ts.accept_word("one", "item", "round", "turn")
        return Node("skip", no)

    def st_next(self, ts, no):
        return Node("skip", no)

    def st_continue(self, ts, no):
        return Node("skip", no)

    def st_quit(self, ts, no):
        return Node("quit", no)

    def st_exit(self, ts, no):
        return Node("quit", no)

    # ================================================================ tasks
    def st_make(self, ts, no):
        ts.accept_word("a", "an", "new")
        if ts.at_word("task", "function", "action", "command", "recipe"):
            ts.next()
            return self._task(ts, no)
        if ts.accept_word("list"):
            name = ts.name("a name for the list")
            items = []
            if ts.accept_word("with", "of", "containing", "holding"):
                items = self.exprs(ts)
            return Node("set", no, target=E("var", name), value=E("list", items))
        if ts.accept_word("book", "dictionary", "record", "object"):
            name = ts.name("a name for the book")
            pairs = []
            if ts.accept_word("with"):
                while True:
                    k = ts.name()
                    if not (ts.accept_word("as", "is") or ts.accept_op("=", ":")):
                        raise MemoError("Write book fields like: make book dog with name as \"Rex\", age as 3", no)
                    v = self.expr(ts, {"and"})
                    pairs.append((E("str", k), v))
                    if ts.accept_op(",") or ts.accept_word("and"):
                        continue
                    break
            return Node("set", no, target=E("var", name), value=E("book", pairs))
        if ts.at_word("window", "app", "application", "program", "form", "screen"):
            ts.next()
            return self._window(ts, no)
        if ts.at_word("canvas", "picture", "drawing", "paper", "image"):
            kind = ts.next().value
            return self._canvas(ts, no, kind)
        if ts.at_word("model", "sprite", "shape", "character", "object2d"):
            ts.next()
            return self._model(ts, no)
        if ts.at_word("folder", "directory"):
            ts.next()
            return Node("mkdir", no, path=self.expr(ts))
        if ts.at_word("kind", "type", "class", "blueprint"):
            ts.next()
            return self._kind(ts, no)
        if ts.at_word("timer"):
            ts.next()
            return self.parse_every_like(ts, no)
        # make x 5 / make score equal to 5
        name = ts.name()
        ts.accept_word("be", "equal", "equals")
        ts.accept_word("to")
        return Node("set", no, target=E("var", name), value=self.expr(ts))

    def st_create(self, ts, no):
        return self.st_make(ts, no)

    def st_define(self, ts, no):
        ts.accept_word("task", "function")
        return self._task(ts, no)

    def st_to(self, ts, no):
        # to greet with name ... end   (Logo style)
        return self._task(ts, no)

    def st_task(self, ts, no):
        return self._task(ts, no)

    def st_function(self, ts, no):
        return self._task(ts, no)

    def _task(self, ts, no):
        ts.accept_word("called", "named")
        name = ts.name("a name for the task")
        params = []
        if ts.accept_op("("):
            if not ts.accept_op(")"):
                while True:
                    params.append(ts.name())
                    if ts.accept_op(","):
                        continue
                    ts.expect_op(")")
                    break
        elif ts.accept_word("with", "using", "taking", "needing", "given"):
            while True:
                if ts.at_word("a", "an", "the") and ts.peek(1) is not None and ts.peek(1).kind == "WORD" and ts.peek(1).value != "and":
                    ts.next()
                params.append(ts.name())
                if ts.accept_op(",") or ts.accept_word("and"):
                    continue
                break
        ts.accept_op(":")
        ts.expect_end()
        body = self.parse_block()
        self.close_block(no)
        return Node("task", no, name=name, params=params, body=body)

    def _kind(self, ts, no):
        name = ts.name("a name for the kind")
        fields = []
        if ts.accept_word("with", "having"):
            while True:
                if ts.at_word("a", "an") and ts.peek(1) is not None and ts.peek(1).kind == "WORD" and ts.peek(1).value != "and":
                    ts.next()
                fields.append(ts.name())
                if ts.accept_op(",") or ts.accept_word("and"):
                    continue
                break
        ts.expect_end()
        methods = []
        while True:
            entry = self.current()
            if entry is None:
                raise MemoError("This 'kind' was never closed", no)
            if self.is_end(entry):
                self.pos += 1
                break
            self.pos += 1
            stmt = self.parse_statement(entry)
            if stmt.kind != "task":
                raise MemoError("Inside a kind you can only make tasks", entry[0])
            methods.append(stmt)
        return Node("kind", no, name=name, fields=fields, methods=methods)

    def st_do(self, ts, no):
        ts.accept_word("the")
        task = ExprParser(ts, {"with", "using", "on", "times", "in"}).parse_unary()
        args = []
        if ts.accept_word("with", "using", "on"):
            args = self.exprs(ts, {"times", "in"})
        if ts.at_word("in") and ts.at_word("background", "the", k=1):
            ts.next(); ts.accept_word("the"); ts.expect_word("background")
            return Node("do", no, task=task, args=args, background=True)
        if not ts.done():
            # do greet 3 times
            n = self.expr(ts, {"times"})
            ts.expect_word("times")
            return Node("repeat", no, mode="times", value=n, body=[Node("do", no, task=task, args=args)])
        return Node("do", no, task=task, args=args)

    def st_call(self, ts, no):
        return self.st_do(ts, no)

    def st_run(self, ts, no):
        if ts.at_word("file", "program", "script"):
            ts.next()
            return Node("runfile", no, path=self.expr(ts))
        return self.st_do(ts, no)

    def st_give(self, ts, no):
        ts.expect_word("back")
        if ts.done():
            return Node("return", no, value=E("nothing"))
        return Node("return", no, value=self.expr(ts))

    def st_return(self, ts, no):
        if ts.done():
            return Node("return", no, value=E("nothing"))
        return Node("return", no, value=self.expr(ts))

    def st_answer(self, ts, no):
        ts.accept_word("with")
        return Node("return", no, value=self.expr(ts))

    def st_use(self, ts, no):
        ts.accept_word("the")
        ts.accept_word("file", "library", "code", "module")
        return Node("use", no, path=self.expr(ts))

    def st_include(self, ts, no):
        return self.st_use(ts, no)

    def st_import(self, ts, no):
        return self.st_use(ts, no)

    # ================================================================ errors
    def st_try(self, ts, no):
        ts.accept_op(":")
        ts.accept_word("to")
        ts.expect_end()
        body = self.parse_block(stop_words=("if", "catch", "when", "onerror", "otherwise"))
        handler = None
        err_name = None
        entry = self.current()
        if entry is not None and not self.is_end(entry):
            self.pos += 1
            hts = TokenStream(entry[1], entry[0])
            if hts.accept_word("catch", "onerror", "otherwise"):
                pass
            else:
                hts.accept_word("if", "when")
                hts.expect_word("it", "that")
                hts.expect_word("fails", "failed", "breaks", "goes")
                hts.accept_word("wrong")
            if hts.accept_word("as", "with"):
                hts.accept_word("the")
                err_name = hts.name()
            hts.accept_op(":")
            hts.expect_end()
            handler = self.parse_block()
        self.close_block(no)
        return Node("try", no, body=body, handler=handler, err=err_name)

    def st_complain(self, ts, no):
        ts.accept_word("that", "about", "with")
        return Node("complain", no, value=self.expr(ts))

    def st_fail(self, ts, no):
        ts.accept_word("with", "because")
        return Node("complain", no, value=self.expr(ts))

    def st_make_sure(self, ts, no):
        return None

    def st_ensure(self, ts, no):
        cond = self.expr(ts, {"or"})
        msg = None
        if ts.accept_word("or"):
            ts.accept_word("complain", "say", "fail")
            msg = self.expr(ts)
        return Node("ensure", no, cond=cond, msg=msg)

    # ================================================================ memory (File.Memory)
    def st_remember(self, ts, no):
        # remember "score" as 10 / remember score   (stores variable under its own name)
        key = self.expr(ts, {"as", "is", "in"})
        if ts.accept_word("as", "is") or ts.accept_op("=", ":"):
            value = self.expr(ts)
        else:
            if key[0] != "var":
                raise MemoError("Write: remember \"name\" as value", no)
            value = key
            key = E("str", key[1])
        return Node("remember", no, key=key, value=value)

    def st_recall(self, ts, no):
        key = self.expr(ts, {"into", "as", "or"})
        default = None
        target = None
        if ts.accept_word("into", "as"):
            target = self.target(ts, {"or"})
        elif key[0] == "var":
            target = key
            key = E("str", key[1])
        else:
            raise MemoError("Write: recall \"name\" into variable", no)
        if ts.accept_word("or"):
            ts.accept_word("use", "default")
            default = self.expr(ts)
        return Node("recall", no, key=key, target=target, default=default)

    def st_forget(self, ts, no):
        if ts.accept_word("everything", "all"):
            return Node("forget", no, key=None)
        key = self.expr(ts)
        if key[0] == "var":
            key = E("str", key[1])
        return Node("forget", no, key=key)

    # ================================================================ files
    def st_write(self, ts, no):
        value = self.expr(ts, {"to", "into", "in"})
        ts.expect_word("to", "into", "in")
        ts.accept_word("the")
        ts.accept_word("file")
        return Node("filewrite", no, value=value, path=self.expr(ts), mode="w")

    def st_save(self, ts, no):
        # save model car to "car.mwmodel" / save list to file "x" / save picture to "x.png"
        if ts.at_word("model", "sprite"):
            ts.next()
            m = self.expr(ts, {"to", "as", "into"})
            ts.expect_word("to", "as", "into")
            ts.accept_word("file")
            return Node("savemodel", no, model=m, path=self.expr(ts))
        value = self.expr(ts, {"to", "as", "into", "in"})
        ts.expect_word("to", "as", "into", "in")
        ts.accept_word("the")
        ts.accept_word("file")
        return Node("save", no, value=value, path=self.expr(ts))

    def st_append(self, ts, no):
        value = self.expr(ts, {"to", "into"})
        ts.expect_word("to", "into")
        ts.accept_word("the")
        ts.accept_word("file")
        return Node("filewrite", no, value=value, path=self.expr(ts), mode="a")

    def st_read(self, ts, no):
        ts.accept_word("the")
        lines = False
        if ts.accept_word("lines"):
            ts.accept_word("of", "from", "in")
            lines = True
        ts.accept_word("file")
        path = self.expr(ts, {"into", "as"})
        ts.expect_word("into", "as")
        return Node("fileread", no, path=path, target=self.target(ts, ()), lines=lines)

    def st_load(self, ts, no):
        if ts.at_word("model", "sprite"):
            ts.next()
            name = ts.name()
            ts.expect_word("from")
            ts.accept_word("file")
            return Node("loadmodel", no, name=name, path=self.expr(ts))
        ts.accept_word("file")
        path = self.expr(ts, {"into", "as"})
        ts.expect_word("into", "as")
        return Node("load", no, path=path, target=self.target(ts, ()))

    def st_delete(self, ts, no):
        if ts.accept_word("file"):
            return Node("filedelete", no, path=self.expr(ts))
        if ts.accept_word("folder", "directory"):
            return Node("filedelete", no, path=self.expr(ts), folder=True)
        return Node("erase", no, what=self.expr(ts))

    def st_copy(self, ts, no):
        ts.accept_word("file")
        a = self.expr(ts, {"to"})
        ts.expect_word("to")
        if ts.accept_word("clipboard"):
            return Node("clipboard", no, value=a)
        if ts.at_word("the") and ts.at_word("clipboard", k=1):
            ts.next(); ts.next()
            return Node("clipboard", no, value=a)
        return Node("filecopy", no, src=a, dst=self.expr(ts), move=False)

    def st_rename(self, ts, no):
        ts.accept_word("file")
        a = self.expr(ts, {"to"})
        ts.expect_word("to")
        return Node("filecopy", no, src=a, dst=self.expr(ts), move=True)

    def st_open(self, ts, no):
        ts.accept_word("the")
        ts.accept_word("file", "website", "link", "page", "folder")
        return Node("openthing", no, what=self.expr(ts))

    def st_download(self, ts, no):
        url = self.expr(ts, {"into", "to", "as"})
        ts.expect_word("into", "to", "as")
        if ts.accept_word("file"):
            return Node("download", no, url=url, path=self.expr(ts), target=None)
        return Node("download", no, url=url, path=None, target=self.target(ts, ()))

    def st_fetch(self, ts, no):
        ts.accept_word("page", "website", "url", "the")
        return self.st_download(ts, no)

    # ================================================================ time
    def st_wait(self, ts, no):
        ts.accept_word("for")
        if ts.at_word("a"):
            ts.next()
            amount = E("num", 1)
        else:
            amount = self.expr(ts, set(TIME_UNITS))
        unit = ts.accept_word(*TIME_UNITS) or "seconds"
        return Node("wait", no, amount=amount, unit=unit)

    def st_pause(self, ts, no):
        return self.st_wait(ts, no)

    def st_sleep(self, ts, no):
        return self.st_wait(ts, no)

    def st_every(self, ts, no):
        return self.parse_every_like(ts, no, True)

    def parse_every_like(self, ts, no, said_every=False):
        if not said_every:
            ts.accept_word("every")
        amount = self.expr(ts, set(TIME_UNITS) | {"do", "doing", "run"})
        unit = ts.accept_word(*TIME_UNITS) or "milliseconds"
        if ts.accept_word("do", "doing", "run", "call"):
            task = ts.name("a task name")
            ts.expect_end()
            return Node("every", no, amount=amount, unit=unit, task=task, body=None)
        ts.accept_op(":")
        ts.expect_end()
        body = self.parse_block()
        self.close_block(no)
        return Node("every", no, amount=amount, unit=unit, task=None, body=body)

    def st_after(self, ts, no):
        amount = self.expr(ts, set(TIME_UNITS) | {"do"})
        unit = ts.accept_word(*TIME_UNITS) or "seconds"
        if ts.accept_word("do", "run", "call"):
            task = ts.name()
            return Node("after", no, amount=amount, unit=unit, task=task, body=None)
        ts.accept_op(":")
        ts.expect_end()
        body = self.parse_block()
        self.close_block(no)
        return Node("after", no, amount=amount, unit=unit, task=None, body=body)

    # ================================================================ screen & sound
    def st_clear(self, ts, no):
        if ts.done() or ts.accept_word("screen", "console", "terminal"):
            ts.accept_word("the")
            return Node("clearscreen", no)
        ts.accept_word("the")
        return Node("clearthing", no, what=self.expr(ts))

    def st_beep(self, ts, no):
        times = self.expr(ts, {"times"}) if not ts.done() else E("num", 1)
        ts.accept_word("times")
        return Node("beep", no, times=times)

    def st_play(self, ts, no):
        ts.accept_word("the", "a")
        if ts.accept_word("note", "tone"):
            freq = self.expr(ts, {"for"})
            dur = E("num", 300)
            if ts.accept_word("for"):
                dur = self.expr(ts, set(TIME_UNITS))
                unit = ts.accept_word(*TIME_UNITS) or "milliseconds"
                if unit.startswith("sec"):
                    dur = E("bin", "*", dur, E("num", 1000))
            return Node("tone", no, freq=freq, dur=dur)
        ts.accept_word("sound", "music", "song", "file")
        loop = False
        path = self.expr(ts, {"forever", "looping", "on"})
        if ts.accept_word("forever", "looping") or ts.accept_phrase("on", "repeat"):
            loop = True
        return Node("sound", no, path=path, loop=loop)

    def st_speak(self, ts, no):
        return Node("speak", no, value=self.expr(ts))

    def st_color(self, ts, no):
        # color text "green"  -> console colors
        ts.accept_word("text", "words", "output")
        return Node("consolecolor", no, value=self.expr(ts))

    def st_colour(self, ts, no):
        return self.st_color(ts, no)

    def st_show(self, ts, no):
        # show window / show message "hi" / show shape
        if ts.accept_word("message", "popup", "alert", "notice"):
            ts.accept_word("box")
            text = self.expr(ts, {"titled", "with"})
            title = None
            if ts.accept_word("titled") or ts.accept_phrase("with", "title"):
                title = self.expr(ts)
            return Node("popup", no, text=text, title=title, style="info")
        if ts.accept_word("warning"):
            return Node("popup", no, text=self.expr(ts), title=None, style="warning")
        if ts.accept_word("error"):
            return Node("popup", no, text=self.expr(ts), title=None, style="error")
        ts.accept_word("the")
        what = self.expr(ts)
        return Node("show", no, what=what)

    def st_hide(self, ts, no):
        ts.accept_word("the")
        return Node("hide", no, what=self.expr(ts))

    def st_alert(self, ts, no):
        return Node("popup", no, text=self.expr(ts), title=None, style="info")

    def st_close(self, ts, no):
        ts.accept_word("the")
        return Node("closewin", no, what=self.expr(ts))

    # ================================================================ GUI apps
    def _window(self, ts, no):
        name = ts.name("a name for the window")
        opts = self.options(ts, {
            "called": "expr", "titled": "expr", "title": "expr", "named": "expr",
            "sized": "size", "size": "size", "color": "expr", "colour": "expr", "background": "expr",
            "icon": "expr", "fullscreen": "flag", "resizable": "flag", "fixed": "flag", "theme": "expr",
            "dark": "flag", "at": "pair",
        })
        return Node("window", no, name=name, opts=opts)

    def parse_add_widget(self, ts, no):
        ts.accept_word("a", "an", "new")
        kind = ts.next().value
        if kind in ("input", "text", "progress", "check", "drop", "list", "number", "color", "date") and ts.at_word("box", "field", "bar", "area", "down", "picker", k=0):
            extra = ts.next().value
            kind = {"inputbox": "input", "inputfield": "input", "textbox": "textbox", "textfield": "input", "textarea": "textbox",
                    "progressbar": "progress", "checkbox": "checkbox", "dropdown": "dropdown", "listbox": "listbox",
                    "numberbox": "spinner", "numberfield": "spinner", "colorpicker": "colorpicker", "datepicker": "input"}.get(kind + extra, kind)
        kind = WIDGET_KINDS.get(kind, kind)
        name = None
        if ts.peek() is not None and ts.peek().kind == "WORD" and ts.peek().value not in ("to", "on", "in", "into", "called", "named"):
            name = ts.name()
        if ts.accept_word("called", "named"):
            name = ts.name()
        ts.expect_word("to", "on", "in", "into")
        ts.accept_word("the")
        parent = ts.name("the window (or panel) to add it to")
        opts = self.options(ts, WIDGET_OPTIONS)
        return Node("widget", no, wkind=kind, name=name, parent=parent, opts=opts)

    def st_when(self, ts, no):
        # when button is clicked do task / when key "space" is pressed in app do task
        # when mouse is clicked on board do task / when window closes do task
        # inline block form: when button is clicked ... end
        if ts.accept_word("key"):
            key = self.expr(ts, {"is", "pressed", "released", "goes", "in", "on", "do"})
            ts.accept_word("is", "gets", "goes")
            ev = ts.accept_word("pressed", "released", "held", "up", "down") or "pressed"
            if ev in ("down", "held"):
                ev = "pressed"
            if ev == "up":
                ev = "released"
            target = None
            if ts.accept_word("in", "on"):
                target = ts.name()
            return self._when_tail(ts, no, "key" + ev, target, key)
        if ts.accept_word("any"):
            ts.expect_word("key")
            ts.accept_word("is")
            ts.expect_word("pressed")
            target = None
            if ts.accept_word("in", "on"):
                target = ts.name()
            return self._when_tail(ts, no, "anykey", target, None)
        if ts.accept_word("mouse"):
            ts.accept_word("is", "button")
            ev = ts.next().value  # clicked, moves, moved, released, dragged, pressed
            ev = {"moves": "mousemove", "moved": "mousemove", "moving": "mousemove", "clicked": "mouseclick", "clicks": "mouseclick",
                  "pressed": "mouseclick", "released": "mouserelease", "dragged": "mousedrag", "drags": "mousedrag",
                  "rightclicked": "mouseright", "right": "mouseright"}.get(ev, "mouseclick")
            if ev == "mouseright":
                ts.accept_word("clicked", "clicks")
            target = None
            if ts.accept_word("on", "in", "over"):
                target = ts.name()
            return self._when_tail(ts, no, ev, target, None)
        if ts.accept_word("the"):
            pass
        if ts.accept_word("program", "app"):
            ts.accept_word("starts", "begins", "opens")
            return self._when_tail(ts, no, "start", None, None)
        target = ts.name()
        ts.accept_word("is", "gets", "was")
        ev = ts.next().value if not ts.at_word("do", "doing", "run", "call") and not ts.done() else "clicked"
        ev = {"clicks": "clicked", "pressed": "clicked", "pushed": "clicked", "tapped": "clicked",
              "changed": "changed", "changes": "changed", "moved": "changed", "typed": "changed", "edited": "changed",
              "closed": "closing", "closes": "closing", "closing": "closing",
              "selected": "changed", "picked": "changed", "chosen": "changed", "ticked": "changed", "checked": "changed",
              "submitted": "submit", "entered": "submit", "resized": "resized", "opened": "opened", "shown": "opened",
              "doubleclicked": "doubleclicked", "double": "doubleclicked", "hovered": "hover", "entered_": "hover"}.get(ev, ev)
        if ev == "doubleclicked":
            ts.accept_word("clicked")
        return self._when_tail(ts, no, ev, target, None)

    def _when_tail(self, ts, no, event, target, key):
        if ts.accept_word("do", "doing", "run", "call", "then"):
            if not ts.done():
                task = ts.name("a task name")
                ts.expect_end()
                return Node("when", no, event=event, target=target, key=key, task=task, body=None)
        ts.accept_op(":")
        ts.expect_end()
        body = self.parse_block()
        self.close_block(no)
        return Node("when", no, event=event, target=target, key=key, task=None, body=body)

    def st_on(self, ts, no):
        return self.st_when(ts, no)

    def st_focus(self, ts, no):
        ts.accept_word("on")
        return Node("focus", no, what=self.expr(ts))

    def st_enable(self, ts, no):
        return Node("enable", no, what=self.expr(ts), on=True)

    def st_disable(self, ts, no):
        return Node("enable", no, what=self.expr(ts), on=False)

    def st_menu(self, ts, no):
        # menu "File" in app with "Open" doing openit, "Quit" doing quitit
        title = self.expr(ts, {"in", "on"})
        ts.expect_word("in", "on")
        win = ts.name()
        ts.expect_word("with")
        items = []
        while True:
            label = self.expr(ts, {"doing", "do"})
            ts.expect_word("doing", "do")
            items.append((label, ts.name()))
            if ts.accept_op(","):
                continue
            break
        return Node("menu", no, title=title, window=win, items=items)

    # ================================================================ 2D graphics
    def _canvas(self, ts, no, kind):
        name = ts.name("a name for the canvas")
        parent = None
        if ts.accept_word("in", "on", "inside"):
            ts.accept_word("the")
            parent = ts.name()
        opts = self.options(ts, {"sized": "size", "size": "size", "color": "expr", "colour": "expr",
                                 "background": "expr", "at": "pair", "fill": "expr"})
        return Node("canvas", no, name=name, parent=parent, opts=opts, offscreen=(parent is None))

    def st_draw(self, ts, no):
        ts.accept_word("a", "an", "the")
        if ts.at_word("model", "sprite"):
            ts.next()
            return self._place(ts, no)
        shape = ts.next().value
        shape = SHAPE_ALIASES.get(shape, shape)
        if shape not in SHAPES:
            raise MemoError(f"I can't draw a '{shape}'. I can draw: {', '.join(sorted(SHAPES))}", no)
        main = None
        if shape in ("text", "image") and ts.peek() is not None and not (ts.peek().kind == "WORD" and ts.peek().value in DRAW_OPTIONS or ts.at_word("on", "in")):
            main = self.expr(ts, OPTION_WORDS)
        canvas = None
        if ts.accept_word("on", "in"):
            ts.accept_word("the")
            canvas = ts.name()
        opts = self.options(ts, DRAW_OPTIONS)
        if main is not None:
            opts["saying" if shape == "text" else "file"] = main
        return Node("draw", no, shape=shape, canvas=canvas, opts=opts)

    def st_paint(self, ts, no):
        return self.st_draw(ts, no)

    def st_fill(self, ts, no):
        # fill board with "skyblue"
        canvas = ts.name()
        ts.expect_word("with")
        return Node("fillcanvas", no, canvas=canvas, color=self.expr(ts))

    def _model(self, ts, no):
        name = ts.name("a name for the model")
        ts.accept_op(":")
        ts.expect_end()
        parts = []
        while True:
            entry = self.current()
            if entry is None:
                raise MemoError("This model was never closed. Add 'end' after its shapes.", no)
            if self.is_end(entry):
                self.pos += 1
                break
            self.pos += 1
            mts = TokenStream(entry[1], entry[0])
            mts.accept_word("draw", "a", "an", "add")
            mts.accept_word("a", "an")
            shape = mts.next().value
            shape = SHAPE_ALIASES.get(shape, shape)
            if shape not in SHAPES:
                raise MemoError(f"A model can be made from these shapes: {', '.join(sorted(SHAPES))}", entry[0])
            opts = self.options(mts, DRAW_OPTIONS)
            parts.append((shape, opts, entry[0]))
        return Node("model", no, name=name, parts=parts)

    def st_place(self, ts, no):
        return self._place(ts, no)

    def st_stamp(self, ts, no):
        return self._place(ts, no)

    def _place(self, ts, no):
        ts.accept_word("model", "sprite", "a", "the")
        model = ExprParser(ts, OPTION_WORDS).parse_unary()
        canvas = None
        if ts.accept_word("on", "in"):
            ts.accept_word("the")
            canvas = ts.name()
        opts = self.options(ts, {"at": "pair", "called": "name", "named": "name", "size": "expr", "scale": "expr",
                                 "angle": "expr", "color": "expr", "colour": "expr", "turned": "expr", "rotated": "expr"})
        return Node("place", no, model=model, canvas=canvas, opts=opts)

    def st_move(self, ts, no):
        what = ExprParser(ts, {"by", "to", "up", "down", "left", "right", "forward", "forwards", "towards", "toward"}).parse_unary()
        if ts.accept_word("to"):
            x = self.expr(ts, OPTION_WORDS); ts.accept_op(","); y = self.expr(ts)
            return Node("moveto", no, what=what, x=x, y=y)
        if ts.accept_word("by"):
            x = self.expr(ts, OPTION_WORDS); ts.accept_op(","); y = self.expr(ts)
            return Node("moveby", no, what=what, x=x, y=y)
        if ts.at_word("up", "down", "left", "right"):
            d = ts.next().value
            amount = self.expr(ts) if not ts.done() else E("num", 10)
            dx, dy = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}[d]
            return Node("moveby", no, what=what, x=E("bin", "*", E("num", dx), amount), y=E("bin", "*", E("num", dy), amount))
        if ts.accept_word("forward", "forwards"):
            return Node("forward", no, what=what, amount=self.expr(ts))
        if ts.accept_word("towards", "toward"):
            tx = self.expr(ts, OPTION_WORDS | {"by"}); ts.accept_op(","); ty = self.expr(ts, {"by", "speed"})
            ts.expect_word("by", "speed")
            return Node("towards", no, what=what, x=tx, y=ty, amount=self.expr(ts))
        raise MemoError("Write: move NAME by 5, 0   or   move NAME to 100, 50   or   move NAME left 10", no)

    def st_rotate(self, ts, no):
        what = ExprParser(ts, {"by", "to"}).parse_unary()
        if ts.accept_word("to"):
            return Node("rotate", no, what=what, angle=self.expr(ts, {"degrees"}), absolute=True)
        ts.expect_word("by")
        angle = self.expr(ts, {"degrees"})
        ts.accept_word("degrees", "degree")
        return Node("rotate", no, what=what, angle=angle, absolute=False)

    def st_turn(self, ts, no):
        what = ExprParser(ts, {"by", "left", "right", "to"}).parse_unary()
        if ts.accept_word("left"):
            angle = E("neg", self.expr(ts, {"degrees"}))
        else:
            ts.accept_word("right", "by")
            angle = self.expr(ts, {"degrees"})
        ts.accept_word("degrees", "degree")
        return Node("rotate", no, what=what, angle=angle, absolute=False)

    def st_spin(self, ts, no):
        return self.st_rotate(ts, no)

    def st_scale(self, ts, no):
        what = ExprParser(ts, {"by", "to"}).parse_unary()
        ts.expect_word("by", "to")
        return Node("scale", no, what=what, factor=self.expr(ts))

    def st_grow(self, ts, no):
        return self.st_scale(ts, no)

    def st_resize(self, ts, no):
        what = ExprParser(ts, {"to"}).parse_unary()
        ts.expect_word("to")
        w = self.expr(ts, {"by"}); ts.expect_word("by")
        return Node("resize", no, what=what, w=w, h=self.expr(ts))

    def st_flip(self, ts, no):
        what = ExprParser(ts, {"horizontally", "vertically", "across", "sideways", "upside"}).parse_unary()
        axis = "h"
        if ts.accept_word("vertically") or ts.accept_word("upside"):
            ts.accept_word("down")
            axis = "v"
        else:
            ts.accept_word("horizontally", "sideways", "across")
        return Node("flip", no, what=what, axis=axis)

    def st_recolor(self, ts, no):
        what = ExprParser(ts, {"to"}).parse_unary()
        ts.expect_word("to")
        return Node("recolor", no, what=what, color=self.expr(ts))

    def st_paintover(self, ts, no):
        return self.st_recolor(ts, no)

    def st_export(self, ts, no):
        ts.accept_word("the")
        what = ts.name()
        ts.expect_word("to", "as", "into")
        ts.accept_word("file")
        return Node("export", no, canvas=what, path=self.expr(ts))

    def st_bring(self, ts, no):
        what = ExprParser(ts, {"to"}).parse_unary()
        ts.expect_word("to")
        ts.accept_word("the")
        where = ts.next().value
        return Node("layer", no, what=what, where="front" if where in ("front", "top") else "back")

    def st_send(self, ts, no):
        return self.st_bring(ts, no)

    def st_animate(self, ts, no):
        # animate ball to 300, 200 over 2 seconds
        what = ExprParser(ts, {"to"}).parse_unary()
        ts.expect_word("to")
        x = self.expr(ts, OPTION_WORDS | {"over", "in"}); ts.accept_op(","); y = self.expr(ts, {"over", "in"})
        ts.expect_word("over", "in")
        dur = self.expr(ts, set(TIME_UNITS))
        unit = ts.accept_word(*TIME_UNITS) or "seconds"
        return Node("animate", no, what=what, x=x, y=y, dur=dur, unit=unit)

    def st_bounce(self, ts, no):
        # bounce ball inside board  -> keeps shape in canvas by flipping its speed variables
        what = ExprParser(ts, {"inside", "in", "off", "using"}).parse_unary()
        ts.accept_word("inside", "in", "off")
        ts.accept_word("the")
        ts.accept_word("edges", "walls")
        ts.accept_word("of")
        canvas = ts.name() if not ts.at_word("using") else None
        ts.expect_word("using")
        sx = ts.name(); ts.accept_op(","); ts.accept_word("and")
        sy = ts.name()
        return Node("bounce", no, what=what, canvas=canvas, sx=sx, sy=sy)

    # ================================================================ misc
    def st_note(self, ts, no):
        return None

    def st_pass(self, ts, no):
        return Node("pass", no)

    def st_nothing(self, ts, no):
        return Node("pass", no)

    def st_debug(self, ts, no):
        return Node("whisper", no, values=self.exprs(ts))


NOT_MINE = object()

STATEMENT_ALIASES = {
    "print": "say", "write_line": "say", "tell": "say", "display": "say", "output": "say", "echo": "say",
    "shout": "say",
    "otherwise_": "if", "whenever": "when",
    "insert": "put", "append_": "append", "give_": "give", "push": "put",
    "erase": "delete", "destroy": "delete",
    "go": "move", "jump": "move", "slide": "move", "teleport": "move",
    "build": "make", "new": "make",
    "store": "remember", "keep": "remember",
    "get": "recall", "fetch_": "recall",
    "sayback": "give",
    "launch": "open", "visit": "open", "browse": "open",
    "draw_": "draw", "plot": "draw",
    "enlarge": "grow", "shrink": "scale",
}

# Some aliases need special handling: "get" can mean "recall" from memory only
# if followed by text; keep it simple.

TIME_UNITS = ("seconds", "second", "secs", "sec", "s", "milliseconds", "millisecond", "ms", "minutes", "minute", "mins", "min",
              "frames", "frame", "hours", "hour")

WIDGET_KINDS = {
    "label": "label", "text": "label", "title": "label", "heading": "heading", "header": "heading",
    "button": "button",
    "input": "input", "entry": "input", "field": "input", "box": "input", "password": "password",
    "textbox": "textbox", "textarea": "textbox", "editor": "textbox", "notes": "textbox",
    "checkbox": "checkbox", "check": "checkbox", "tickbox": "checkbox", "toggle": "checkbox", "switch": "checkbox",
    "slider": "slider", "scale": "slider",
    "dropdown": "dropdown", "choice": "dropdown", "picker": "dropdown", "combo": "dropdown", "menu_": "dropdown",
    "listbox": "listbox", "list": "listbox",
    "canvas": "canvas", "drawing": "canvas", "paper": "canvas",
    "image": "image", "picture": "image", "photo": "image",
    "progress": "progress", "progressbar": "progress", "bar": "progress",
    "spinner": "spinner", "number": "spinner",
    "panel": "panel", "frame": "panel", "group": "panel", "row": "row", "column": "panel",
    "separator": "separator", "line_": "separator", "divider": "separator",
    "radio": "radio", "option": "radio", "choices": "radio",
    "link": "link", "colorpicker": "colorpicker", "color": "colorpicker", "drop": "dropdown", "space": "space", "spacer": "space",
    "table": "table", "grid": "table", "tabs": "tabs", "tab": "tab",
}

WIDGET_OPTIONS = {
    "saying": "expr", "text": "expr", "doing": "name", "do": "name", "at": "pair", "sized": "size", "size": "size",
    "width": "expr", "height": "expr", "from": "range", "with": "expr", "color": "expr", "colour": "expr",
    "background": "expr", "foreground": "expr", "font": "expr", "bold": "flag", "tip": "expr", "placeholder": "expr",
    "image": "expr", "step": "expr", "start": "expr", "called": "name", "named": "name", "wrap": "flag",
    "columns": "list", "title": "expr", "big": "flag", "small": "flag", "hint": "expr", "value": "expr",
    "going": "expr", "options": "expr", "filling": "flag", "centered": "flag", "align": "expr", "icon": "expr",
    "readonly": "flag", "rows": "expr",
}

SHAPES = {"circle", "ellipse", "rectangle", "square", "line", "triangle", "polygon", "star", "text", "dot", "arc",
          "heart", "image", "arrow", "hexagon", "pentagon", "diamond", "path", "grid", "ring", "roundbox"}

SHAPE_ALIASES = {"oval": "ellipse", "box": "rectangle", "rect": "rectangle", "pixel": "dot", "point": "dot",
                 "words": "text", "label": "text", "picture": "image", "sprite": "image", "photo": "image",
                 "poly": "polygon", "shape": "polygon", "hex": "hexagon", "curve": "path", "lines": "path",
                 "donut": "ring", "pie": "arc", "rhombus": "diamond", "roundrect": "roundbox", "button": "roundbox"}

DRAW_OPTIONS = {
    "at": "pair", "from": "pair", "to": "pair", "size": "size", "sized": "size", "radius": "expr",
    "color": "expr", "colour": "expr", "fill": "expr", "outline": "expr", "border": "expr",
    "width": "expr", "thickness": "expr", "called": "name", "named": "name", "saying": "expr",
    "points": "expr", "font": "expr", "angle": "expr", "start": "expr", "extent": "expr",
    "file": "expr", "bold": "flag", "dashed": "flag", "smooth": "flag", "spacing": "expr", "tag": "expr",
    "corner": "expr", "hidden": "flag", "arrow": "flag",
}

OPTION_KEY = {"colour": "color", "fill": "color", "named": "called", "border": "outline", "thickness": "width",
              "titled": "title", "sized": "size", "text": "saying", "do": "doing"}


KNOWN_COMMANDS = sorted({n[3:] for n in dir(Parser) if n.startswith("st_")} | set(STATEMENT_ALIASES))
