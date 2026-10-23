"""Color names Memowrite understands (all the web colors, plus a few friendly ones)."""

from ..errors import MemoError

NAMED = {
    "aliceblue": "#f0f8ff", "antiquewhite": "#faebd7", "aqua": "#00ffff", "aquamarine": "#7fffd4", "azure": "#f0ffff",
    "beige": "#f5f5dc", "bisque": "#ffe4c4", "black": "#000000", "blanchedalmond": "#ffebcd", "blue": "#0000ff",
    "blueviolet": "#8a2be2", "brown": "#a52a2a", "burlywood": "#deb887", "cadetblue": "#5f9ea0", "chartreuse": "#7fff00",
    "chocolate": "#d2691e", "coral": "#ff7f50", "cornflowerblue": "#6495ed", "cornsilk": "#fff8dc", "crimson": "#dc143c",
    "cyan": "#00ffff", "darkblue": "#00008b", "darkcyan": "#008b8b", "darkgoldenrod": "#b8860b", "darkgray": "#a9a9a9",
    "darkgreen": "#006400", "darkgrey": "#a9a9a9", "darkkhaki": "#bdb76b", "darkmagenta": "#8b008b",
    "darkolivegreen": "#556b2f", "darkorange": "#ff8c00", "darkorchid": "#9932cc", "darkred": "#8b0000",
    "darksalmon": "#e9967a", "darkseagreen": "#8fbc8f", "darkslateblue": "#483d8b", "darkslategray": "#2f4f4f",
    "darkslategrey": "#2f4f4f", "darkturquoise": "#00ced1", "darkviolet": "#9400d3", "deeppink": "#ff1493",
    "deepskyblue": "#00bfff", "dimgray": "#696969", "dimgrey": "#696969", "dodgerblue": "#1e90ff",
    "firebrick": "#b22222", "floralwhite": "#fffaf0", "forestgreen": "#228b22", "fuchsia": "#ff00ff",
    "gainsboro": "#dcdcdc", "ghostwhite": "#f8f8ff", "gold": "#ffd700", "goldenrod": "#daa520", "gray": "#808080",
    "grey": "#808080", "green": "#008000", "greenyellow": "#adff2f", "honeydew": "#f0fff0", "hotpink": "#ff69b4",
    "indianred": "#cd5c5c", "indigo": "#4b0082", "ivory": "#fffff0", "khaki": "#f0e68c", "lavender": "#e6e6fa",
    "lavenderblush": "#fff0f5", "lawngreen": "#7cfc00", "lemonchiffon": "#fffacd", "lightblue": "#add8e6",
    "lightcoral": "#f08080", "lightcyan": "#e0ffff", "lightgoldenrodyellow": "#fafad2", "lightgray": "#d3d3d3",
    "lightgreen": "#90ee90", "lightgrey": "#d3d3d3", "lightpink": "#ffb6c1", "lightsalmon": "#ffa07a",
    "lightseagreen": "#20b2aa", "lightskyblue": "#87cefa", "lightslategray": "#778899", "lightslategrey": "#778899",
    "lightsteelblue": "#b0c4de", "lightyellow": "#ffffe0", "lime": "#00ff00", "limegreen": "#32cd32",
    "linen": "#faf0e6", "magenta": "#ff00ff", "maroon": "#800000", "mediumaquamarine": "#66cdaa",
    "mediumblue": "#0000cd", "mediumorchid": "#ba55d3", "mediumpurple": "#9370db", "mediumseagreen": "#3cb371",
    "mediumslateblue": "#7b68ee", "mediumspringgreen": "#00fa9a", "mediumturquoise": "#48d1cc",
    "mediumvioletred": "#c71585", "midnightblue": "#191970", "mintcream": "#f5fffa", "mistyrose": "#ffe4e1",
    "moccasin": "#ffe4b5", "navajowhite": "#ffdead", "navy": "#000080", "oldlace": "#fdf5e6", "olive": "#808000",
    "olivedrab": "#6b8e23", "orange": "#ffa500", "orangered": "#ff4500", "orchid": "#da70d6",
    "palegoldenrod": "#eee8aa", "palegreen": "#98fb98", "paleturquoise": "#afeeee", "palevioletred": "#db7093",
    "papayawhip": "#ffefd5", "peachpuff": "#ffdab9", "peru": "#cd853f", "pink": "#ffc0cb", "plum": "#dda0dd",
    "powderblue": "#b0e0e6", "purple": "#800080", "rebeccapurple": "#663399", "red": "#ff0000",
    "rosybrown": "#bc8f8f", "royalblue": "#4169e1", "saddlebrown": "#8b4513", "salmon": "#fa8072",
    "sandybrown": "#f4a460", "seagreen": "#2e8b57", "seashell": "#fff5ee", "sienna": "#a0522d", "silver": "#c0c0c0",
    "skyblue": "#87ceeb", "slateblue": "#6a5acd", "slategray": "#708090", "slategrey": "#708090", "snow": "#fffafa",
    "springgreen": "#00ff7f", "steelblue": "#4682b4", "tan": "#d2b48c", "teal": "#008080", "thistle": "#d8bfd8",
    "tomato": "#ff6347", "turquoise": "#40e0d0", "violet": "#ee82ee", "wheat": "#f5deb3", "white": "#ffffff",
    "whitesmoke": "#f5f5f5", "yellow": "#ffff00", "yellowgreen": "#9acd32",
    # friendly extras
    "grass": "#4caf50", "sky": "#87ceeb", "sea": "#1e88e5", "sand": "#e8d29b", "night": "#1a1a2e", "sun": "#ffcc00",
    "fire": "#ff5722", "ice": "#d6f4ff", "wood": "#8d6e63", "stone": "#9e9e9e", "leaf": "#66bb6a", "cherry": "#d2042d",
    "lemon": "#fff44f", "mint": "#98ff98", "peach": "#ffcba4", "rose": "#ff66cc", "cobalt": "#0047ab",
    "memowrite": "#3b5bdb", "memo": "#3b5bdb",
}


def normalize(name):
    if name is None:
        return None
    if isinstance(name, (list, tuple)) and len(name) >= 3:
        return "#%02x%02x%02x" % tuple(int(max(0, min(255, float(c)))) for c in name[:3])
    text = str(name).strip().lower()
    if text in ("", "none", "transparent", "nothing", "clear", "invisible"):
        return None
    key = text.replace(" ", "").replace("-", "").replace("_", "")
    if key in NAMED:
        return NAMED[key]
    if text.startswith("#"):
        h = text[1:]
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        if len(h) == 6 and all(c in "0123456789abcdef" for c in h):
            return "#" + h
    if text.startswith("rgb(") and text.endswith(")"):
        parts = [float(p) for p in text[4:-1].split(",")]
        return normalize(parts)
    # light/dark versions: "light red", "dark blue"
    for prefix, factor in (("light", 1.45), ("dark", 0.6), ("pale", 1.7), ("deep", 0.8)):
        if key.startswith(prefix) and key[len(prefix):] in NAMED:
            r, g, b = to_rgb(NAMED[key[len(prefix):]])
            if factor > 1:
                mix = factor - 1
                r, g, b = (int(c + (255 - c) * min(1, mix)) for c in (r, g, b))
            else:
                r, g, b = (int(c * factor) for c in (r, g, b))
            return "#%02x%02x%02x" % (r, g, b)
    names = sorted(k for k in NAMED if len(k) < 9)[:40]
    raise MemoError(f"I don't know the color '{name}'", hint="Try a name like red, sky blue, orange, or a code like #ff8800")


def to_rgb(color):
    c = normalize(color)
    if c is None:
        return None
    return int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)


def rgb(r, g, b):
    return "#%02x%02x%02x" % (int(max(0, min(255, r))), int(max(0, min(255, g))), int(max(0, min(255, b))))


def lighter(color, amount=0.3):
    r, g, b = to_rgb(color)
    return rgb(r + (255 - r) * amount, g + (255 - g) * amount, b + (255 - b) * amount)


def darker(color, amount=0.3):
    r, g, b = to_rgb(color)
    return rgb(r * (1 - amount), g * (1 - amount), b * (1 - amount))


def mix(c1, c2, t=0.5):
    a, b = to_rgb(c1), to_rgb(c2)
    return rgb(*(x + (y - x) * t for x, y in zip(a, b)))
