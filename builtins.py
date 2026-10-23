"""The Memowrite standard library of built-in tasks.

Every built-in can be used two ways:
    length("hello")        or      length of "hello"
"""

import datetime
import json
import math
import os
import re
import string
import time

from ..errors import MemoError
from ..values import (Builtin, Task, to_text, type_name, truthy, is_number, to_number, tidy_number,
                      looks_like_number, same)

REGISTRY = []   # (names, min, max, doc, factory)


def builtin(names, min_args=0, max_args=None, doc=""):
    if isinstance(names, str):
        names = [names]

    def deco(fn):
        REGISTRY.append((names, min_args, max_args, doc, fn))
        return fn
    return deco


def make_builtins(interp):
    table = {}
    for names, lo, hi, doc, fn in REGISTRY:
        bound = _bind(fn, interp)
        b = Builtin(names[0], bound, doc, lo, hi)
        for n in names:
            table[n] = b
    from . import graphics, files, system, textplus, gui
    for mod in (graphics, files, system, textplus, gui):
        if hasattr(mod, "extra_builtins"):
            for name, (fn, lo, hi, doc) in mod.extra_builtins(interp).items():
                table[name] = Builtin(name, fn, doc, lo, hi)
    return table


def _bind(fn, interp):
    def call(*args):
        return fn(interp, *args)
    call.__name__ = fn.__name__
    return call


def num(v):
    return to_number(v)


def need_list(v, what="this"):
    if isinstance(v, list):
        return v
    if isinstance(v, (tuple, set)):
        return list(v)
    if isinstance(v, dict):
        return list(v.values())
    if isinstance(v, str):
        return list(v)
    raise MemoError(f"I needed a list but {what} is {type_name(v)}")


# =================================================================== maths

@builtin(["sqrt", "squareroot", "root"], 1, 1, "Square root of a number")
def _sqrt(it, x):
    x = num(x)
    if x < 0:
        raise MemoError("You can't take the square root of a negative number")
    return tidy_number(math.sqrt(x))


@builtin(["power", "pow"], 2, 2, "power(2, 3) is 8")
def _power(it, a, b):
    return tidy_number(num(a) ** num(b))


@builtin(["abs", "absolute", "positive"], 1, 1, "Makes a number positive")
def _abs(it, x):
    return tidy_number(abs(num(x)))


@builtin(["round", "rounded"], 1, 2, "round(3.7) is 4, round(3.14159, 2) is 3.14")
def _round(it, x, places=0):
    x = num(x)
    places = int(num(places))
    if places <= 0:
        return int(math.floor(x + 0.5)) if x >= 0 else -int(math.floor(-x + 0.5))
    factor = 10 ** places
    return tidy_number(math.floor(x * factor + 0.5) / factor)


@builtin(["floor", "rounddown"], 1, 1, "Rounds down")
def _floor(it, x):
    return int(math.floor(num(x)))


@builtin(["ceiling", "ceil", "roundup"], 1, 1, "Rounds up")
def _ceil(it, x):
    return int(math.ceil(num(x)))


@builtin(["whole", "integer", "int", "wholenumber"], 1, 1, "Drops the decimals")
def _int(it, x):
    if isinstance(x, str) and not looks_like_number(x):
        raise MemoError(f"'{x}' is not a number")
    return int(num(x))


@builtin(["number", "tonumber", "num"], 1, 1, "Turns text into a number")
def _number(it, x):
    if isinstance(x, str) and not looks_like_number(x):
        raise MemoError(f"'{x}' is not a number")
    return num(x)


@builtin(["sin", "sine"], 1, 1, "Sine of an angle in degrees")
def _sin(it, x):
    return tidy_number(round(math.sin(math.radians(num(x))), 12))


@builtin(["cos", "cosine"], 1, 1, "Cosine of an angle in degrees")
def _cos(it, x):
    return tidy_number(round(math.cos(math.radians(num(x))), 12))


@builtin(["tan", "tangent"], 1, 1, "Tangent of an angle in degrees")
def _tan(it, x):
    return tidy_number(round(math.tan(math.radians(num(x))), 12))


@builtin(["asin", "arcsin"], 1, 1, "Angle (degrees) whose sine is x")
def _asin(it, x):
    return tidy_number(math.degrees(math.asin(num(x))))


@builtin(["acos", "arccos"], 1, 1, "Angle (degrees) whose cosine is x")
def _acos(it, x):
    return tidy_number(math.degrees(math.acos(num(x))))


@builtin(["atan", "arctan"], 1, 2, "Angle (degrees) of a slope, atan(y, x) also works")
def _atan(it, y, x=None):
    if x is None:
        return tidy_number(math.degrees(math.atan(num(y))))
    return tidy_number(math.degrees(math.atan2(num(y), num(x))))


@builtin(["log", "logarithm"], 1, 2, "Logarithm (base 10 by default)")
def _log(it, x, base=10):
    return tidy_number(math.log(num(x), num(base)))


@builtin(["ln", "naturallog"], 1, 1, "Natural logarithm")
def _ln(it, x):
    return tidy_number(math.log(num(x)))


@builtin(["exp"], 1, 1, "e to the power of x")
def _exp(it, x):
    return tidy_number(math.exp(num(x)))


@builtin(["e"], 0, 0, "The number e")
def _e(it):
    return math.e


@builtin(["max", "biggest", "largest", "highest"], 1, None, "The biggest value")
def _max(it, *args):
    vals = need_list(args[0]) if len(args) == 1 else list(args)
    if not vals:
        return None
    return max(vals, key=lambda v: num(v) if (is_number(v) or looks_like_number(v)) else 0)


@builtin(["min", "smallest", "lowest", "least"], 1, None, "The smallest value")
def _min(it, *args):
    vals = need_list(args[0]) if len(args) == 1 else list(args)
    if not vals:
        return None
    return min(vals, key=lambda v: num(v) if (is_number(v) or looks_like_number(v)) else 0)


@builtin(["sum", "total", "add_up"], 1, None, "Adds up all the numbers")
def _sum(it, *args):
    vals = need_list(args[0]) if len(args) == 1 else list(args)
    return tidy_number(sum(num(v) for v in vals))


@builtin(["average", "mean"], 1, None, "The average of numbers")
def _avg(it, *args):
    vals = need_list(args[0]) if len(args) == 1 else list(args)
    if not vals:
        return 0
    return tidy_number(sum(num(v) for v in vals) / len(vals))


@builtin(["median", "middle"], 1, 1, "The middle value of a list of numbers")
def _median(it, lst):
    vals = sorted(num(v) for v in need_list(lst))
    if not vals:
        return 0
    n = len(vals)
    return tidy_number(vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2)


@builtin(["clamp", "limit", "keep_between"], 3, 3, "clamp(x, low, high) keeps x between low and high")
def _clamp(it, x, lo, hi):
    return tidy_number(max(num(lo), min(num(hi), num(x))))


@builtin(["lerp", "mix", "blend"], 3, 3, "lerp(a, b, 0.5) is halfway between a and b")
def _lerp(it, a, b, t):
    return tidy_number(num(a) + (num(b) - num(a)) * num(t))


@builtin(["distance"], 4, 4, "distance(x1, y1, x2, y2)")
def _distance(it, x1, y1, x2, y2):
    return tidy_number(math.hypot(num(x2) - num(x1), num(y2) - num(y1)))


@builtin(["angle_between", "direction"], 4, 4, "Angle in degrees from point 1 to point 2")
def _angle(it, x1, y1, x2, y2):
    return tidy_number(math.degrees(math.atan2(num(y2) - num(y1), num(x2) - num(x1))))


@builtin(["is_prime", "prime"], 1, 1, "Is the number prime?")
def _prime(it, n):
    n = int(num(n))
    if n < 2:
        return False
    for d in range(2, int(n ** 0.5) + 1):
        if n % d == 0:
            return False
    return True


@builtin(["factorial"], 1, 1, "5 factorial is 120")
def _fact(it, n):
    return math.factorial(int(num(n)))


@builtin(["gcd", "greatest_common_divisor"], 2, 2, "Greatest common divisor")
def _gcd(it, a, b):
    return math.gcd(int(num(a)), int(num(b)))


@builtin(["lcm"], 2, 2, "Least common multiple")
def _lcm(it, a, b):
    a, b = int(num(a)), int(num(b))
    return abs(a * b) // math.gcd(a, b) if a and b else 0


@builtin(["sign"], 1, 1, "-1, 0 or 1")
def _sign(it, x):
    x = num(x)
    return (x > 0) - (x < 0)


@builtin(["percent", "percentage"], 2, 2, "percent(25, 200) is 12.5")
def _percent(it, part, whole):
    return tidy_number(num(part) / num(whole) * 100) if num(whole) else 0


@builtin(["radians"], 1, 1, "Degrees to radians")
def _rad(it, x):
    return math.radians(num(x))


@builtin(["degrees"], 1, 1, "Radians to degrees")
def _deg(it, x):
    return tidy_number(math.degrees(num(x)))


@builtin(["fibonacci", "fib"], 1, 1, "The n-th Fibonacci number")
def _fib(it, n):
    a, b = 0, 1
    for _ in range(int(num(n))):
        a, b = b, a + b
    return a


@builtin(["binary"], 1, 1, "A number written in binary")
def _bin(it, n):
    return bin(int(num(n)))[2:]


@builtin(["hex", "hexadecimal"], 1, 1, "A number written in hexadecimal")
def _hex(it, n):
    return hex(int(num(n)))[2:].upper()


@builtin(["from_binary"], 1, 1, "Binary text to a number")
def _frombin(it, t):
    return int(to_text(t), 2)


@builtin(["from_hex"], 1, 1, "Hexadecimal text to a number")
def _fromhex(it, t):
    return int(to_text(t).lstrip("#"), 16)


@builtin(["is_even", "even"], 1, 1, "Is the number even?")
def _even(it, x):
    return num(x) % 2 == 0


@builtin(["is_odd", "odd"], 1, 1, "Is the number odd?")
def _odd(it, x):
    return num(x) % 2 == 1


@builtin(["format_number", "commas", "with_commas"], 1, 2, "1234567 -> 1,234,567")
def _commas(it, x, places=None):
    x = num(x)
    if places is None:
        return f"{x:,}" if isinstance(x, int) else f"{x:,.2f}"
    return f"{x:,.{int(num(places))}f}"


@builtin(["money", "currency"], 1, 2, "money(5) -> 5.00")
def _money(it, x, symbol=""):
    return f"{to_text(symbol)}{num(x):,.2f}"


# =================================================================== random

@builtin(["random", "random_number", "rand"], 0, 2, "random(1, 6) gives a whole number from 1 to 6")
def _random(it, a=None, b=None):
    r = it.random
    if a is None:
        return r.random()
    if b is None:
        a, b = 1, a
    a, b = num(a), num(b)
    if isinstance(a, int) and isinstance(b, int):
        return r.randint(min(a, b), max(a, b))
    return r.uniform(a, b)


@builtin(["pick", "choose", "random_item", "any_of"], 1, None, "A random item from a list")
def _pick(it, *args):
    vals = need_list(args[0]) if len(args) == 1 else list(args)
    if not vals:
        raise MemoError("I can't pick from an empty list")
    return it.random.choice(vals)


@builtin(["shuffled"], 1, 1, "A shuffled copy of a list")
def _shuffled(it, lst):
    c = list(need_list(lst))
    it.random.shuffle(c)
    return c


@builtin(["chance", "coin_flip", "flip_coin"], 0, 1, "chance(30) is yes 30% of the time")
def _chance(it, pct=50):
    return it.random.random() * 100 < num(pct)


@builtin(["dice", "roll", "roll_dice"], 0, 1, "Roll a dice (6 sides by default)")
def _dice(it, sides=6):
    return it.random.randint(1, int(num(sides)))


@builtin(["seed", "set_seed"], 1, 1, "Makes random numbers repeatable")
def _seed(it, s):
    it.random.seed(s)
    return None


@builtin(["random_color", "random_colour"], 0, 0, "A random bright color")
def _randcolor(it):
    import colorsys
    r, g, b = colorsys.hsv_to_rgb(it.random.random(), 0.65 + it.random.random() * 0.35, 0.8 + it.random.random() * 0.2)
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


@builtin(["random_name"], 0, 0, "A random friendly name")
def _randname(it):
    first = ["Ada", "Max", "Luna", "Leo", "Mia", "Noah", "Ella", "Finn", "Zoe", "Oscar", "Ivy", "Theo", "Nora", "Felix", "Ruby"]
    return it.random.choice(first)


@builtin(["random_word"], 0, 0, "A random English word")
def _randword(it):
    words = ["apple", "river", "rocket", "garden", "silver", "dragon", "planet", "pencil", "castle", "ocean", "thunder",
             "candle", "forest", "mirror", "puzzle", "window", "guitar", "tiger", "cloud", "island"]
    return it.random.choice(words)


@builtin(["uuid", "unique_id"], 0, 0, "A unique id text")
def _uuid(it):
    import uuid
    return str(uuid.uuid4())


@builtin(["password", "make_password", "random_password"], 0, 1, "A random strong password")
def _password(it, length=12):
    import secrets
    chars = string.ascii_letters + string.digits + "!@#$%&*?"
    return "".join(secrets.choice(chars) for _ in range(int(num(length))))


# =================================================================== text

@builtin(["text", "totext", "string", "str"], 1, 1, "Turns anything into text")
def _text(it, v):
    return to_text(v)


@builtin(["length", "len", "size", "count_of", "how_many"], 1, 1, "How many items or letters")
def _length(it, v):
    if v is None:
        return 0
    if isinstance(v, (str, list, dict)):
        return len(v)
    if is_number(v):
        return len(to_text(v))
    if hasattr(v, "length"):
        return v.length()
    raise MemoError(f"{type_name(v)} has no length")


@builtin(["uppercase", "upper", "capitals", "shout_text"], 1, 1, "HELLO")
def _upper(it, t):
    return to_text(t).upper()


@builtin(["lowercase", "lower"], 1, 1, "hello")
def _lower(it, t):
    return to_text(t).lower()


@builtin(["titlecase", "title_case", "capitalize_words"], 1, 1, "Hello World")
def _title(it, t):
    return to_text(t).title()


@builtin(["capitalize", "capitalise", "sentence_case"], 1, 1, "Hello world")
def _cap(it, t):
    t = to_text(t)
    return t[:1].upper() + t[1:]


@builtin(["trim", "trimmed", "strip", "tidy"], 1, 1, "Removes spaces at the start and end")
def _trim(it, t):
    return to_text(t).strip()


@builtin(["reversed", "reverse", "backwards"], 1, 1, "olleh / reversed list")
def _reversed(it, v):
    if isinstance(v, list):
        return list(reversed(v))
    return to_text(v)[::-1]


@builtin(["split", "split_text"], 1, 2, "split(\"a,b\", \",\") gives [a, b]")
def _split(it, t, sep=None):
    t = to_text(t)
    if sep is None:
        return t.split()
    sep = to_text(sep)
    if sep == "":
        return list(t)
    return t.split(sep)


@builtin(["join", "joined", "glue"], 1, 2, "join([a, b], \", \") gives \"a, b\"")
def _join(it, lst, sep=""):
    return to_text(sep).join(to_text(x) for x in need_list(lst))


@builtin(["replace", "replaced", "swap_text"], 3, 3, "replace(text, \"old\", \"new\")")
def _replace(it, t, a, b):
    return to_text(t).replace(to_text(a), to_text(b))


@builtin(["contains", "has_text", "includes"], 2, 2, "Does the text or list contain something?")
def _contains(it, a, b):
    return it.compare("contains", a, b)


@builtin(["starts_with", "startswith", "begins_with"], 2, 2, "Does the text start with ...?")
def _sw(it, a, b):
    return to_text(a).lower().startswith(to_text(b).lower())


@builtin(["ends_with", "endswith"], 2, 2, "Does the text end with ...?")
def _ew(it, a, b):
    return to_text(a).lower().endswith(to_text(b).lower())


@builtin(["find", "position", "position_of", "index_of", "where_is"], 2, 2, "Position (from 1) of something, or 0")
def _find(it, hay, needle):
    if isinstance(hay, list):
        for i, x in enumerate(hay, start=1):
            if same(x, needle):
                return i
        return 0
    return to_text(hay).lower().find(to_text(needle).lower()) + 1


@builtin(["count", "count_of_text", "occurrences"], 2, 2, "How many times something appears")
def _count(it, hay, needle):
    if isinstance(hay, list):
        return sum(1 for x in hay if same(x, needle))
    return to_text(hay).lower().count(to_text(needle).lower())


@builtin(["part", "middle_of", "substring", "slice"], 2, 3, "part(\"hello\", 2, 4) gives \"ell\"")
def _part(it, t, start, end=None):
    return it.get_slice(t, start, end)


@builtin(["left", "first_letters"], 2, 2, "left(\"hello\", 2) gives \"he\"")
def _left(it, t, n):
    return to_text(t)[:int(num(n))]


@builtin(["right", "last_letters"], 2, 2, "right(\"hello\", 2) gives \"lo\"")
def _right(it, t, n):
    n = int(num(n))
    return to_text(t)[-n:] if n > 0 else ""


@builtin(["repeat_text", "repeated"], 2, 2, "repeat_text(\"ha\", 3) gives \"hahaha\"")
def _rep(it, t, n):
    return to_text(t) * int(num(n))


@builtin(["words"], 1, 1, "The words in a text as a list")
def _words(it, t):
    return re.findall(r"[\w'-]+", to_text(t))


@builtin(["lines"], 1, 1, "The lines in a text as a list")
def _lines(it, t):
    return to_text(t).splitlines()


@builtin(["letters", "characters", "chars"], 1, 1, "The letters in a text as a list")
def _letters(it, t):
    return list(to_text(t))


@builtin(["word_at"], 2, 2, "word 2 of a sentence")
def _wordat(it, t, n):
    return it.get_index(_words(it, t), n)


@builtin(["line_at"], 2, 2, "line 2 of a text")
def _lineat(it, t, n):
    return it.get_index(to_text(t).splitlines(), n)


@builtin(["first_word"], 1, 1, "The first word")
def _fw(it, t):
    w = _words(it, t)
    return w[0] if w else ""


@builtin(["last_word"], 1, 1, "The last word")
def _lw(it, t):
    w = _words(it, t)
    return w[-1] if w else ""


@builtin(["first_line"], 1, 1, "The first line")
def _fl(it, t):
    l = to_text(t).splitlines()
    return l[0] if l else ""


@builtin(["last_line"], 1, 1, "The last line")
def _ll(it, t):
    l = to_text(t).splitlines()
    return l[-1] if l else ""


@builtin(["is_number", "isnumber", "is_numeric"], 1, 1, "Is this a number (or text that is a number)?")
def _isnum(it, v):
    return is_number(v) or looks_like_number(v)


@builtin(["is_letter", "is_letters", "is_alpha"], 1, 1, "Is this text only letters?")
def _isalpha(it, v):
    return to_text(v).isalpha()


@builtin(["is_upper"], 1, 1, "Is the text in capitals?")
def _isupper(it, v):
    return to_text(v).isupper()


@builtin(["is_lower"], 1, 1, "Is the text in small letters?")
def _islower(it, v):
    return to_text(v).islower()


@builtin(["is_vowel"], 1, 1, "Is the letter a vowel?")
def _isvowel(it, v):
    return to_text(v).lower() in ("a", "e", "i", "o", "u")


@builtin(["is_palindrome", "palindrome"], 1, 1, "Is it the same backwards?")
def _ispal(it, v):
    t = re.sub(r"[^a-z0-9]", "", to_text(v).lower())
    return t == t[::-1]


@builtin(["code_of", "char_code", "ascii"], 1, 1, "The number code of a letter")
def _ord(it, c):
    c = to_text(c)
    return ord(c[0]) if c else 0


@builtin(["letter_of_code", "char", "from_code"], 1, 1, "The letter with a number code")
def _chr(it, n):
    return chr(int(num(n)))


@builtin(["pad_left", "pad"], 2, 3, "pad_left(\"7\", 3, \"0\") gives \"007\"")
def _padl(it, t, width, fill=" "):
    return to_text(t).rjust(int(num(width)), (to_text(fill) or " ")[0])


@builtin(["pad_right"], 2, 3, "pad_right(\"hi\", 5) gives \"hi   \"")
def _padr(it, t, width, fill=" "):
    return to_text(t).ljust(int(num(width)), (to_text(fill) or " ")[0])


@builtin(["center", "centre"], 2, 3, "Centers text in a width")
def _center(it, t, width, fill=" "):
    return to_text(t).center(int(num(width)), (to_text(fill) or " ")[0])


@builtin(["remove_spaces", "nospaces"], 1, 1, "Removes all spaces")
def _nosp(it, t):
    return re.sub(r"\s+", "", to_text(t))


@builtin(["only_letters"], 1, 1, "Keeps only the letters")
def _onlylet(it, t):
    return "".join(c for c in to_text(t) if c.isalpha())


@builtin(["only_digits", "only_numbers"], 1, 1, "Keeps only the digits")
def _onlydig(it, t):
    return "".join(c for c in to_text(t) if c.isdigit())


@builtin(["count_words", "word_count"], 1, 1, "How many words")
def _cw(it, t):
    return len(_words(it, t))


@builtin(["count_vowels"], 1, 1, "How many vowels")
def _cv(it, t):
    return sum(1 for c in to_text(t).lower() if c in "aeiou")


@builtin(["slug", "url_name"], 1, 1, "\"Hello World!\" -> \"hello-world\"")
def _slug(it, t):
    return re.sub(r"[^a-z0-9]+", "-", to_text(t).lower()).strip("-")


@builtin(["caesar", "secret_code", "encode_caesar"], 1, 2, "Shifts letters to make a secret code")
def _caesar(it, t, shift=3):
    shift = int(num(shift))
    out = []
    for c in to_text(t):
        if c.isalpha():
            base = ord("A") if c.isupper() else ord("a")
            out.append(chr((ord(c) - base + shift) % 26 + base))
        else:
            out.append(c)
    return "".join(out)


@builtin(["decode_caesar"], 1, 2, "Undoes caesar()")
def _decaesar(it, t, shift=3):
    return _caesar(it, t, -int(num(shift)))


@builtin(["morse", "to_morse"], 1, 1, "Turns text into Morse code")
def _morse(it, t):
    table = {"a": ".-", "b": "-...", "c": "-.-.", "d": "-..", "e": ".", "f": "..-.", "g": "--.", "h": "....", "i": "..",
             "j": ".---", "k": "-.-", "l": ".-..", "m": "--", "n": "-.", "o": "---", "p": ".--.", "q": "--.-", "r": ".-.",
             "s": "...", "t": "-", "u": "..-", "v": "...-", "w": ".--", "x": "-..-", "y": "-.--", "z": "--..",
             "0": "-----", "1": ".----", "2": "..---", "3": "...--", "4": "....-", "5": ".....", "6": "-....",
             "7": "--...", "8": "---..", "9": "----.", " ": "/"}
    return " ".join(table.get(c, "?") for c in to_text(t).lower())


@builtin(["matches", "matches_pattern", "regex_match"], 2, 2, "Does text match a pattern (regular expression)?")
def _matches(it, t, pattern):
    return re.search(to_text(pattern), to_text(t)) is not None


@builtin(["find_all", "regex_find"], 2, 2, "All pieces of text matching a pattern")
def _findall(it, t, pattern):
    return re.findall(to_text(pattern), to_text(t))


@builtin(["is_email", "looks_like_email"], 1, 1, "Does it look like an email address?")
def _isemail(it, t):
    return re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", to_text(t)) is not None


@builtin(["format", "fill_in"], 1, None, "format(\"{} has {}\", \"Bob\", 3)")
def _format(it, template, *args):
    out = to_text(template)
    for a in args:
        out = out.replace("{}", to_text(a), 1)
    return out


@builtin(["spell_number", "number_to_words", "in_words"], 1, 1, "42 -> forty-two")
def _spell(it, n):
    n = int(num(n))
    ones = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve",
            "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]

    def say(x):
        if x < 0:
            return "minus " + say(-x)
        if x < 20:
            return ones[x]
        if x < 100:
            return tens[x // 10] + ("" if x % 10 == 0 else "-" + ones[x % 10])
        if x < 1000:
            return ones[x // 100] + " hundred" + ("" if x % 100 == 0 else " and " + say(x % 100))
        for size, word in ((10 ** 9, "billion"), (10 ** 6, "million"), (1000, "thousand")):
            if x >= size:
                rest = x % size
                return say(x // size) + " " + word + ("" if rest == 0 else (" and " if rest < 100 else " ") + say(rest))
    return say(n)


@builtin(["ordinal"], 1, 1, "1 -> 1st, 2 -> 2nd")
def _ordinal(it, n):
    n = int(num(n))
    suffix = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


@builtin(["plural"], 2, 3, "plural(3, \"cat\") -> \"3 cats\"")
def _plural(it, n, word, many=None):
    n = num(n)
    w = to_text(word)
    if n == 1:
        return f"1 {w}"
    if many is not None:
        return f"{to_text(n)} {to_text(many)}"
    if w.endswith(("s", "x", "ch", "sh")):
        p = w + "es"
    elif w.endswith("y") and len(w) > 1 and w[-2] not in "aeiou":
        p = w[:-1] + "ies"
    else:
        p = w + "s"
    return f"{to_text(n)} {p}"


# =================================================================== lists

@builtin(["list", "tolist", "make_list"], 0, None, "list(1, 2, 3) or list of a text")
def _list(it, *args):
    if len(args) == 1:
        v = args[0]
        if isinstance(v, str):
            return list(v)
        if isinstance(v, dict):
            return [[k, x] for k, x in v.items()]
        if isinstance(v, list):
            return list(v)
        if hasattr(v, "items_list"):
            return v.items_list()
    return list(args)


@builtin(["range", "numbers", "numbers_from"], 1, 3, "range(1, 5) gives [1, 2, 3, 4, 5]")
def _range(it, a, b=None, step=1):
    if b is None:
        a, b = 1, a
    a, b, step = num(a), num(b), num(step)
    if step == 0:
        raise MemoError("The step can't be 0")
    out = []
    x = a
    if b < a and step > 0:
        step = -step
    while (x <= b + 1e-9) if step > 0 else (x >= b - 1e-9):
        out.append(tidy_number(x))
        x += step
        if len(out) > 10_000_000:
            raise MemoError("That range is far too big")
    return out


@builtin(["first"], 1, 1, "The first item")
def _first(it, v):
    seq = v if isinstance(v, (list, str)) else need_list(v)
    return seq[0] if seq else None


@builtin(["last"], 1, 1, "The last item")
def _last(it, v):
    seq = v if isinstance(v, (list, str)) else need_list(v)
    return seq[-1] if seq else None


@builtin(["rest", "all_but_first"], 1, 1, "Everything except the first item")
def _rest(it, v):
    return v[1:]


@builtin(["sorted", "sort_list"], 1, 2, "A sorted copy of a list")
def _sorted(it, lst, backwards=False):
    from ..interpreter import sort_key
    return sorted(need_list(lst), key=sort_key, reverse=truthy(backwards))


@builtin(["unique", "no_duplicates", "distinct"], 1, 1, "The list without repeated items")
def _unique(it, lst):
    out = []
    for x in need_list(lst):
        if not any(same(x, y, True) for y in out):
            out.append(x)
    return out


@builtin(["flatten"], 1, 1, "Turns a list of lists into one list")
def _flatten(it, lst):
    out = []
    for x in need_list(lst):
        if isinstance(x, list):
            out.extend(_flatten(it, x))
        else:
            out.append(x)
    return out


@builtin(["copy", "copy_of", "duplicate"], 1, 1, "A copy of a list or book")
def _copy(it, v):
    import copy
    if isinstance(v, (list, dict)):
        return copy.deepcopy(v)
    if hasattr(v, "clone"):
        return v.clone()
    return v


@builtin(["keys", "names_in", "fields"], 1, 1, "The keys of a book")
def _keys(it, v):
    if isinstance(v, dict):
        return list(v.keys())
    if hasattr(v, "fields") and isinstance(getattr(v, "fields"), dict):
        return list(v.fields.keys())
    raise MemoError("Only books have keys")


@builtin(["values"], 1, 1, "The values of a book")
def _values(it, v):
    if isinstance(v, dict):
        return list(v.values())
    raise MemoError("Only books have values")


@builtin(["has_key", "has"], 2, 2, "Does the book have this key?")
def _haskey(it, book, key):
    if isinstance(book, dict):
        return any(same(k, key) for k in book)
    return it.compare("contains", book, key)


@builtin(["get_or", "lookup", "get"], 2, 3, "get(book, key, default)")
def _get(it, obj, key, default=None):
    v = it.get_index(obj, key) if isinstance(obj, dict) else (it.get_index(obj, key) if isinstance(obj, (list, str)) and is_number(key) and 0 < abs(int(key)) <= len(obj) else None)
    return default if v is None else v


@builtin(["take", "first_n"], 2, 2, "take(list, 3) - the first 3 items")
def _take(it, lst, n):
    return lst[:int(num(n))]


@builtin(["drop", "skip_n"], 2, 2, "drop(list, 2) - all but the first 2 items")
def _drop(it, lst, n):
    return lst[int(num(n)):]


@builtin(["zip", "pair_up"], 2, 2, "Pairs two lists together")
def _zip(it, a, b):
    return [[x, y] for x, y in zip(need_list(a), need_list(b))]


@builtin(["chunk", "groups_of"], 2, 2, "Splits a list into groups of n")
def _chunk(it, lst, n):
    n = max(1, int(num(n)))
    lst = need_list(lst)
    return [lst[i:i + n] for i in range(0, len(lst), n)]


@builtin(["fill_list", "list_of"], 2, 2, "fill_list(3, 0) gives [0, 0, 0]")
def _filllist(it, n, value):
    import copy
    return [copy.deepcopy(value) for _ in range(int(num(n)))]


@builtin(["grid_of", "make_grid"], 3, 3, "grid_of(rows, columns, value) - a list of lists")
def _grid(it, rows, cols, value):
    import copy
    return [[copy.deepcopy(value) for _ in range(int(num(cols)))] for _ in range(int(num(rows)))]


@builtin(["map", "each_changed", "transform"], 2, 2, "map(list, task) runs a task on every item")
def _map(it, lst, fn):
    return [it.call(fn, [x]) for x in need_list(lst)]


@builtin(["filter", "keep", "only", "select"], 2, 2, "filter(list, task) keeps items where the task gives yes")
def _filter(it, lst, fn):
    return [x for x in need_list(lst) if truthy(it.call(fn, [x]))]


@builtin(["reduce", "combine", "fold"], 3, 3, "reduce(list, task, start)")
def _reduce(it, lst, fn, start):
    acc = start
    for x in need_list(lst):
        acc = it.call(fn, [acc, x])
    return acc


@builtin(["any", "any_true"], 1, 2, "Is any item true (or true for the task)?")
def _any(it, lst, fn=None):
    return any(truthy(it.call(fn, [x]) if fn is not None else x) for x in need_list(lst))


@builtin(["all", "all_true", "every_one"], 1, 2, "Are all items true (or true for the task)?")
def _all(it, lst, fn=None):
    return all(truthy(it.call(fn, [x]) if fn is not None else x) for x in need_list(lst))


@builtin(["sort_by"], 2, 3, "sort_by(list, \"age\") sorts books by a field")
def _sortby(it, lst, key, backwards=False):
    from ..interpreter import sort_key
    if isinstance(key, (Task, Builtin)):
        return sorted(need_list(lst), key=lambda x: sort_key(it.call(key, [x])), reverse=truthy(backwards))
    k = to_text(key)
    return sorted(need_list(lst), key=lambda x: sort_key(it.get_prop(x, k)), reverse=truthy(backwards))


@builtin(["group_by"], 2, 2, "group_by(list, \"type\") makes a book of lists")
def _groupby(it, lst, key):
    out = {}
    for x in need_list(lst):
        k = it.call(key, [x]) if isinstance(key, (Task, Builtin)) else it.get_prop(x, to_text(key))
        out.setdefault(to_text(k), []).append(x)
    return out


@builtin(["index_list", "numbered"], 1, 1, "[a, b] -> [[1, a], [2, b]]")
def _enum(it, lst):
    return [[i, x] for i, x in enumerate(need_list(lst), start=1)]


@builtin(["most_common", "mode"], 1, 1, "The item that appears most often")
def _mode(it, lst):
    from collections import Counter
    vals = [to_text(x) if not is_number(x) else x for x in need_list(lst)]
    if not vals:
        return None
    return Counter(vals).most_common(1)[0][0]


@builtin(["tally", "counts"], 1, 1, "A book of how many times each item appears")
def _tally(it, lst):
    out = {}
    for x in need_list(lst):
        k = to_text(x)
        out[k] = out.get(k, 0) + 1
    return out


@builtin(["book", "make_book", "dictionary"], 0, None, "book(\"name\", \"Bob\", \"age\", 3)")
def _book(it, *args):
    if len(args) == 1 and isinstance(args[0], list):
        return {to_text(p[0]): p[1] for p in args[0] if isinstance(p, list) and len(p) == 2}
    if len(args) % 2:
        raise MemoError("book() needs pairs: key, value, key, value ...")
    return {to_text(args[i]): args[i + 1] for i in range(0, len(args), 2)}


@builtin(["merge", "merged"], 2, 2, "Merges two books")
def _merge(it, a, b):
    c = dict(a)
    c.update(b)
    return c


# =================================================================== types

@builtin(["typeof", "type", "kind_of", "what_is"], 1, 1, "What kind of value this is")
def _typeof(it, v):
    return type_name(v)


@builtin(["bool", "yes_or_no", "truth"], 1, 1, "Turns a value into yes or no")
def _bool(it, v):
    return truthy(v)


@builtin(["is_list"], 1, 1, "Is this a list?")
def _islist(it, v):
    return isinstance(v, list)


@builtin(["is_text"], 1, 1, "Is this text?")
def _istext(it, v):
    return isinstance(v, str)


@builtin(["is_book"], 1, 1, "Is this a book?")
def _isbook(it, v):
    return isinstance(v, dict)


@builtin(["is_nothing", "is_none"], 1, 1, "Is this nothing?")
def _isnone(it, v):
    return v is None


@builtin(["default", "or_else", "otherwise_use"], 2, 2, "default(x, 0) gives 0 if x is nothing")
def _default(it, v, d):
    return d if v is None or v == "" else v


# =================================================================== time

@builtin(["now", "time_now"], 0, 0, "The date and time now as text")
def _now(it):
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@builtin(["time", "clock"], 0, 0, "The time now, like 14:05")
def _time(it):
    return datetime.datetime.now().strftime("%H:%M")


@builtin(["today", "date"], 0, 0, "Today's date, like 2026-10-23")
def _today(it):
    return datetime.date.today().isoformat()


@builtin(["year"], 0, 0, "This year")
def _year(it):
    return datetime.date.today().year


@builtin(["month"], 0, 0, "This month (1-12)")
def _month(it):
    return datetime.date.today().month


@builtin(["month_name"], 0, 1, "The name of this month (or of month n)")
def _monthname(it, n=None):
    import calendar
    return calendar.month_name[int(num(n)) if n is not None else datetime.date.today().month]


@builtin(["day"], 0, 0, "Day of the month")
def _day(it):
    return datetime.date.today().day


@builtin(["weekday", "day_name", "day_of_week"], 0, 1, "Monday, Tuesday ... (today or a date)")
def _weekday(it, d=None):
    if d is None:
        return datetime.date.today().strftime("%A")
    return datetime.date.fromisoformat(to_text(d)).strftime("%A")


@builtin(["hour"], 0, 0, "The hour now (0-23)")
def _hour(it):
    return datetime.datetime.now().hour


@builtin(["minute"], 0, 0, "The minute now")
def _minute(it):
    return datetime.datetime.now().minute


@builtin(["second"], 0, 0, "The second now")
def _second(it):
    return datetime.datetime.now().second


@builtin(["timestamp", "seconds_since_1970"], 0, 0, "Seconds since 1970")
def _ts(it):
    return time.time()


@builtin(["timer", "seconds_running", "running_time", "elapsed"], 0, 0, "Seconds since the program started")
def _timer(it):
    return round(time.time() - it.start_time, 3)


@builtin(["milliseconds", "ms_now"], 0, 0, "Milliseconds since the program started")
def _ms(it):
    return int((time.time() - it.start_time) * 1000)


@builtin(["days_between", "days_until"], 1, 2, "Days between two dates (or until a date)")
def _daysbetween(it, a, b=None):
    if b is None:
        a, b = datetime.date.today().isoformat(), a
    d1 = datetime.date.fromisoformat(to_text(a))
    d2 = datetime.date.fromisoformat(to_text(b))
    return (d2 - d1).days


@builtin(["add_days"], 2, 2, "add_days(\"2026-01-01\", 10)")
def _adddays(it, d, n):
    return (datetime.date.fromisoformat(to_text(d)) + datetime.timedelta(days=int(num(n)))).isoformat()


@builtin(["format_date", "pretty_date"], 1, 2, "format_date(\"2026-10-23\") -> \"Friday 23 October 2026\"")
def _fmtdate(it, d, pattern=None):
    dd = datetime.date.fromisoformat(to_text(d)[:10])
    if pattern is None:
        return dd.strftime("%A %d %B %Y").replace(" 0", " ")
    return dd.strftime(to_text(pattern))


@builtin(["age_from", "age"], 1, 1, "Age in years from a birth date")
def _age(it, d):
    b = datetime.date.fromisoformat(to_text(d))
    t = datetime.date.today()
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


@builtin(["is_leap_year", "leap_year"], 1, 1, "Is it a leap year?")
def _leap(it, y):
    import calendar
    return calendar.isleap(int(num(y)))


@builtin(["countdown_text", "duration"], 1, 1, "125 seconds -> 2:05")
def _duration(it, secs):
    secs = int(num(secs))
    h, rem = divmod(abs(secs), 3600)
    m, s = divmod(rem, 60)
    return (f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}")


# =================================================================== data

@builtin(["to_json", "json"], 1, 1, "Turns a value into JSON text")
def _tojson(it, v):
    return json.dumps(v, indent=2, ensure_ascii=False, default=to_text)


@builtin(["from_json", "parse_json"], 1, 1, "Turns JSON text into lists and books")
def _fromjson(it, t):
    return json.loads(to_text(t))


@builtin(["from_csv", "parse_csv"], 1, 1, "Turns CSV text into a list of lists")
def _fromcsv(it, t):
    import csv
    import io
    return [[tidy_number(float(c)) if looks_like_number(c) else c for c in row] for row in csv.reader(io.StringIO(to_text(t)))]


@builtin(["to_csv"], 1, 1, "Turns a list of lists into CSV text")
def _tocsv(it, rows):
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    for r in need_list(rows):
        w.writerow([to_text(c) for c in (r if isinstance(r, list) else [r])])
    return buf.getvalue()


@builtin(["memory", "recall_value", "remembered"], 1, 2, "memory(\"score\") reads a value from File.Memory")
def _memory(it, key, default=None):
    k = to_text(key)
    return it.memory.get(k) if it.memory.has(k) else default


@builtin(["memory_keys", "remembered_names"], 0, 0, "Everything saved in File.Memory")
def _memkeys(it):
    return it.memory.keys()


@builtin(["remembers", "in_memory"], 1, 1, "Is this name saved in File.Memory?")
def _remembers(it, key):
    return it.memory.has(to_text(key))


@builtin(["hash", "fingerprint"], 1, 1, "A short fingerprint (sha256) of some text")
def _hash(it, t):
    import hashlib
    return hashlib.sha256(to_text(t).encode()).hexdigest()


@builtin(["base64", "encode_base64"], 1, 1, "Encodes text as base64")
def _b64(it, t):
    import base64
    return base64.b64encode(to_text(t).encode()).decode()


@builtin(["decode_base64"], 1, 1, "Decodes base64 text")
def _b64d(it, t):
    import base64
    return base64.b64decode(to_text(t)).decode(errors="replace")


# =================================================================== tasks & program

@builtin(["run_task", "call_task"], 1, None, "run_task(mytask, value1, value2 ...)")
def _calltask(it, fn, *args):
    return it.call(fn, list(args))


@builtin(["version", "memowrite_version"], 0, 0, "The Memowrite version")
def _version(it):
    from .. import __version__
    return __version__


@builtin(["program_folder", "this_folder"], 0, 0, "The folder your program is in")
def _folder(it):
    return it.base_dir
