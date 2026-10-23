"""Fancy text for console programs: banners, boxes, tables, bars."""

import textwrap

from ..values import to_text, to_number, is_number

# A small 5-line block font for banners
FONT = {
    "A": [" ### ", "#   #", "#####", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#### ", "#   #", "#### "],
    "C": [" ####", "#    ", "#    ", "#    ", " ####"],
    "D": ["#### ", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#### ", "#    ", "#####"],
    "F": ["#####", "#    ", "#### ", "#    ", "#    "],
    "G": [" ####", "#    ", "#  ##", "#   #", " ### "],
    "H": ["#   #", "#   #", "#####", "#   #", "#   #"],
    "I": ["#####", "  #  ", "  #  ", "  #  ", "#####"],
    "J": ["#####", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "###  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#### ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#### ", "#  # ", "#   #"],
    "S": [" ####", "#    ", " ### ", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "# # #", "## ##", "#   #"],
    "X": ["#   #", " # # ", "  #  ", " # # ", "#   #"],
    "Y": ["#   #", " # # ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "   # ", "  #  ", " #   ", "#####"],
    "0": [" ### ", "#  ##", "# # #", "##  #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "  ## ", " #   ", "#####"],
    "3": ["#### ", "    #", " ### ", "    #", "#### "],
    "4": ["#   #", "#   #", "#####", "    #", "    #"],
    "5": ["#####", "#    ", "#### ", "    #", "#### "],
    "6": [" ### ", "#    ", "#### ", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", "  #  "],
    "8": [" ### ", "#   #", " ### ", "#   #", " ### "],
    "9": [" ### ", "#   #", " ####", "    #", " ### "],
    " ": ["     ", "     ", "     ", "     ", "     "],
    "!": ["  #  ", "  #  ", "  #  ", "     ", "  #  "],
    "?": [" ### ", "#   #", "  ## ", "     ", "  #  "],
    ".": ["     ", "     ", "     ", "     ", "  #  "],
    "-": ["     ", "     ", "#####", "     ", "     "],
    ":": ["     ", "  #  ", "     ", "  #  ", "     "],
    "'": ["  #  ", "  #  ", "     ", "     ", "     "],
}


def banner(text, char="#"):
    rows = ["", "", "", "", ""]
    for c in to_text(text).upper():
        glyph = FONT.get(c, FONT["?"])
        for i in range(5):
            rows[i] += glyph[i].replace("#", char or "#") + " "
    return "\n".join(r.rstrip() for r in rows)


def boxed(text, style="single"):
    lines = to_text(text).splitlines() or [""]
    w = max(len(l) for l in lines)
    chars = {"single": "┌┐└┘─│", "double": "╔╗╚╝═║", "round": "╭╮╰╯─│", "plain": "++++-|", "stars": "******"}.get(style, "┌┐└┘─│")
    tl, tr, bl, br, h, v = chars
    out = [tl + h * (w + 2) + tr]
    out += [f"{v} {l.ljust(w)} {v}" for l in lines]
    out.append(bl + h * (w + 2) + br)
    return "\n".join(out)


def table(rows, headers=None):
    rows = [r if isinstance(r, list) else [r] for r in rows]
    if rows and all(isinstance(r, dict) for r in rows):
        pass
    if headers is None and rows and isinstance(rows[0], list):
        data = rows
    else:
        data = ([headers] if headers else []) + rows
    data = [[to_text(c) for c in r] for r in data]
    if not data:
        return ""
    cols = max(len(r) for r in data)
    for r in data:
        r += [""] * (cols - len(r))
    widths = [max(len(r[i]) for r in data) for i in range(cols)]
    line = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    out = [line]
    for i, r in enumerate(data):
        out.append("| " + " | ".join(c.ljust(widths[j]) if not _numeric(c) else c.rjust(widths[j]) for j, c in enumerate(r)) + " |")
        if i == 0 and headers is not None:
            out.append(line.replace("-", "="))
    out.append(line)
    return "\n".join(out)


def _numeric(c):
    try:
        float(c)
        return True
    except ValueError:
        return False


def bar(value, maximum=100, width=20):
    v = to_number(value)
    m = to_number(maximum) or 1
    w = int(to_number(width))
    filled = int(round(max(0, min(1, v / m)) * w))
    return "[" + "#" * filled + "-" * (w - filled) + f"] {int(round(v / m * 100))}%"


def extra_builtins(it):
    def book_table(books):
        if books and all(isinstance(b, dict) for b in books):
            headers = []
            for b in books:
                for k in b:
                    if k not in headers:
                        headers.append(k)
            return table([[b.get(h, "") for h in headers] for b in books], headers)
        return table(books)

    return {
        "banner": (lambda t, c="#": banner(t, to_text(c)), 1, 2, "Big block letters"),
        "box": (lambda t, s="single": boxed(t, to_text(s)), 1, 2, "Draws a box around text"),
        "table": (lambda rows, headers=None: book_table(rows) if headers is None else table(rows, headers), 1, 2, "Makes a text table from a list of lists"),
        "progress_bar": (bar, 1, 3, "A text progress bar like [#####-----] 50%"),
        "wrap": (lambda t, w=60: "\n".join(textwrap.wrap(to_text(t), int(to_number(w)))), 1, 2, "Wraps long text into lines"),
        "indent": (lambda t, n=4: textwrap.indent(to_text(t), " " * int(to_number(n))), 1, 2, "Indents every line"),
        "underline": (lambda t, c="-": to_text(t) + "\n" + to_text(c)[:1] * len(to_text(t)), 1, 2, "Text with a line under it"),
        "stars": (lambda n: "*" * int(to_number(n)), 1, 1, "A row of stars"),
    }
