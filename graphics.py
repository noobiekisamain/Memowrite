"""2D graphics for Memowrite: canvases, shapes, 2D models, animation and export.

Positions:
  * circles, ellipses, stars, polygons, triangles, text and images are placed by their CENTER
  * rectangles, squares and round boxes are placed by their TOP-LEFT corner
Sizes:
  * circle size = radius, ellipse size = width by height, square size = side,
    rectangle size = width by height, star/hexagon/pentagon size = radius,
    triangle size = side length, text size = font size
"""

import json
import math
import os
import struct
import zlib

from ..errors import MemoError
from ..values import to_text, to_number, is_number, tidy_number, truthy
from . import colors

CIRCLE_STEPS = 64


# =================================================================== shapes

class Shape:
    def __init__(self, kind, pts, fill=None, outline=None, width=1, closed=True, **extra):
        self.kind = kind
        self.pts = [[float(x), float(y)] for x, y in pts]
        self.fill = fill
        self.outline = outline
        self.width = width
        self.closed = closed
        self.text = extra.get("text")
        self.font_size = extra.get("font_size", 14)
        self.bold = extra.get("bold", False)
        self.font = extra.get("font", "Segoe UI")
        self.image_path = extra.get("image_path")
        self.smooth = extra.get("smooth", False)
        self.dashed = extra.get("dashed", False)
        self.arrow = extra.get("arrow", False)
        self.angle = extra.get("angle", 0.0)
        self.hidden = extra.get("hidden", False)
        self.tk_id = None
        self.photo = None
        self.canvas = None

    def spec(self):
        return {"kind": self.kind, "pts": [[round(x, 3), round(y, 3)] for x, y in self.pts], "fill": self.fill,
                "outline": self.outline, "width": self.width, "closed": self.closed, "text": self.text,
                "font_size": self.font_size, "bold": self.bold, "font": self.font, "image_path": self.image_path,
                "smooth": self.smooth, "dashed": self.dashed, "arrow": self.arrow, "angle": self.angle}

    @staticmethod
    def from_spec(s):
        extra = {k: s.get(k) for k in ("text", "font_size", "bold", "font", "image_path", "smooth", "dashed", "arrow", "angle")}
        extra = {k: v for k, v in extra.items() if v is not None}
        return Shape(s["kind"], s["pts"], s.get("fill"), s.get("outline"), s.get("width", 1), s.get("closed", True), **extra)

    def bbox(self):
        xs = [p[0] for p in self.pts]
        ys = [p[1] for p in self.pts]
        if self.kind == "text" and self.text:
            w = len(self.text) * self.font_size * 0.55
            h = self.font_size * 1.3
            x, y = self.pts[0]
            return x - w / 2, y - h / 2, x + w / 2, y + h / 2
        if self.kind == "image" and self.photo is not None:
            x, y = self.pts[0]
            w, h = self.photo.width(), self.photo.height()
            return x - w / 2, y - h / 2, x + w / 2, y + h / 2
        pad = (self.width or 0) / 2 if not self.closed or self.fill is None else 0
        return min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad


def rotate_points(pts, cx, cy, degrees):
    a = math.radians(degrees)
    ca, sa = math.cos(a), math.sin(a)
    for p in pts:
        dx, dy = p[0] - cx, p[1] - cy
        p[0] = cx + dx * ca - dy * sa
        p[1] = cy + dx * sa + dy * ca


def regular_polygon(cx, cy, r, n, start=-90):
    return [[cx + r * math.cos(math.radians(start + 360 * i / n)), cy + r * math.sin(math.radians(start + 360 * i / n))] for i in range(n)]


def ellipse_points(cx, cy, rx, ry, steps=CIRCLE_STEPS):
    return [[cx + rx * math.cos(2 * math.pi * i / steps), cy + ry * math.sin(2 * math.pi * i / steps)] for i in range(steps)]


def star_points(cx, cy, r, tips=5, inner=0.45):
    pts = []
    for i in range(tips * 2):
        rr = r if i % 2 == 0 else r * inner
        a = math.radians(-90 + 180 * i / tips)
        pts.append([cx + rr * math.cos(a), cy + rr * math.sin(a)])
    return pts


def heart_points(cx, cy, size, steps=60):
    pts = []
    s = size / 32
    for i in range(steps):
        t = 2 * math.pi * i / steps
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append([cx + x * s, cy - y * s])
    return pts


def roundbox_points(x, y, w, h, r):
    r = max(0, min(r, w / 2, h / 2))
    pts = []
    corners = ((x + w - r, y + r, -90), (x + w - r, y + h - r, 0), (x + r, y + h - r, 90), (x + r, y + r, 180))
    for cx, cy, start in corners:
        for i in range(9):
            a = math.radians(start + 90 * i / 8)
            pts.append([cx + r * math.cos(a), cy + r * math.sin(a)])
    return pts


def arc_points(cx, cy, r, start, extent, steps=40):
    pts = [[cx, cy]]
    for i in range(steps + 1):
        a = math.radians(start + extent * i / steps)
        pts.append([cx + r * math.cos(a), cy + r * math.sin(a)])
    return pts


# =================================================================== groups (what variables hold)

class ShapeGroup:
    """One or more shapes that move together. A drawn shape or a placed model."""
    TYPE_NAME = "shape"

    def __init__(self, shapes, canvas, name=None, kind="shape"):
        self.shapes = shapes
        self.canvas = canvas
        self.name = name
        self.kind = kind
        self.heading = 0.0
        self.data = {}

    def __repr__(self):
        return f"{self.kind} {self.name or ''}".strip()

    # geometry
    def bbox(self):
        boxes = [s.bbox() for s in self.shapes if not s.hidden] or [s.bbox() for s in self.shapes]
        if not boxes:
            return 0, 0, 0, 0
        return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)

    def cx(self):
        l, t, r, b = self.bbox()
        return (l + r) / 2

    def cy(self):
        l, t, r, b = self.bbox()
        return (t + b) / 2

    def _changed(self):
        if self.canvas is not None:
            for s in self.shapes:
                self.canvas.redraw(s)

    def move_by(self, dx, dy):
        for s in self.shapes:
            for p in s.pts:
                p[0] += dx
                p[1] += dy
        self._changed()

    def move_to(self, x, y):
        self.move_by(x - self.cx(), y - self.cy())

    def forward(self, amount):
        a = math.radians(self.heading - 90)
        self.move_by(amount * math.cos(a), amount * math.sin(a))

    def move_towards(self, tx, ty, amount):
        dx, dy = tx - self.cx(), ty - self.cy()
        d = math.hypot(dx, dy)
        if d <= amount or d == 0:
            self.move_to(tx, ty)
        else:
            self.move_by(dx / d * amount, dy / d * amount)

    def rotate_by(self, degrees):
        cx, cy = self.cx(), self.cy()
        for s in self.shapes:
            rotate_points(s.pts, cx, cy, degrees)
            if s.kind == "text":
                s.angle = (s.angle - degrees) % 360
        self.heading = (self.heading + degrees) % 360
        self._changed()

    def rotate_to(self, degrees):
        self.rotate_by(degrees - self.heading)

    def scale_by(self, f):
        cx, cy = self.cx(), self.cy()
        for s in self.shapes:
            for p in s.pts:
                p[0] = cx + (p[0] - cx) * f
                p[1] = cy + (p[1] - cy) * f
            if s.kind == "text":
                s.font_size = max(1, s.font_size * f)
        self._changed()

    def resize(self, w, h):
        l, t, r, b = self.bbox()
        cw, ch = (r - l) or 1, (b - t) or 1
        for s in self.shapes:
            for p in s.pts:
                p[0] = l + (p[0] - l) * w / cw
                p[1] = t + (p[1] - t) * h / ch
        self._changed()

    def flip(self, axis):
        cx, cy = self.cx(), self.cy()
        for s in self.shapes:
            for p in s.pts:
                if axis == "h":
                    p[0] = 2 * cx - p[0]
                else:
                    p[1] = 2 * cy - p[1]
        self._changed()

    def recolor(self, c):
        c = colors.normalize(c)
        for s in self.shapes:
            if s.closed and s.kind not in ("text",) and s.fill is not None:
                s.fill = c
            elif not s.closed or s.kind == "text":
                if s.kind == "text":
                    s.fill = c
                else:
                    s.outline = c
            else:
                s.outline = c
        self._changed()

    def hide(self):
        for s in self.shapes:
            s.hidden = True
        self._changed()

    def show(self):
        for s in self.shapes:
            s.hidden = False
        self._changed()

    def delete(self):
        if self.canvas is not None:
            for s in self.shapes:
                self.canvas.remove(s)
        self.shapes = []

    def to_front(self):
        if self.canvas is not None:
            for s in self.shapes:
                self.canvas.raise_shape(s)

    def to_back(self):
        if self.canvas is not None:
            for s in reversed(self.shapes):
                self.canvas.lower_shape(s)

    def touches(self, other):
        if isinstance(other, list):
            return any(self.touches(o) for o in other)
        if isinstance(other, ShapeGroup):
            if other is self or not other.shapes or not self.shapes:
                return False
            if all(s.hidden for s in self.shapes) or all(s.hidden for s in other.shapes):
                return False
            a, b = self.bbox(), other.bbox()
            return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]
        if isinstance(other, str) and other.lower() in ("edge", "edges", "wall", "walls", "the edge"):
            return self.touches_edge()
        if isinstance(other, (list, tuple)) and len(other) == 2:
            x, y = to_number(other[0]), to_number(other[1])
            l, t, r, b = self.bbox()
            return l <= x <= r and t <= y <= b
        return False

    def touches_edge(self):
        if self.canvas is None:
            return False
        l, t, r, b = self.bbox()
        return l <= 0 or t <= 0 or r >= self.canvas.width or b >= self.canvas.height

    def contains_point(self, x, y):
        l, t, r, b = self.bbox()
        return l <= x <= r and t <= y <= b

    def clone(self):
        shapes = [Shape.from_spec(s.spec()) for s in self.shapes]
        g = ShapeGroup(shapes, self.canvas, None, self.kind)
        g.heading = self.heading
        g.data = dict(self.data)
        if self.canvas is not None:
            for s in shapes:
                self.canvas.add(s)
        return g

    # properties: x of ball, set color of ball to "red", set ball.speed to 5
    def get_prop(self, word):
        l, t, r, b = self.bbox()
        props = {
            "x": tidy_number(round((l + r) / 2, 3)), "y": tidy_number(round((t + b) / 2, 3)),
            "left": tidy_number(round(l, 3)), "right": tidy_number(round(r, 3)), "top": tidy_number(round(t, 3)),
            "bottom": tidy_number(round(b, 3)), "width": tidy_number(round(r - l, 3)), "height": tidy_number(round(b - t, 3)),
            "angle": tidy_number(round(self.heading, 3)), "heading": tidy_number(round(self.heading, 3)),
            "name": self.name, "visible": not all(s.hidden for s in self.shapes), "parts": len(self.shapes),
        }
        if word in props:
            return props[word]
        if word in ("color", "colour", "fill"):
            for s in self.shapes:
                if s.fill:
                    return s.fill
            return self.shapes[0].outline if self.shapes else None
        if word in ("outline", "border"):
            return self.shapes[0].outline if self.shapes else None
        if word in ("text", "saying"):
            for s in self.shapes:
                if s.kind == "text":
                    return s.text
            return None
        if word in self.data:
            return self.data[word]
        if word in ("touching_edge", "at_edge"):
            return self.touches_edge()
        raise KeyError(word)

    def set_prop(self, word, value):
        if word == "x":
            self.move_by(to_number(value) - self.cx(), 0)
        elif word == "y":
            self.move_by(0, to_number(value) - self.cy())
        elif word == "left":
            self.move_by(to_number(value) - self.bbox()[0], 0)
        elif word == "top":
            self.move_by(0, to_number(value) - self.bbox()[1])
        elif word in ("right",):
            self.move_by(to_number(value) - self.bbox()[2], 0)
        elif word in ("bottom",):
            self.move_by(0, to_number(value) - self.bbox()[3])
        elif word in ("angle", "heading"):
            self.rotate_to(to_number(value))
        elif word in ("color", "colour", "fill"):
            self.recolor(to_text(value))
        elif word in ("outline", "border"):
            c = colors.normalize(value)
            for s in self.shapes:
                s.outline = c
            self._changed()
        elif word in ("width",):
            l, t, r, b = self.bbox()
            self.resize(to_number(value), b - t)
        elif word in ("height",):
            l, t, r, b = self.bbox()
            self.resize(r - l, to_number(value))
        elif word in ("text", "saying"):
            for s in self.shapes:
                if s.kind == "text":
                    s.text = to_text(value)
            self._changed()
        elif word == "visible":
            self.show() if truthy(value) else self.hide()
        elif word == "size":
            # size of text
            for s in self.shapes:
                if s.kind == "text":
                    s.font_size = to_number(value)
            self._changed()
        else:
            self.data[word] = value


# =================================================================== canvas

class Canvas:
    TYPE_NAME = "canvas"

    def __init__(self, name, width=600, height=400, bg="#ffffff"):
        self.name = name
        self.width = int(width)
        self.height = int(height)
        self.bg = colors.normalize(bg) if bg else "#ffffff"
        self.shapes = []
        self.tk = None
        self.widget = None  # GUI widget wrapper when inside a window

    def __repr__(self):
        return f"canvas {self.name} ({self.width}x{self.height})"

    def attach(self, tk_canvas):
        self.tk = tk_canvas
        tk_canvas.configure(background=self.bg or "#ffffff")
        for s in self.shapes:
            s.tk_id = None
            self._create(s)

    # -- tk drawing
    def _font(self, s):
        return (s.font or "Segoe UI", int(round(s.font_size)), "bold" if s.bold else "normal")

    def _create(self, s):
        if self.tk is None:
            return
        c = self.tk
        flat = [v for p in s.pts for v in p]
        state = "hidden" if s.hidden else "normal"
        if s.kind == "text":
            s.tk_id = c.create_text(s.pts[0][0], s.pts[0][1], text=s.text or "", fill=s.fill or "#000000",
                                    font=self._font(s), angle=s.angle, state=state)
        elif s.kind == "image":
            import tkinter as tk
            if s.photo is None and s.image_path:
                try:
                    s.photo = tk.PhotoImage(file=s.image_path)
                except Exception as e:
                    raise MemoError(f"I couldn't open the image {os.path.basename(s.image_path)} (use .png or .gif)")
            s.tk_id = c.create_image(s.pts[0][0], s.pts[0][1], image=s.photo, state=state)
        elif not s.closed:
            kw = dict(fill=s.outline or "#000000", width=s.width or 1, smooth=s.smooth, capstyle="round", joinstyle="round", state=state)
            if s.dashed:
                kw["dash"] = (6, 4)
            if s.arrow:
                kw["arrow"] = "last"
                kw["arrowshape"] = (12, 15, 5)
            if len(flat) < 4:
                flat = flat + flat
            s.tk_id = c.create_line(*flat, **kw)
        else:
            kw = dict(fill=s.fill or "", outline=s.outline or "", width=s.width if s.outline else 0, smooth=s.smooth, state=state)
            if s.dashed:
                kw["dash"] = (6, 4)
            s.tk_id = c.create_polygon(*flat, **kw)

    def add(self, s):
        s.canvas = self
        self.shapes.append(s)
        self._create(s)

    def redraw(self, s):
        if self.tk is None or s.tk_id is None:
            return
        c = self.tk
        try:
            if s.kind in ("text", "image"):
                c.coords(s.tk_id, s.pts[0][0], s.pts[0][1])
                if s.kind == "text":
                    c.itemconfigure(s.tk_id, text=s.text or "", fill=s.fill or "#000000", font=self._font(s), angle=s.angle)
            else:
                flat = [v for p in s.pts for v in p]
                if not s.closed and len(flat) < 4:
                    flat = flat + flat
                c.coords(s.tk_id, *flat)
                if s.closed:
                    c.itemconfigure(s.tk_id, fill=s.fill or "", outline=s.outline or "", width=s.width if s.outline else 0)
                else:
                    c.itemconfigure(s.tk_id, fill=s.outline or "#000000", width=s.width or 1)
            c.itemconfigure(s.tk_id, state="hidden" if s.hidden else "normal")
        except Exception:
            pass

    def remove(self, s):
        if s in self.shapes:
            self.shapes.remove(s)
        if self.tk is not None and s.tk_id is not None:
            self.tk.delete(s.tk_id)
            s.tk_id = None

    def raise_shape(self, s):
        if s in self.shapes:
            self.shapes.remove(s)
            self.shapes.append(s)
        if self.tk is not None and s.tk_id is not None:
            self.tk.tag_raise(s.tk_id)

    def lower_shape(self, s):
        if s in self.shapes:
            self.shapes.remove(s)
            self.shapes.insert(0, s)
        if self.tk is not None and s.tk_id is not None:
            self.tk.tag_lower(s.tk_id)

    def clear(self):
        for s in list(self.shapes):
            self.remove(s)

    def fill(self, color):
        self.bg = colors.normalize(color) or "#ffffff"
        if self.tk is not None:
            self.tk.configure(background=self.bg)

    def show(self):
        if self.widget is not None:
            self.widget.show()

    def hide(self):
        if self.widget is not None:
            self.widget.hide()

    def shapes_at(self, x, y):
        out = []
        for s in self.shapes:
            l, t, r, b = s.bbox()
            if l <= x <= r and t <= y <= b:
                out.append(s)
        return out

    def get_prop(self, word):
        props = {"width": self.width, "height": self.height, "background": self.bg, "color": self.bg,
                 "shapes": len(self.shapes), "name": self.name, "center_x": self.width / 2, "center_y": self.height / 2,
                 "middle_x": self.width / 2, "middle_y": self.height / 2}
        if word in props:
            return tidy_number(props[word]) if is_number(props[word]) else props[word]
        raise KeyError(word)

    def set_prop(self, word, value):
        if word in ("background", "color", "colour"):
            self.fill(to_text(value))
        elif word == "width":
            self.width = int(to_number(value))
            if self.tk is not None:
                self.tk.configure(width=self.width)
        elif word == "height":
            self.height = int(to_number(value))
            if self.tk is not None:
                self.tk.configure(height=self.height)
        else:
            raise KeyError(word)

    # -- export
    def export(self, path):
        ext = os.path.splitext(path)[1].lower()
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)
        if ext == ".svg":
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(self.to_svg())
        elif ext == ".png":
            write_png(path, self.rasterize())
        elif ext in (".ppm",):
            img = self.rasterize()
            with open(path, "wb") as fh:
                fh.write(b"P6 %d %d 255\n" % (img.w, img.h) + bytes(img.px))
        elif ext in (".ps", ".eps") and self.tk is not None:
            self.tk.postscript(file=path, colormode="color")
        elif ext in (".json", ".mwpic"):
            with open(path, "w", encoding="utf-8") as fh:
                json.dump({"width": self.width, "height": self.height, "background": self.bg,
                           "shapes": [s.spec() for s in self.shapes]}, fh, indent=1)
        else:
            raise MemoError("I can save pictures as .png, .svg, .ppm, .mwpic or .ps")

    def to_svg(self):
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.width}" height="{self.height}" viewBox="0 0 {self.width} {self.height}">',
               f'<rect width="100%" height="100%" fill="{self.bg or "#ffffff"}"/>']
        for s in self.shapes:
            if s.hidden:
                continue
            pts = " ".join(f"{x:.2f},{y:.2f}" for x, y in s.pts)
            if s.kind == "text":
                x, y = s.pts[0]
                weight = "bold" if s.bold else "normal"
                text = (s.text or "").replace("&", "&amp;").replace("<", "&lt;")
                rot = f' transform="rotate({-s.angle:.1f} {x:.1f} {y:.1f})"' if s.angle else ""
                out.append(f'<text x="{x:.2f}" y="{y:.2f}" fill="{s.fill or "#000"}" font-family="{s.font}, sans-serif" '
                           f'font-size="{s.font_size * 1.33:.1f}" font-weight="{weight}" text-anchor="middle" dominant-baseline="central"{rot}>{text}</text>')
            elif s.kind == "image":
                x, y = s.pts[0]
                out.append(f'<image href="{s.image_path}" x="{x:.1f}" y="{y:.1f}" transform="translate(-50%,-50%)"/>')
            elif not s.closed:
                dash = ' stroke-dasharray="6 4"' if s.dashed else ""
                out.append(f'<polyline points="{pts}" fill="none" stroke="{s.outline or "#000"}" stroke-width="{s.width}" stroke-linecap="round" stroke-linejoin="round"{dash}/>')
            else:
                stroke = f' stroke="{s.outline}" stroke-width="{s.width}"' if s.outline else ""
                out.append(f'<polygon points="{pts}" fill="{s.fill or "none"}"{stroke}/>')
        out.append("</svg>")
        return "\n".join(out)

    def rasterize(self):
        img = Raster(self.width, self.height, colors.to_rgb(self.bg or "#ffffff"))
        for s in self.shapes:
            if s.hidden or s.kind in ("text", "image"):
                continue
            if s.closed:
                if s.fill:
                    img.fill_polygon(s.pts, colors.to_rgb(s.fill))
                if s.outline and s.width:
                    ring = s.pts + [s.pts[0]]
                    for a, b in zip(ring, ring[1:]):
                        img.thick_line(a, b, s.width, colors.to_rgb(s.outline))
            else:
                col = colors.to_rgb(s.outline or "#000000")
                for a, b in zip(s.pts, s.pts[1:]):
                    img.thick_line(a, b, s.width or 1, col)
        return img


# =================================================================== a tiny rasterizer for PNG export

class Raster:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bytes(bg) * (w * h))

    def fill_polygon(self, pts, rgb):
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        y0 = max(0, int(math.floor(min(ys))))
        y1 = min(self.h - 1, int(math.ceil(max(ys))))
        n = len(pts)
        color = bytes(rgb)
        for y in range(y0, y1 + 1):
            sy = y + 0.5
            xs = []
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                if (ay <= sy < by) or (by <= sy < ay):
                    xs.append(ax + (sy - ay) * (bx - ax) / (by - ay))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = max(0, int(math.ceil(xs[i] - 0.5)))
                xb = min(self.w - 1, int(math.floor(xs[i + 1] - 0.5)))
                if xb >= xa:
                    start = (y * self.w + xa) * 3
                    self.px[start:start + (xb - xa + 1) * 3] = color * (xb - xa + 1)

    def thick_line(self, a, b, width, rgb):
        dx, dy = b[0] - a[0], b[1] - a[1]
        d = math.hypot(dx, dy)
        hw = max(0.5, width / 2)
        if d == 0:
            self.fill_polygon(ellipse_points(a[0], a[1], hw, hw, 12), rgb)
            return
        nx, ny = -dy / d * hw, dx / d * hw
        self.fill_polygon([[a[0] + nx, a[1] + ny], [b[0] + nx, b[1] + ny], [b[0] - nx, b[1] - ny], [a[0] - nx, a[1] - ny]], rgb)
        if width > 2:
            self.fill_polygon(ellipse_points(b[0], b[1], hw, hw, 12), rgb)


def write_png(path, img):
    raw = bytearray()
    row = img.w * 3
    for y in range(img.h):
        raw.append(0)
        raw += img.px[y * row:(y + 1) * row]

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", img.w, img.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# =================================================================== building shapes from options

def _num(it, opts, key, default=None):
    if key not in opts or opts[key] is None:
        return default
    return to_number(it.eval(opts[key]))


def _pair(it, opts, key, default=(0, 0)):
    if key not in opts:
        return default
    a, b = opts[key]
    return to_number(it.eval(a)), to_number(it.eval(b))


def _size(it, opts, default):
    if "size" not in opts:
        return default
    a, b = opts["size"]
    w = to_number(it.eval(a))
    h = to_number(it.eval(b)) if b is not None else None
    return w, h


def _color(it, opts, key, default):
    if key not in opts:
        return default
    v = opts[key]
    if v is True:
        return default
    return colors.normalize(it.eval(v))


def build_shapes(it, shape, opts, line=None):
    """Make Shape objects from a draw statement's options."""
    x, y = _pair(it, opts, "at", (None, None))
    has_at = x is not None
    if not has_at:
        x, y = 0, 0
    color = _color(it, opts, "color", None)
    outline = _color(it, opts, "outline", None)
    width = _num(it, opts, "width", None)
    extra = {"dashed": bool(opts.get("dashed")), "smooth": bool(opts.get("smooth")), "hidden": bool(opts.get("hidden"))}
    out = []

    def poly(pts, default_fill="#3b5bdb"):
        fill = color if color is not None else (None if outline else default_fill)
        return Shape(shape, pts, fill, outline, width if width is not None else (2 if outline else 1), True, **extra)

    if shape == "circle":
        w, _ = _size(it, opts, (_num(it, opts, "radius", 20), None))
        r = _num(it, opts, "radius", w)
        out.append(poly(ellipse_points(x, y, r, r)))
    elif shape == "ring":
        w, _ = _size(it, opts, (_num(it, opts, "radius", 20), None))
        r = _num(it, opts, "radius", w)
        pts = ellipse_points(x, y, r, r)
        s = Shape("ring", pts, None, color or outline or "#3b5bdb", width if width is not None else 6, True, **extra)
        out.append(s)
    elif shape == "ellipse":
        w, h = _size(it, opts, (60, 40))
        h = w if h is None else h
        out.append(poly(ellipse_points(x, y, w / 2, h / 2)))
    elif shape in ("rectangle", "square", "roundbox"):
        w, h = _size(it, opts, (80, 50) if shape != "square" else (50, None))
        if shape == "square" or h is None:
            h = w
        if shape == "roundbox":
            pts = roundbox_points(x, y, w, h, _num(it, opts, "corner", 12))
        else:
            pts = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
        out.append(poly(pts))
    elif shape == "triangle":
        if "points" in opts:
            pts = [[to_number(p[0]), to_number(p[1])] for p in it.eval(opts["points"])]
        else:
            side, _ = _size(it, opts, (60, None))
            hgt = side * math.sqrt(3) / 2
            pts = [[x, y - hgt * 2 / 3], [x + side / 2, y + hgt / 3], [x - side / 2, y + hgt / 3]]
        out.append(poly(pts))
    elif shape in ("hexagon", "pentagon"):
        r, _ = _size(it, opts, (30, None))
        out.append(poly(regular_polygon(x, y, r, 6 if shape == "hexagon" else 5, -90 if shape == "pentagon" else 0)))
    elif shape == "diamond":
        w, h = _size(it, opts, (50, 70))
        h = w * 1.4 if h is None else h
        out.append(poly([[x, y - h / 2], [x + w / 2, y], [x, y + h / 2], [x - w / 2, y]]))
    elif shape == "star":
        r, _ = _size(it, opts, (30, None))
        tips = 5
        if "points" in opts:
            pv = it.eval(opts["points"])
            if is_number(pv):
                tips = int(pv)
        out.append(poly(star_points(x, y, r, tips), "#ffcc00"))
    elif shape == "heart":
        s, _ = _size(it, opts, (50, None))
        out.append(poly(heart_points(x, y, s), "#e63946"))
    elif shape == "polygon":
        if "points" not in opts:
            raise MemoError("A polygon needs points, like: draw polygon points [[0,0], [50,0], [25,40]]", line)
        pts = [[to_number(p[0]) + (x if has_at else 0), to_number(p[1]) + (y if has_at else 0)] for p in it.eval(opts["points"])]
        out.append(poly(pts))
    elif shape in ("line", "arrow", "path"):
        if shape == "path" or ("points" in opts):
            raw = it.eval(opts["points"]) if "points" in opts else []
            pts = [[to_number(p[0]), to_number(p[1])] for p in raw]
        else:
            a = _pair(it, opts, "from", (x, y))
            b = _pair(it, opts, "to", (a[0] + 100, a[1]))
            pts = [list(a), list(b)]
        if shape == "arrow" or opts.get("arrow"):
            extra["arrow"] = True
        out.append(Shape("line", pts, None, color or outline or "#222222", width if width is not None else 3, False, **extra))
    elif shape == "dot":
        r, _ = _size(it, opts, (3, None))
        out.append(poly(ellipse_points(x, y, r, r, 16), "#000000"))
    elif shape == "arc":
        r, _ = _size(it, opts, (40, None))
        start = _num(it, opts, "start", 0)
        extent = _num(it, opts, "extent", 90)
        out.append(poly(arc_points(x, y, r, -start, -extent)))
    elif shape == "text":
        text = to_text(it.eval(opts["saying"])) if "saying" in opts else ""
        size, _ = _size(it, opts, (16, None))
        font = to_text(it.eval(opts["font"])) if "font" in opts else "Segoe UI"
        s = Shape("text", [[x, y]], color or "#111111", None, 0, True, text=text, font_size=size, bold=bool(opts.get("bold")), font=font, **extra)
        out.append(s)
    elif shape == "image":
        if "file" not in opts:
            raise MemoError("Which picture? Write: draw image \"cat.png\" at 100, 100", line)
        path = it.path(it.eval(opts["file"]))
        if not os.path.exists(path):
            raise MemoError(f"I can't find the picture {os.path.basename(path)}", line)
        out.append(Shape("image", [[x, y]], None, None, 0, True, image_path=path, **extra))
    elif shape == "grid":
        w, h = _size(it, opts, (300, 200))
        h = w if h is None else h
        step = _num(it, opts, "spacing", 20)
        col = color or outline or "#dddddd"
        gx = x
        while gx <= x + w + 0.01:
            out.append(Shape("line", [[gx, y], [gx, y + h]], None, col, width or 1, False))
            gx += step
        gy = y
        while gy <= y + h + 0.01:
            out.append(Shape("line", [[x, gy], [x + w, gy]], None, col, width or 1, False))
            gy += step
    else:
        raise MemoError(f"I can't draw a {shape}", line)

    angle = _num(it, opts, "angle", 0)
    return out, angle


def current_canvas(it, name=None):
    if name:
        c = it.lookup(name)
        if hasattr(c, "canvas_object"):
            c = c.canvas_object()
        if not isinstance(c, Canvas):
            raise MemoError(f"'{name}' is not a canvas")
        return c
    c = getattr(it, "current_canvas", None)
    if c is None:
        # make a window with a canvas automatically, so drawing just works
        gui = it.ensure_gui()
        c = gui.auto_canvas()
    return c


def draw(it, n):
    canvas = current_canvas(it, n.canvas)
    shapes, angle = build_shapes(it, n.shape, n.opts, n.line)
    for s in shapes:
        canvas.add(s)
    group = ShapeGroup(shapes, canvas, n.opts.get("called"), n.shape)
    if angle:
        group.rotate_by(angle)
    if n.opts.get("called"):
        it.assign(n.opts["called"], group)
    it.last_shape = group
    it.pump()
    return group


def make_canvas(it, n):
    w, h = 600, 400
    if "size" in n.opts:
        a, b = n.opts["size"]
        w = to_number(it.eval(a))
        h = to_number(it.eval(b)) if b is not None else w
    bg = None
    for key in ("color", "background"):
        if key in n.opts:
            bg = to_text(it.eval(n.opts[key]))
    c = Canvas(n.name, w, h, bg or "#ffffff")
    if n.parent is not None:
        gui = it.ensure_gui()
        gui.attach_canvas(c, n.parent, n.opts)
    it.assign(n.name, c)
    it.current_canvas = c


# =================================================================== 2D models

class Model:
    """A reusable 2D model made of shapes (like a car, a tree, a character)."""
    TYPE_NAME = "model"

    def __init__(self, name, specs):
        self.name = name
        self.specs = specs

    def __repr__(self):
        return f"model {self.name} ({len(self.specs)} parts)"

    def bbox(self):
        shapes = [Shape.from_spec(s) for s in self.specs]
        if not shapes:
            return 0, 0, 0, 0
        boxes = [s.bbox() for s in shapes]
        return min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)

    def get_prop(self, word):
        l, t, r, b = self.bbox()
        if word == "width":
            return tidy_number(round(r - l, 3))
        if word == "height":
            return tidy_number(round(b - t, 3))
        if word in ("parts", "length"):
            return len(self.specs)
        if word == "name":
            return self.name
        raise KeyError(word)

    def length(self):
        return len(self.specs)

    def save(self, path):
        if not os.path.splitext(path)[1]:
            path += ".mwmodel"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump({"memowrite_model": 1, "name": self.name, "parts": self.specs}, fh, indent=1)

    @staticmethod
    def load(path, name):
        if not os.path.splitext(path)[1]:
            path += ".mwmodel"
        if not os.path.exists(path):
            raise MemoError(f"I can't find the model file {os.path.basename(path)}")
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
        return Model(data.get("name", name), data["parts"])

    def build(self, x, y, scale=1.0, angle=0.0, recolor=None):
        shapes = []
        for spec in self.specs:
            s = Shape.from_spec(spec)
            for p in s.pts:
                p[0] = x + p[0] * scale
                p[1] = y + p[1] * scale
            s.width = (s.width or 0) * scale if s.width else s.width
            if s.kind == "text":
                s.font_size *= scale
            if recolor and s.fill and s.kind != "text":
                s.fill = recolor
            shapes.append(s)
        return shapes


def make_model(it, n):
    specs = []
    for shape, opts, line in n.parts:
        it.line = line
        built, angle = build_shapes(it, shape, opts, line)
        if angle:
            g = ShapeGroup(built, None)
            g.rotate_by(angle)
        specs.extend(s.spec() for s in built)
    it.assign(n.name, Model(n.name, specs))


def place(it, n):
    model = it.eval(n.model)
    if isinstance(model, ShapeGroup):
        clone = model.clone()
        if "at" in n.opts:
            x, y = _pair(it, n.opts, "at")
            clone.move_to(x, y)
        if n.opts.get("called"):
            it.assign(n.opts["called"], clone)
        return clone
    if not isinstance(model, Model):
        raise MemoError("I can only place models. Make one with: make model car ... end", n.line)
    canvas = current_canvas(it, n.canvas)
    x, y = _pair(it, n.opts, "at", (canvas.width / 2, canvas.height / 2))
    scale = _num(it, n.opts, "size", None) or _num(it, n.opts, "scale", 1)
    recolor = _color(it, n.opts, "color", None)
    shapes = model.build(x, y, scale, 0, recolor)
    for s in shapes:
        canvas.add(s)
    group = ShapeGroup(shapes, canvas, n.opts.get("called") or model.name, "model")
    angle = _num(it, n.opts, "angle", None) or _num(it, n.opts, "turned", None) or _num(it, n.opts, "rotated", 0)
    if angle:
        group.rotate_by(angle)
    if n.opts.get("called"):
        it.assign(n.opts["called"], group)
    it.last_shape = group
    it.pump()
    return group


# =================================================================== builtins

def extra_builtins(it):
    def rgb(r, g, b):
        return colors.rgb(to_number(r), to_number(g), to_number(b))

    def hsl(h, s, l):
        import colorsys
        r, g, b = colorsys.hls_to_rgb((to_number(h) % 360) / 360, to_number(l) / 100, to_number(s) / 100)
        return colors.rgb(r * 255, g * 255, b * 255)

    def lighter(c, amount=0.3):
        return colors.lighter(to_text(c), to_number(amount))

    def darker(c, amount=0.3):
        return colors.darker(to_text(c), to_number(amount))

    def mix(a, b, t=0.5):
        return colors.mix(to_text(a), to_text(b), to_number(t))

    def color_code(c):
        return colors.normalize(c)

    def touching(a, b):
        return a.touches(b) if hasattr(a, "touches") else False

    def touching_edge(a):
        return a.touches_edge() if hasattr(a, "touches_edge") else False

    def shapes_on(c):
        return len(current_canvas(it, None).shapes) if c is None else len(c.shapes)

    def clone(g):
        return g.clone()

    def model_from(*groups):
        specs = []
        ox = oy = None
        for g in groups:
            if isinstance(g, list):
                for x in g:
                    specs += [s.spec() for s in x.shapes]
            else:
                specs += [s.spec() for s in g.shapes]
        if not specs:
            raise MemoError("model_from needs some shapes")
        tmp = Model("m", specs)
        l, t, r, b = tmp.bbox()
        cx, cy = (l + r) / 2, (t + b) / 2
        for s in specs:
            s["pts"] = [[p[0] - cx, p[1] - cy] for p in s["pts"]]
        return Model("model", specs)

    def point_in(g, x, y):
        return g.contains_point(to_number(x), to_number(y))

    def canvas_width(c=None):
        return (c or current_canvas(it, None)).width

    def canvas_height(c=None):
        return (c or current_canvas(it, None)).height

    return {
        "rgb": (rgb, 3, 3, "rgb(255, 128, 0) makes a color"),
        "hsl": (hsl, 3, 3, "hsl(200, 80, 50) makes a color from hue, saturation, lightness"),
        "lighter": (lighter, 1, 2, "A lighter version of a color"),
        "darker": (darker, 1, 2, "A darker version of a color"),
        "mix_colors": (mix, 2, 3, "Mixes two colors"),
        "color_code": (color_code, 1, 1, "The #rrggbb code of a color name"),
        "touching": (touching, 2, 2, "Do two shapes touch?"),
        "touching_edge": (touching_edge, 1, 1, "Is the shape at the edge of its canvas?"),
        "shape_count": (shapes_on, 0, 1, "How many shapes are on a canvas"),
        "clone": (clone, 1, 1, "Makes a copy of a shape on the same canvas"),
        "model_from": (model_from, 1, None, "Turns drawn shapes into a reusable model"),
        "point_inside": (point_in, 3, 3, "Is the point inside the shape?"),
        "canvas_width": (canvas_width, 0, 1, "Width of the canvas"),
        "canvas_height": (canvas_height, 0, 1, "Height of the canvas"),
    }
