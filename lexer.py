"""Memowrite lexer: turns one line of Memowrite into tokens.

Memowrite is written in plain English words, so the lexer is simple:
words, numbers, text in quotes, and a few symbols.
"""

from .errors import MemoError


class Token:
    __slots__ = ("kind", "value", "col")

    def __init__(self, kind, value, col):
        self.kind = kind      # WORD, NUM, STR, OP
        self.value = value
        self.col = col

    def __repr__(self):
        return f"Token({self.kind},{self.value!r})"

    def is_word(self, *words):
        return self.kind == "WORD" and self.value in words

    def is_op(self, *ops):
        return self.kind == "OP" and self.value in ops


TWO_CHAR_OPS = ("==", "!=", ">=", "<=", "<>", "**")
ONE_CHAR_OPS = "+-*/%^()[]{},:=<>&.;"

ESCAPES = {"n": "\n", "t": "\t", "\\": "\\", '"': '"', "'": "'", "{": "\x01", "}": "\x02"}


def tokenize(line, lineno=0):
    tokens = []
    i = 0
    n = len(line)
    while i < n:
        c = line[i]
        if c in " \t\r":
            i += 1
            continue
        # comments: '#' or '//' anywhere outside text
        if c == "#" or line.startswith("//", i):
            break
        if c.isdigit() or (c == "." and i + 1 < n and line[i + 1].isdigit()):
            start = i
            seen_dot = False
            while i < n and (line[i].isdigit() or (line[i] == "." and not seen_dot and i + 1 < n and line[i + 1].isdigit()) or line[i] == "_"):
                if line[i] == ".":
                    seen_dot = True
                i += 1
            raw = line[start:i].replace("_", "")
            value = float(raw) if seen_dot else int(raw)
            # allow 5px / 10ms style units to be ignored? no - keep it strict
            tokens.append(Token("NUM", value, start))
            continue
        if c.isalpha() or c == "_":
            start = i
            while i < n and (line[i].isalnum() or line[i] == "_"):
                i += 1
            word = line[start:i]
            # contractions: don't, doesn't, isn't, can't
            if i + 1 < n and line[i] == "'" and line[i + 1] == "t" and word.lower().endswith("n"):
                base = word.lower()[:-1]
                i += 2
                mapping = {"do": "does", "does": "does", "is": "is", "ca": "can", "are": "is", "wo": "will"}
                tokens.append(Token("WORD", mapping.get(base, base), start))
                tokens.append(Token("WORD", "not", start))
                continue
            tokens.append(Token("WORD", word.lower(), start))
            continue
        if c in "\"'":
            quote = c
            start = i
            i += 1
            buf = []
            closed = False
            depth = 0
            while i < n:
                ch = line[i]
                if depth > 0 and ch in "\"'":
                    # text inside {...} inside text: "{pet["age"]}"
                    j = line.find(ch, i + 1)
                    if j >= 0 and line.find("}", j + 1) >= 0:
                        buf.append(line[i:j + 1])
                        i = j + 1
                        continue
                if ch == "{":
                    if line.startswith("{{", i) and depth == 0:
                        buf.append("{{")
                        i += 2
                        continue
                    depth += 1
                elif ch == "}" and depth > 0:
                    depth -= 1
                if ch == "\\" and i + 1 < n:
                    nxt = line[i + 1]
                    buf.append(ESCAPES.get(nxt, "\\" + nxt))
                    i += 2
                    continue
                if ch == quote:
                    closed = True
                    i += 1
                    break
                buf.append(ch)
                i += 1
            if not closed:
                raise MemoError("This text is missing its closing quote mark " + quote, lineno)
            tokens.append(Token("STR", "".join(buf), start))
            continue
        two = line[i:i + 2]
        if two in TWO_CHAR_OPS:
            tokens.append(Token("OP", {"<>": "!=", "**": "^"}.get(two, two), i))
            i += 2
            continue
        if c in ONE_CHAR_OPS:
            tokens.append(Token("OP", c, i))
            i += 1
            continue
        raise MemoError(f"I don't understand the symbol '{c}'", lineno)
    return tokens


def is_comment_line(stripped):
    low = stripped.lower()
    return (not stripped) or low.startswith("#") or low.startswith("//") or low == "note" or low.startswith("note ") or low.startswith("note:")
