"""
Custom Tk widgets shared by every VisoLab application (identical copies).

Everything is drawn on a Canvas so a control looks the same on macOS,
Windows and Linux instead of mixing native and custom styles:

  * ``RoundedButton``     primary / secondary / ghost / danger button
  * ``RoundedEntry``      single-line text field
  * ``RoundedCombobox``   dropdown; can show translated labels while its
                          variable keeps the canonical value
  * ``CheckBox``          check box with a label
  * ``RadioButton``       radio button with a label
  * ``SegmentedControl``  a row of mutually exclusive segments (tabs)
  * ``GradientProgressBar``, ``RoundedSlider``
  * ``card`` / ``divider`` helpers and ``ScrollFrame``

Colours come from design.py (neutrals) and from the accent set with
``set_accent`` (the active mode's tone of the app hue). No business logic
lives here.

The dark appearance is applied here, once for every app: importing this
module routes every colour handed to Tk (widget options, canvas items,
text tags, ttk styles) and every colour these widgets paint into an image
through design.themed, so the apps keep writing light colours and the
same code draws both appearances. ``adapt_image`` does the same for a
picture such as a logo, and ``apply_window_appearance`` asks the
operating system for a matching title bar and native controls.
"""
from __future__ import annotations

import sys
import tkinter as tk
import tkinter.font as tkfont

from design import (C_APP_BG, C_BORDER, C_BORDER_STRONG, C_DANGER,
                    C_DISABLED_BG, C_DISABLED_FG, C_DIVIDER,
                    C_SURFACE, C_SURFACE_ALT, C_TEXT, C_TEXT_2, C_TEXT_3,
                    CONTROL_H, CONTROL_R, F_BODY, F_BUTTON, F_SMALL,
                    F_SMALL_B, accent_set, is_dark, mix, themed)
from theme import BAR_H, BAR_W, C_PROGRESS_END, C_PROGRESS_START, _MODE_THEMES

# Height of a text field; kept under this name for older call sites.
_ENTRY_HEIGHT = CONTROL_H

_ACCENT = dict(_MODE_THEMES["home"])


def set_accent(theme: dict) -> None:
    """Make *theme* (a _MODE_THEMES entry) the accent for widgets created
    from now on. Called when the active mode changes."""
    _ACCENT.clear()
    _ACCENT.update(theme)
    if "accent" not in _ACCENT:
        _ACCENT.update(accent_set(theme["primary"], theme["primary_dark"]))


def accent() -> dict:
    return _ACCENT


# ══════════════════════════════════════════════════════════════════════════════
#  Appearance
# ══════════════════════════════════════════════════════════════════════════════

_OPTION_ROLE = {}
for _k in ("bg", "background", "activebackground", "readonlybackground",
           "disabledbackground", "troughcolor", "selectcolor",
           "selectbackground", "fieldbackground", "lightcolor",
           "darkcolor"):
    _OPTION_ROLE[_k] = "bg"
for _k in ("fg", "foreground", "activeforeground", "disabledforeground",
           "selectforeground", "insertbackground", "insertcolor",
           "arrowcolor"):
    _OPTION_ROLE[_k] = "fg"
for _k in ("highlightbackground", "highlightcolor", "bordercolor"):
    _OPTION_ROLE[_k] = "mark"
_ITEM_KEYS = ("fill", "outline", "activefill", "activeoutline",
              "disabledfill", "disabledoutline")


def _map_options(cnf):
    if not isinstance(cnf, dict) or not cnf:
        return cnf
    out = None
    for key, value in cnf.items():
        role = _OPTION_ROLE.get(str(key).lstrip("-"))
        if role and isinstance(value, str):
            new = themed(value, role)
            if new != value:
                if out is None:
                    out = dict(cnf)
                out[key] = new
    return cnf if out is None else out


def _map_item(item_type, cnf):
    if not isinstance(cnf, dict) or not cnf:
        return cnf
    out = None
    for key in _ITEM_KEYS:
        value = cnf.get(key)
        if isinstance(value, str) and value:
            role = "fg" if (item_type == "text" and "fill" in key) else "mark"
            new = themed(value, role)
            if new != value:
                if out is None:
                    out = dict(cnf)
                out[key] = new
    return cnf if out is None else out


def _install_appearance_hooks():
    if getattr(tk, "_visolab_appearance", False):
        return
    tk._visolab_appearance = True
    misc_options = tk.Misc._options
    set_item = tk.Misc.__setitem__
    create = tk.Canvas._create
    item_configure = tk.Canvas.itemconfigure

    def _options(self, cnf, kw=None):
        if is_dark():
            cnf, kw = _map_options(cnf), _map_options(kw)
            if isinstance(self, (tk.Entry, tk.Text, tk.Spinbox)):
                merged = dict(cnf) if isinstance(cnf, dict) else {}
                merged.update(kw or {})
                ink = merged.get("fg") or merged.get("foreground")
                if ink and "insertbackground" not in merged:
                    kw = dict(kw or {})
                    kw["insertbackground"] = ink
        return misc_options(self, cnf, kw)

    def __setitem__(self, key, value):
        role = _OPTION_ROLE.get(key)
        if role and isinstance(value, str):
            value = themed(value, role)
        return set_item(self, key, value)

    def _create(self, item_type, args, kw):
        if is_dark():
            kw = _map_item(item_type, kw)
            if args and isinstance(args[-1], dict):
                args = tuple(args[:-1]) + (_map_item(item_type, args[-1]),)
        return create(self, item_type, args, kw)

    def itemconfigure(self, tag_or_id, cnf=None, **kw):
        if is_dark() and (kw or isinstance(cnf, dict)):
            try:
                item_type = self.type(tag_or_id)
            except tk.TclError:
                item_type = None
            kw = _map_item(item_type, kw)
            cnf = _map_item(item_type, cnf)
        return item_configure(self, tag_or_id, cnf, **kw)

    class Scrollbar(tk.Scrollbar):
        # The native macOS scroll bar keeps the light look whatever the
        # window's appearance, so the dark appearance draws its own.
        # Subclasses (ttk.Scrollbar) are left alone.
        def __new__(cls, master=None, cnf=None, **kw):
            if cls is Scrollbar and is_dark():
                return FlatScrollbar(master, **dict(cnf or {}, **kw))
            return super().__new__(cls)

    tk.Scrollbar = Scrollbar
    tk.Misc._options = _options
    tk.Misc.__setitem__ = __setitem__
    tk.Canvas._create = _create
    tk.Canvas.itemconfigure = tk.Canvas.itemconfig = itemconfigure

    toplevel_init = tk.Toplevel.__init__

    def _toplevel_init(self, *a, **k):
        toplevel_init(self, *a, **k)
        apply_window_appearance(self)
    tk.Toplevel.__init__ = _toplevel_init

    try:
        from tkinter import ttk
    except ImportError:                             # pragma: no cover
        return
    style_configure = ttk.Style.configure
    style_map = ttk.Style.map

    def configure(self, style, query_opt=None, **kw):
        if is_dark():
            kw = _map_options(kw)
        return style_configure(self, style, query_opt, **kw)

    def map_(self, style, query_opt=None, **kw):
        if is_dark():
            for key, spec in list(kw.items()):
                role = _OPTION_ROLE.get(key)
                if role and isinstance(spec, (list, tuple)):
                    kw[key] = [tuple(st[:-1]) + (themed(st[-1], role),)
                               if isinstance(st, (list, tuple)) and st
                               and isinstance(st[-1], str) else st
                               for st in spec]
        return style_map(self, style, query_opt, **kw)
    ttk.Style.configure = configure
    ttk.Style.map = map_


def apply_window_appearance(win) -> None:
    """Ask the operating system for a title bar and native controls
    (scroll bars, menus) in the appearance in force. Best effort: older
    Tk versions and other platforms simply keep their own."""
    dark = is_dark()
    try:
        if sys.platform == "darwin":
            win.update_idletasks()
            win.tk.call("::tk::unsupported::MacWindowStyle", "appearance",
                        win._w, "darkaqua" if dark else "aqua")
        elif sys.platform.startswith("win"):
            import ctypes
            win.update_idletasks()
            hwnd = ctypes.windll.user32.GetParent(win.winfo_id())
            value = ctypes.c_int(1 if dark else 0)
            for attribute in (20, 19):      # DWMWA_USE_IMMERSIVE_DARK_MODE
                if not ctypes.windll.dwmapi.DwmSetWindowAttribute(
                        hwnd, attribute, ctypes.byref(value),
                        ctypes.sizeof(value)):
                    break
    except Exception:                               # noqa: BLE001
        pass


def adapt_image(pil):
    """A PIL image (a logo, a mark) for the appearance in force. In dark,
    neutral pixels swap lightness, so a white ground becomes the dark
    surface and near-black lettering turns light, and dark coloured
    pixels are lightened like text; transparency is kept."""
    if not is_dark():
        return pil
    try:
        import numpy as np
    except ImportError:                             # pragma: no cover
        return pil
    img = pil.convert("RGBA")
    arr = np.asarray(img).astype(float) / 255.0
    rgb, alpha = arr[..., :3], arr[..., 3:]
    hi, lo = rgb.max(axis=2), rgb.min(axis=2)
    chroma = hi - lo
    light = (hi + lo) / 2
    ground = np.array([int(themed("#FFFFFF", "bg")[i:i + 2], 16)
                       for i in (1, 3, 5)]) / 255.0
    ink = np.array([int(themed("#1B2230", "fg")[i:i + 2], 16)
                    for i in (1, 3, 5)]) / 255.0
    swapped = ground + (1.0 - light)[..., None] * (ink - ground)
    lift = np.clip((0.62 - light) / 0.62, 0, 1)[..., None] * 0.55
    coloured = rgb + (1.0 - rgb) * lift
    neutral = np.clip(1.0 - chroma / 0.22, 0, 1)[..., None]
    out = neutral * swapped + (1 - neutral) * coloured
    merged = np.concatenate([np.clip(out, 0, 1), alpha], axis=2)
    from PIL import Image as _Image
    return _Image.fromarray((merged * 255).round().astype("uint8"), "RGBA")


_install_appearance_hooks()


def _font_obj(font):
    try:
        return tkfont.Font(font=font)
    except tk.TclError:
        return tkfont.nametofont("TkDefaultFont")


def text_width(text, font) -> int:
    return _font_obj(font).measure(text)


def _parent_bg(parent):
    try:
        return parent.cget("bg")
    except (tk.TclError, AttributeError):
        return C_APP_BG


try:
    from PIL import Image, ImageDraw, ImageTk
    _PIL = True
except Exception:                                   # pragma: no cover
    _PIL = False

_SS = 4                     # supersampling factor for anti-aliased shapes
_IMG_CACHE = {}


def _rgba(colour):
    if not colour:
        return None
    c = str(colour).lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        named = {"white": "FFFFFF", "black": "000000"}
        c = named.get(str(colour).lower(), "000000")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def _photo(key, size, paint):
    """A cached PhotoImage of *size*, drawn at _SS x by *paint(draw, ss)*
    and downsampled, so edges are anti-aliased on every platform (Tk's own
    canvas shapes are not)."""
    # An image belongs to the Tk interpreter that made it, so a cached one
    # is reused only while that same root is alive.
    root = getattr(tk, "_default_root", None)
    hit = _IMG_CACHE.get(key)
    if hit is not None and hit[0] is root:
        return hit[1]
    w, h = max(1, int(round(size[0]))), max(1, int(round(size[1])))
    big = Image.new("RGBA", (w * _SS, h * _SS), (0, 0, 0, 0))
    paint(ImageDraw.Draw(big), _SS)
    img = ImageTk.PhotoImage(big.resize((w, h), Image.LANCZOS))
    if len(_IMG_CACHE) > 600:
        _IMG_CACHE.clear()
    _IMG_CACHE[key] = (root, img)
    return img


def _keep(canvas, item, photo):
    """Keep *photo* alive for as long as *item* is on *canvas*."""
    live = getattr(canvas, "_img_refs", None)
    if live is None:
        live = canvas._img_refs = {}
    try:
        present = set(canvas.find_all())
        for k in [k for k in live if k not in present]:
            del live[k]
    except tk.TclError:
        pass
    live[item] = photo


def _rr(canvas, x0, y0, x1, y1, r, fill="", outline="", width=1, tags=None,
        **_ignored):
    """Anti-aliased rounded rectangle, filled and/or outlined."""
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0:
        return None
    r = max(0.0, min(r, w / 2, h / 2))
    fill = themed(fill, "mark") or None
    outline = themed(outline, "mark") or None
    if not _PIL:
        return canvas.create_rectangle(x0, y0, x1, y1, fill=fill or "",
                                       outline=outline or "", width=width,
                                       tags=tags)
    key = ("rr", round(w, 1), round(h, 1), round(r, 1), fill, outline,
           round(width, 1))

    def paint(d, ss):
        box = [0, 0, w * ss - 1, h * ss - 1]
        d.rounded_rectangle(box, radius=r * ss, fill=_rgba(fill),
                            outline=_rgba(outline),
                            width=max(1, int(round(width * ss)))
                            if outline else 0)
    photo = _photo(key, (w, h), paint)
    item = canvas.create_image(x0, y0, anchor="nw", image=photo,
                               tags=tags)
    _keep(canvas, item, photo)
    return item


def glyph(kind, size, colour, bg=None, ring=None):
    """Small anti-aliased status glyphs: "done" (filled disc with a check),
    "current" (ring with a dot), "todo" (thin ring), "dot", "radio_on",
    "radio_off", "check_on", "check_off". Returns a PhotoImage."""
    colour, ring = themed(colour, "fg"), themed(ring, "fg")
    bg = themed(bg or "#FFFFFF", "bg")
    key = ("glyph", kind, size, colour, bg, ring)

    def paint(d, ss):
        s = size * ss
        c = _rgba(colour)
        if kind in ("done", "check_on"):
            if kind == "done":
                d.ellipse([ss, ss, s - ss, s - ss], fill=c)
            else:
                d.rounded_rectangle([ss * 0.5, ss * 0.5, s - ss * 0.5,
                                     s - ss * 0.5], radius=4 * ss, fill=c)
            pts = [(0.28 * s, 0.53 * s), (0.44 * s, 0.68 * s),
                   (0.73 * s, 0.35 * s)]
            d.line(pts, fill=(255, 255, 255, 255), width=int(1.9 * ss),
                   joint="curve")
        elif kind == "current":
            d.ellipse([ss, ss, s - ss, s - ss], outline=c, width=int(2 * ss))
            m = 0.32 * s
            d.ellipse([m, m, s - m, s - m], fill=c)
        elif kind == "todo":
            d.ellipse([1.5 * ss, 1.5 * ss, s - 1.5 * ss, s - 1.5 * ss],
                      outline=c, width=int(1.3 * ss))
        elif kind == "dot":
            m = 0.28 * s
            d.ellipse([m, m, s - m, s - m], fill=c)
        elif kind == "radio_on":
            d.ellipse([ss * 0.5, ss * 0.5, s - ss * 0.5, s - ss * 0.5],
                      fill=c)
            m = 0.33 * s
            d.ellipse([m, m, s - m, s - m], fill=(255, 255, 255, 255))
        elif kind == "radio_off":
            d.ellipse([ss * 0.6, ss * 0.6, s - ss * 0.6, s - ss * 0.6],
                      fill=_rgba(bg or "#FFFFFF"), outline=c,
                      width=int(1.3 * ss))
        elif kind == "check_off":
            d.rounded_rectangle([ss * 0.6, ss * 0.6, s - ss * 0.6,
                                 s - ss * 0.6], radius=4 * ss,
                                fill=_rgba(bg or "#FFFFFF"), outline=c,
                                width=int(1.3 * ss))
        if ring:
            d.ellipse([0, 0, s - 1, s - 1], outline=_rgba(ring),
                      width=int(2 * ss)) if kind.startswith("radio") else \
                d.rounded_rectangle([0, 0, s - 1, s - 1], radius=5 * ss,
                                    outline=_rgba(ring), width=int(2 * ss))
    return _photo(key, (size, size), paint)


def icon(kind, size, colour):
    """Line icons for navigation: "home", "open", "save", "help",
    "settings"."""
    colour = themed(colour, "fg")
    key = ("icon", kind, size, colour)

    def paint(d, ss):
        s = size * ss
        c = _rgba(colour)
        lw = max(1, int(1.6 * ss))

        def P(*pts):
            return [(x * s, y * s) for x, y in pts]
        if kind == "home":
            d.line(P((0.14, 0.50), (0.50, 0.18), (0.86, 0.50)), fill=c,
                   width=lw, joint="curve")
            d.line(P((0.26, 0.42), (0.26, 0.84), (0.74, 0.84), (0.74, 0.42)),
                   fill=c, width=lw, joint="curve")
        elif kind == "open":
            d.line(P((0.12, 0.26), (0.40, 0.26), (0.48, 0.36), (0.88, 0.36),
                     (0.88, 0.80), (0.12, 0.80), (0.12, 0.26)), fill=c,
                   width=lw, joint="curve")
        elif kind == "save":
            d.line(P((0.50, 0.14), (0.50, 0.60)), fill=c, width=lw)
            d.line(P((0.30, 0.42), (0.50, 0.62), (0.70, 0.42)), fill=c,
                   width=lw, joint="curve")
            d.line(P((0.16, 0.66), (0.16, 0.84), (0.84, 0.84), (0.84, 0.66)),
                   fill=c, width=lw, joint="curve")
        elif kind == "help":
            d.ellipse([0.10 * s, 0.10 * s, 0.90 * s, 0.90 * s], outline=c,
                      width=lw)
            d.arc([0.36 * s, 0.26 * s, 0.64 * s, 0.52 * s], 200, 90,
                  fill=c, width=lw)
            d.line(P((0.50, 0.52), (0.50, 0.60)), fill=c, width=lw)
            r = 0.05 * s
            d.ellipse([0.5 * s - r, 0.72 * s - r, 0.5 * s + r, 0.72 * s + r],
                      fill=c)
        elif kind == "settings":
            import math
            for k in range(8):
                a = k * math.pi / 4
                d.line(P((0.5 + 0.27 * math.cos(a), 0.5 + 0.27 * math.sin(a)),
                         (0.5 + 0.40 * math.cos(a), 0.5 + 0.40 * math.sin(a))),
                       fill=c, width=int(lw * 1.9))
            d.ellipse([0.22 * s, 0.22 * s, 0.78 * s, 0.78 * s], outline=c,
                      width=lw)
            d.ellipse([0.39 * s, 0.39 * s, 0.61 * s, 0.61 * s], outline=c,
                      width=lw)
    return _photo(key, (size, size), paint)



def brand_mark(size, colour, points):
    """The app's mark at sidebar size: a tile in the brand colour with the
    app's curve in white. *points* is the curve as (x, y) pairs in 0-1 of
    the tile. The full app icon is too fine to read this small."""
    key = ("brand", size, colour, tuple(points))

    def paint(d, ss):
        s = size * ss
        d.rounded_rectangle([0, 0, s - 1, s - 1], radius=0.26 * s,
                            fill=_rgba(colour))
        d.line([(x * s, y * s) for x, y in points], fill=(255, 255, 255, 255),
               width=max(1, int(0.10 * s)), joint="curve")
        r = 0.05 * s
        for x, y in (points[0], points[-1]):
            d.ellipse([x * s - r, y * s - r, x * s + r, y * s + r],
                      fill=(255, 255, 255, 255))
    return _photo(key, (size, size), paint)

def _is_light(colour) -> bool:
    c = colour.lstrip("#")
    if len(c) != 6:
        return str(colour).lower() in ("white", "#fff")
    r, g, b = (int(c[i:i + 2], 16) for i in (0, 2, 4))
    return (0.299 * r + 0.587 * g + 0.114 * b) > 170


# ══════════════════════════════════════════════════════════════════════════════
#  Buttons
# ══════════════════════════════════════════════════════════════════════════════

class RoundedButton(tk.Canvas):
    """A button in one of four variants.

    ``variant``: "primary" (filled accent), "secondary" (outlined, neutral
    text), "ghost" (text only, accent colour) or "danger". When no variant
    is given it is inferred from the colours passed, so older call sites
    that pass ``bg``/``fg`` keep working: white text means primary,
    anything else secondary. ``width=None`` sizes the button to its text.
    """

    def __init__(self, parent, text="", command=None,
                 bg=None, hover_bg=None, disabled_bg=None,
                 fg=None, disabled_fg=None,
                 width=None, height=None, radius=None, font=None,
                 variant=None, min_width=72, padding=16):
        self._text = text
        self._command = command
        self._font = font or F_BUTTON
        self._min_width = min_width
        self._padding = padding
        self._explicit = {"bg": bg, "hover_bg": hover_bg, "fg": fg,
                          "disabled_bg": disabled_bg,
                          "disabled_fg": disabled_fg}
        self._variant = variant or self._infer_variant(bg, fg)
        self._accent = dict(_ACCENT)
        h = height or CONTROL_H
        self._btn_h = h
        self._fixed_w = width
        self._btn_w = self._natural_width()
        self._r = CONTROL_R if radius is None else min(radius, CONTROL_R)
        super().__init__(parent, width=self._btn_w, height=h,
                         bg=_parent_bg(parent), bd=0, highlightthickness=0,
                         takefocus=1)
        self._state = "normal"
        self._hovered = False
        self._focused = False
        self._pressed = False
        self._draw()
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<FocusIn>", lambda _e: self._set_focus(True))
        self.bind("<FocusOut>", lambda _e: self._set_focus(False))
        self.bind("<Return>", lambda _e: self.invoke())
        self.bind("<space>", lambda _e: self.invoke())

    @staticmethod
    def _infer_variant(bg, fg):
        if fg is not None and str(fg).lower() in ("white", "#fff", "#ffffff"):
            return "primary"
        if fg is None and bg is not None and not _is_light(bg):
            return "primary"
        return "secondary"

    def _natural_width(self):
        natural = text_width(self._text, self._font) + 2 * self._padding
        if self._fixed_w:
            return max(int(self._fixed_w), natural)
        return max(self._min_width, natural)

    def _colours(self):
        a = self._accent
        v = self._variant
        ex = self._explicit
        if self._state == "disabled":
            if v in ("ghost", "link"):
                return None, None, C_DISABLED_FG
            if v == "secondary":
                return C_SURFACE, C_BORDER, C_DISABLED_FG
            return C_DISABLED_BG, None, C_DISABLED_FG
        if v == "primary":
            fill = ex["bg"] or a["accent"]
            hover = ex["hover_bg"] or a["accent_hover"]
            return (hover if (self._hovered or self._pressed) else fill,
                    None, "#FFFFFF")
        if v == "danger":
            return (mix(C_DANGER, "#000000", 0.2) if self._hovered
                    else C_DANGER), None, "#FFFFFF"
        if v in ("ghost", "link"):
            fg = a["accent"]
            fill = a["subtle"] if (self._hovered and v == "ghost") else None
            return fill, None, fg
        # secondary
        fill = "#F1F3F5" if (self._hovered or self._pressed) else C_SURFACE
        return fill, C_BORDER_STRONG, C_TEXT

    def _draw(self):
        self.delete("all")
        w, h, r = self._btn_w, self._btn_h, self._r
        fill, outline, fg = self._colours()
        focus = self._focused and self._state == "normal"
        if fill or outline or focus:
            _rr(self, 0, 0, w, h, r, fill=fill,
                outline=self._accent["ring"] if focus else outline,
                width=2 if focus else 1)
        underline = self._variant == "link" and self._hovered
        f = _font_obj(self._font)
        if underline:
            f = tkfont.Font(font=self._font)
            f.configure(underline=1)
        self.create_text(w / 2, h / 2, text=self._text, fill=fg, font=f)
        self._font_ref = f

    # events
    def _on_enter(self, _e):
        if self._state == "normal":
            self._hovered = True
            self._draw()

    def _on_leave(self, _e):
        if self._hovered or self._pressed:
            self._hovered = self._pressed = False
            self._draw()

    def _on_press(self, _e):
        if self._state == "normal":
            self._pressed = True
            self._draw()

    def _on_release(self, e):
        was = self._pressed
        self._pressed = False
        if self._state != "normal":
            return
        self._draw()
        inside = 0 <= e.x <= self._btn_w and 0 <= e.y <= self._btn_h
        if was and inside and self._command:
            self._command()

    def _set_focus(self, on):
        self._focused = on
        self._draw()

    def invoke(self):
        if self._state == "normal" and self._command:
            self._command()

    # compatibility: tests and older code call these directly
    def _on_click(self, _e=None):
        self.invoke()

    def configure(self, cnf=None, **kw):
        redraw = resize = False
        if "state" in kw:
            new_state = kw.pop("state")
            if new_state != self._state:
                self._state = new_state
                self._hovered = self._pressed = False
                redraw = True
        if "text" in kw:
            new_text = kw.pop("text")
            if new_text != self._text:
                self._text = new_text
                redraw = resize = True
        if "command" in kw:
            self._command = kw.pop("command")
        if "variant" in kw:
            self._variant = kw.pop("variant")
            redraw = True
        for key in ("bg", "hover_bg", "fg", "disabled_bg", "disabled_fg"):
            if key in kw:
                self._explicit[key] = kw.pop(key)
                redraw = True
        if "accent" in kw:
            self._accent = dict(kw.pop("accent"))
            redraw = True
        if kw:
            super().configure(**kw)
        if resize:
            self._btn_w = self._natural_width()
            super().configure(width=self._btn_w)
        if redraw:
            self._draw()
    config = configure

    def cget(self, key):
        if key == "text":
            return self._text
        if key == "state":
            return self._state
        return super().cget(key)


# ══════════════════════════════════════════════════════════════════════════════
#  Text entry
# ══════════════════════════════════════════════════════════════════════════════

class RoundedEntry(tk.Frame):
    """Single-line text field. Expands with its container unless
    ``fixed_width`` is given."""

    def __init__(self, parent, textvariable=None, font=None,
                 height=None, radius=None, bg=None, border=None, focus=None,
                 fg=None, fixed_width=None, mono=False, placeholder="",
                 show_end=False):
        """*show_end* keeps the end of a long value in view while the field
        is not being edited: for a path, the part that names the file."""
        super().__init__(parent, bg=_parent_bg(parent))
        self._height = height or CONTROL_H
        self._radius = CONTROL_R if radius is None else min(radius, CONTROL_R)
        self._bg = bg or C_SURFACE
        self._border = border or C_BORDER
        self._focus = focus or _ACCENT["accent"]
        self._ring = _ACCENT["ring"]
        self._state_now = "rest"
        self._last_w = None
        self._placeholder = placeholder

        opts = dict(height=self._height, bg=_parent_bg(parent), bd=0,
                    highlightthickness=0)
        if fixed_width:
            self.canvas = tk.Canvas(self, width=fixed_width, **opts)
            self.canvas.pack()
        else:
            self.canvas = tk.Canvas(self, **opts)
            self.canvas.pack(fill="x", expand=True)

        if font is None:
            from design import F_MONO
            font = F_MONO if mono else F_BODY
        self.entry = tk.Entry(self.canvas, textvariable=textvariable,
                              font=font, relief="flat", bd=0, width=1,
                              bg=self._bg, fg=(fg or C_TEXT),
                              disabledbackground=C_SURFACE_ALT,
                              disabledforeground=C_TEXT_3,
                              insertbackground=C_TEXT, insertwidth=1,
                              highlightthickness=0)
        self._pad = 10
        self._entry_id = self.canvas.create_window(
            self._pad, self._height // 2, window=self.entry, width=200,
            anchor="w", tags=("entry_win",))
        self.entry.bind("<FocusIn>", lambda _e: self._paint("focus"))
        self.entry.bind("<FocusOut>", lambda _e: self._paint("rest"))
        self.entry.bind("<Enter>", lambda _e: self._hover(True))
        self.entry.bind("<Leave>", lambda _e: self._hover(False))
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", lambda _e: self.entry.focus_set())
        self._show_end = bool(show_end and textvariable is not None)
        if self._show_end:
            var = textvariable
            trace = var.trace_add("write", lambda *_a: self._to_end())

            def _forget(event, v=var, t=trace):
                if event.widget is self:
                    self._cancel_end()
                    try:
                        v.trace_remove("write", t)
                    except (tk.TclError, ValueError):
                        pass
            self.bind("<Destroy>", _forget, add="+")
            self.entry.bind("<FocusOut>", lambda _e: self._to_end(), add="+")
            self._to_end()

    def _to_end(self):
        if getattr(self, "_end_job", None):
            return

        def move():
            self._end_job = None
            try:
                if self.entry.focus_get() is not self.entry:
                    self.entry.xview_moveto(1.0)
            except (tk.TclError, KeyError):
                pass
        # Scheduled on the root window, and cancelled when the field is
        # destroyed first, so the callback never outlives its window.
        try:
            self._end_job = self._root().after_idle(move)
        except tk.TclError:
            self._end_job = None

    def _cancel_end(self):
        job, self._end_job = getattr(self, "_end_job", None), None
        if job:
            try:
                self._root().after_cancel(job)
            except tk.TclError:
                pass

    def _hover(self, on):
        if self._state_now != "focus":
            self._paint("hover" if on else "rest")

    def _on_resize(self, event):
        if event.width == self._last_w:
            return
        self._last_w = event.width
        self.canvas.itemconfig(self._entry_id,
                               width=max(10, event.width - 2 * self._pad))
        self._paint(self._state_now)
        if self._show_end:
            self._to_end()

    def _paint(self, state):
        self._state_now = state
        c = self.canvas
        c.delete("bg")
        w = c.winfo_width() or 200
        h = self._height
        if state == "focus":
            _rr(c, 1, 1, w - 1, h - 1, self._radius, fill=self._bg,
                outline=self._focus, width=1.5, tags="bg")
        else:
            border = C_BORDER_STRONG if state == "hover" else self._border
            _rr(c, 1, 1, w - 1, h - 1, self._radius, fill=self._bg,
                outline=border, width=1, tags="bg")
        c.tag_lower("bg")

    def configure(self, cnf=None, **kw):
        if "state" in kw:
            self.entry.configure(state=kw.pop("state"))
        if kw:
            super().configure(**kw)
    config = configure


# ══════════════════════════════════════════════════════════════════════════════
#  Dropdown
# ══════════════════════════════════════════════════════════════════════════════

class RoundedCombobox(tk.Frame):
    """Dropdown bound to a StringVar; calls ``on_select(value)``.

    ``display`` maps a stored value to the text shown (used to translate
    fixed option labels while the variable keeps its canonical value).
    """

    def __init__(self, parent, values=None, textvariable=None,
                 height=None, radius=None, bg=None, border=None, focus=None,
                 fg=None, on_select=None, fixed_width=None, display=None,
                 font=None):
        super().__init__(parent, bg=_parent_bg(parent))
        self._values = list(values or [])
        self._var = textvariable or tk.StringVar()
        self._height = height or CONTROL_H
        self._radius = CONTROL_R if radius is None else min(radius, CONTROL_R)
        self._bg = bg or C_SURFACE
        self._border = border or C_BORDER
        self._focus = focus or _ACCENT["accent"]
        self._fg = fg or C_TEXT
        self._on_select = on_select
        self._display = display or (lambda v: v)
        self._font = font or F_BODY
        self._state = "readonly"
        self._hovered = False
        self._last_w = None

        opts = dict(height=self._height, bg=_parent_bg(parent), bd=0,
                    highlightthickness=0, takefocus=1)
        if fixed_width:
            self.canvas = tk.Canvas(self, width=fixed_width, **opts)
            self.canvas.pack()
        else:
            self.canvas = tk.Canvas(self, **opts)
            self.canvas.pack(fill="x", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Return>", self._on_click)
        self.canvas.bind("<space>", self._on_click)
        self.canvas.bind("<FocusIn>", lambda _e: self._draw())
        self.canvas.bind("<FocusOut>", lambda _e: self._draw())
        self._trace = self._var.trace_add("write", lambda *_: self._draw())

    def _on_resize(self, event):
        if event.width == self._last_w:
            return
        self._last_w = event.width
        self._draw()

    def _on_enter(self, _e):
        if self._state != "disabled":
            self._hovered = True
            self._draw()

    def _on_leave(self, _e):
        self._hovered = False
        self._draw()

    def _on_click(self, _e=None):
        if self._state == "disabled" or not self._values:
            return
        menu = tk.Menu(self, tearoff=0, font=self._font)
        current = self._var.get()
        for v in self._values:
            label = self._display(v)
            if v == current and sys.platform != "darwin":
                label = f"✓  {label}"
            menu.add_command(label=label, command=lambda vv=v: self._select(vv))
        x = self.canvas.winfo_rootx()
        y = self.canvas.winfo_rooty() + self._height + 2
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _select(self, value):
        self._var.set(value)
        if self._on_select:
            self._on_select(value)

    def configure(self, **kw):
        redraw = False
        if "state" in kw:
            self._state = kw.pop("state")
            self._hovered = False
            redraw = True
        if "values" in kw:
            self._values = list(kw.pop("values"))
            redraw = True
        if "display" in kw:
            self._display = kw.pop("display")
            redraw = True
        if kw:
            super().configure(**kw)
        if redraw:
            self._draw()
    config = configure

    def get(self):
        return self._var.get()

    def _draw(self):
        c = self.canvas
        try:
            c.delete("all")
        except tk.TclError:
            return
        w = c.winfo_width() or 300
        h = self._height
        disabled = self._state == "disabled"
        focused = str(c.focus_get()) == str(c) if c.winfo_exists() else False
        if disabled:
            bg, fg, bd = C_SURFACE_ALT, C_DISABLED_FG, C_BORDER
        elif focused:
            bg, fg, bd = self._bg, self._fg, self._focus
        elif self._hovered:
            bg, fg, bd = self._bg, self._fg, C_BORDER_STRONG
        else:
            bg, fg, bd = self._bg, self._fg, self._border
        _rr(c, 1, 1, w - 1, h - 1, self._radius, fill=bg, outline=bd,
            width=1.5 if focused else 1)
        # chevron
        cx, cy = w - 14, h / 2
        c.create_line(cx - 4, cy - 2, cx, cy + 2, cx + 4, cy - 2,
                      fill=C_TEXT_3 if not disabled else C_DISABLED_FG,
                      width=1.6, capstyle="round", joinstyle="round")
        text = self._display(self._var.get() or "")
        f = _font_obj(self._font)
        max_w = w - 12 - 28
        if max_w > 20 and f.measure(text) > max_w:
            while text and f.measure(text + "…") > max_w:
                text = text[:-1]
            text += "…"
        c.create_text(11, h / 2, text=text, anchor="w", font=self._font,
                      fill=fg)


# ══════════════════════════════════════════════════════════════════════════════
#  Check box and radio button
# ══════════════════════════════════════════════════════════════════════════════

class _Toggle(tk.Frame):
    _SIZE = 16

    def __init__(self, parent, text="", variable=None, command=None,
                 font=None, fg=None, bg=None, wraplength=None, anchor="w"):
        bg = bg or _parent_bg(parent)
        super().__init__(parent, bg=bg)
        self._command = command
        self._state = "normal"
        self._fg = fg or C_TEXT
        self._accent = dict(_ACCENT)
        self._hovered = False
        s = self._SIZE
        self._box = tk.Canvas(self, width=s + 2, height=s + 2, bg=bg, bd=0,
                              highlightthickness=0, takefocus=1)
        self._box.pack(side="left", anchor="n", pady=(2, 0))
        self._label = None
        if text:
            kw = {"wraplength": wraplength} if wraplength else {}
            self._label = tk.Label(self, text=text, font=font or F_BODY,
                                   fg=self._fg, bg=bg, anchor=anchor,
                                   justify="left", **kw)
            self._label.pack(side="left", padx=(8, 0), fill="x")
        for w in (self, self._box) + ((self._label,) if self._label else ()):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", lambda _e: self._hover(True))
            w.bind("<Leave>", lambda _e: self._hover(False))
        self._box.bind("<space>", self._click)
        self._box.bind("<FocusIn>", lambda _e: self._draw())
        self._box.bind("<FocusOut>", lambda _e: self._draw())

    def _hover(self, on):
        self._hovered = on and self._state == "normal"
        self._draw()

    def _click(self, _e=None):
        if self._state != "normal":
            return
        self._toggle()
        if self._command:
            self._command()

    def configure(self, cnf=None, **kw):
        if "state" in kw:
            self._state = kw.pop("state")
            if self._label is not None:
                locked_on = (self._state == "disabled"
                             and self._is_on())
                self._label.configure(
                    fg=(C_TEXT_2 if locked_on else C_DISABLED_FG)
                    if self._state == "disabled" else self._fg)
            self._draw()
        if "text" in kw and self._label is not None:
            self._label.configure(text=kw.pop("text"))
        if "command" in kw:
            self._command = kw.pop("command")
        if kw:
            super().configure(**kw)
    config = configure

    def cget(self, key):
        if key == "state":
            return self._state
        if key == "text":
            return self._label.cget("text") if self._label else ""
        return super().cget(key)

    def _focused(self):
        try:
            return str(self._box.focus_get()) == str(self._box)
        except (tk.TclError, KeyError):
            return False


class CheckBox(_Toggle):
    def __init__(self, parent, text="", variable=None, command=None, **kw):
        self._var = variable if variable is not None else tk.BooleanVar()
        super().__init__(parent, text, self._var, command, **kw)
        self._trace = self._var.trace_add("write", lambda *_: self._draw())
        self._draw()

    def _toggle(self):
        self._var.set(not bool(self._var.get()))

    def _is_on(self):
        return bool(self._var.get())

    def invoke(self):
        self._click()

    def _draw(self):
        c = self._box
        try:
            c.delete("all")
        except tk.TclError:
            return
        s = self._SIZE + 2
        on = bool(self._var.get())
        disabled = self._state == "disabled"
        a = self._accent
        ring = a["ring"] if self._focused() else None
        if on:
            colour = mix(a["accent"], "#FFFFFF", 0.45) if disabled \
                else a["accent"]
            img = glyph("check_on", s, colour, ring=ring)
        else:
            outline = (C_BORDER if disabled else
                       (a["accent"] if self._hovered else C_BORDER_STRONG))
            img = glyph("check_off", s, outline,
                        bg=C_SURFACE_ALT if disabled else C_SURFACE,
                        ring=ring)
        item = c.create_image(0, 0, anchor="nw", image=img)
        _keep(c, item, img)


class RadioButton(_Toggle):
    def __init__(self, parent, text="", variable=None, value=None,
                 command=None, **kw):
        self._var = variable if variable is not None else tk.StringVar()
        self._value = value
        super().__init__(parent, text, self._var, command, **kw)
        self._trace = self._var.trace_add("write", lambda *_: self._draw())
        self._draw()

    def _toggle(self):
        self._var.set(self._value)

    def _is_on(self):
        return self._var.get() == self._value

    def invoke(self):
        self._click()

    def _draw(self):
        c = self._box
        try:
            c.delete("all")
        except tk.TclError:
            return
        s = self._SIZE + 2
        on = self._var.get() == self._value
        disabled = self._state == "disabled"
        a = self._accent
        ring = a["ring"] if self._focused() else None
        if on:
            colour = mix(a["accent"], "#FFFFFF", 0.45) if disabled \
                else a["accent"]
            img = glyph("radio_on", s, colour, ring=ring)
        else:
            outline = (C_BORDER if disabled else
                       (a["accent"] if self._hovered else C_BORDER_STRONG))
            img = glyph("radio_off", s, outline,
                        bg=C_SURFACE_ALT if disabled else C_SURFACE,
                        ring=ring)
        item = c.create_image(0, 0, anchor="nw", image=img)
        _keep(c, item, img)


# ══════════════════════════════════════════════════════════════════════════════
#  Segmented control
# ══════════════════════════════════════════════════════════════════════════════

class SegmentedControl(tk.Canvas):
    """Mutually exclusive segments. ``options`` is a list of
    ``(value, label)``; the StringVar holds the selected value."""

    def __init__(self, parent, options, variable, command=None, font=None,
                 height=None, stretch=False):
        self._opts = list(options)
        self._var = variable
        self._command = command
        self._font = font or F_SMALL_B
        self._h = height or CONTROL_H
        self._stretch = stretch
        self._hover = None
        super().__init__(parent, height=self._h, bg=_parent_bg(parent),
                         bd=0, highlightthickness=0)
        self._widths = [text_width(lbl, self._font) + 28
                        for _v, lbl in self._opts]
        if not stretch:
            self.configure(width=sum(self._widths) + 4)
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<Button-1>", self._click)
        self.bind("<Motion>", self._motion)
        self.bind("<Leave>", lambda _e: self._set_hover(None))
        self._trace = self._var.trace_add("write", lambda *_: self._draw())
        self._draw()

    def _layout(self):
        total = self.winfo_width() if self._stretch else sum(self._widths) + 4
        total = max(total, sum(self._widths) + 4)
        extra = (total - 4 - sum(self._widths)) / max(1, len(self._widths))
        xs, x = [], 2
        for w in self._widths:
            xs.append((x, x + w + extra))
            x += w + extra
        return xs

    def _index_at(self, x):
        for i, (x0, x1) in enumerate(self._layout()):
            if x0 <= x <= x1:
                return i
        return None

    def _motion(self, e):
        self._set_hover(self._index_at(e.x))

    def _set_hover(self, i):
        if i != self._hover:
            self._hover = i
            self._draw()

    def _click(self, e):
        i = self._index_at(e.x)
        if i is None:
            return
        value = self._opts[i][0]
        if value != self._var.get():
            self._var.set(value)
            if self._command:
                self._command(value)

    def _draw(self):
        try:
            self.delete("all")
        except tk.TclError:
            return
        h = self._h
        spans = self._layout()
        right = spans[-1][1] + 2 if spans else 4
        _rr(self, 0, 0, right, h, CONTROL_R + 1, fill=C_SEG_TRACK)
        cur = self._var.get()
        for i, ((value, label), (x0, x1)) in enumerate(zip(self._opts, spans)):
            sel = value == cur
            if sel:
                _rr(self, x0, 2, x1, h - 2, CONTROL_R, fill=C_SURFACE,
                    outline=C_BORDER)
            elif i == self._hover:
                _rr(self, x0, 2, x1, h - 2, CONTROL_R, fill=C_SIDEBAR_HOVER_SEG,
                    outline=C_SIDEBAR_HOVER_SEG)
            self.create_text((x0 + x1) / 2, h / 2, text=label,
                             font=self._font,
                             fill=C_TEXT if sel else C_TEXT_2)


C_SIDEBAR_HOVER_SEG = "#D8DCE2"
C_SEG_TRACK = "#E3E6EA"


# ══════════════════════════════════════════════════════════════════════════════
#  Layout helpers
# ══════════════════════════════════════════════════════════════════════════════

def card(parent, padx=0, pady=0, **pack):
    """A white surface with a hairline border."""
    f = tk.Frame(parent, bg=C_SURFACE, highlightthickness=1,
                 highlightbackground=C_BORDER, highlightcolor=C_BORDER)
    if pack is not None and pack != {}:
        f.pack(**pack)
    return f


def divider(parent, bg=None, padx=0, pady=0):
    line = tk.Frame(parent, height=1, bg=C_DIVIDER)
    line.pack(fill="x", padx=padx, pady=pady)
    return line


class ScrollFrame(tk.Frame):
    """A vertically scrolling container; put content in ``.inner``.

    The mouse wheel scrolls whichever ScrollFrame the pointer is over, on
    macOS, Windows and Linux alike.
    """

    def __init__(self, parent, bg=None, **kw):
        bg = bg or _parent_bg(parent)
        super().__init__(parent, bg=bg, **kw)
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self.bar = tk.Scrollbar(self, orient="vertical",
                                command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner,
                                              anchor="nw")
        self.inner.bind("<Configure>", self._sync)
        self.canvas.bind("<Configure>", self._on_canvas)
        self.canvas.bind("<Enter>", lambda _e: self._bind_wheel(True))
        self.canvas.bind("<Leave>", lambda _e: self._bind_wheel(False))
        self._bar_shown = False

    def _on_scroll(self, lo, hi):
        self.bar.set(lo, hi)
        need = not (float(lo) <= 0.0 and float(hi) >= 1.0)
        if need != self._bar_shown:
            self._bar_shown = need
            if need:
                self.bar.pack(side="right", fill="y", before=self.canvas)
            else:
                self.bar.pack_forget()

    def _sync(self, _e=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas(self, e):
        self.canvas.itemconfigure(self._win, width=e.width)

    def _wheel(self, event):
        if getattr(event, "num", None) == 4:
            step = -1
        elif getattr(event, "num", None) == 5:
            step = 1
        elif sys.platform == "darwin":
            step = -event.delta
        else:
            step = -int(event.delta / 120) or (-1 if event.delta > 0 else 1)
        if self._bar_shown:
            self.canvas.yview_scroll(step, "units")

    def _bind_wheel(self, on):
        seqs = ("<MouseWheel>", "<Button-4>", "<Button-5>")
        for s in seqs:
            if on:
                self.canvas.bind_all(s, self._wheel)
            else:
                self.canvas.unbind_all(s)

    def scroll_top(self):
        self.canvas.yview_moveto(0)


class FlatScrollbar(tk.Canvas):
    """A slim scroll bar drawn on a canvas, with the same interface as
    tk.Scrollbar (``set``, ``get``, ``command``, ``orient``). Used in the
    dark appearance, where the native one would stay light."""

    _DROP = ("troughcolor", "activebackground", "elementborderwidth",
             "relief", "jump", "repeatdelay", "repeatinterval",
             "borderwidth", "bd", "highlightthickness", "bg", "background",
             "activerelief", "highlightbackground", "highlightcolor")

    def __init__(self, master=None, **kw):
        self._orient = str(kw.pop("orient", "vertical"))
        self._command = kw.pop("command", None)
        thick = int(kw.pop("width", 12) or 12)
        for key in self._DROP:
            kw.pop(key, None)
        size = ({"width": thick} if self._vertical()
                else {"height": thick})
        super().__init__(master, bd=0, highlightthickness=0,
                         bg=_parent_bg(master), **size, **kw)
        self._lo, self._hi = 0.0, 1.0
        self._grab = None
        self._hover = False
        self.bind("<Configure>", lambda _e: self._draw())
        self.bind("<ButtonPress-1>", self._press)
        self.bind("<B1-Motion>", self._drag)
        self.bind("<ButtonRelease-1>", lambda _e: self._release())
        self.bind("<Enter>", lambda _e: self._set_hover(True))
        self.bind("<Leave>", lambda _e: self._set_hover(False))

    def _vertical(self):
        return not self._orient.startswith("h")

    def _length(self):
        return (self.winfo_height() if self._vertical()
                else self.winfo_width())

    def _thumb(self):
        n = max(1, self._length())
        a = self._lo * n
        b = max(a + 24, self._hi * n)
        if b > n:
            a, b = max(0, n - (b - a)), n
        return a, b

    def _draw(self):
        try:
            self.delete("all")
        except tk.TclError:
            return
        if self._lo <= 0.0 and self._hi >= 1.0:
            return
        a, b = self._thumb()
        t = self.winfo_width() if self._vertical() else self.winfo_height()
        pad = 3
        colour = C_TEXT_3 if (self._hover or self._grab is not None) \
            else C_BORDER_STRONG
        if self._vertical():
            _rr(self, pad, a + pad, t - pad, b - pad, (t - 2 * pad) / 2,
                fill=colour)
        else:
            _rr(self, a + pad, pad, b - pad, t - pad, (t - 2 * pad) / 2,
                fill=colour)

    def _set_hover(self, on):
        self._hover = on
        self._draw()

    def _pos(self, e):
        return e.y if self._vertical() else e.x

    def _press(self, e):
        a, b = self._thumb()
        p = self._pos(e)
        if a <= p <= b:
            self._grab = p - a
        elif self._command:
            self._command("scroll", -1 if p < a else 1, "pages")
        self._draw()

    def _drag(self, e):
        if self._grab is None or not self._command:
            return
        n = max(1, self._length())
        self._command("moveto", max(0.0, (self._pos(e) - self._grab) / n))

    def _release(self):
        self._grab = None
        self._draw()

    def set(self, lo, hi):
        self._lo, self._hi = float(lo), float(hi)
        self._draw()

    def get(self):
        return self._lo, self._hi

    def configure(self, cnf=None, **kw):
        kw = dict(cnf or {}, **kw)
        if "command" in kw:
            self._command = kw.pop("command")
        if "orient" in kw:
            self._orient = str(kw.pop("orient"))
        for key in self._DROP:
            kw.pop(key, None)
        if kw:
            super().configure(**kw)
        self._draw()
    config = configure


# ══════════════════════════════════════════════════════════════════════════════
#  Progress bar and slider
# ══════════════════════════════════════════════════════════════════════════════

def _make_gradient(canvas, width, height, color_left, color_right, y0=0):
    r1, g1, b1 = canvas.winfo_rgb(color_left)
    r2, g2, b2 = canvas.winfo_rgb(color_right)
    for x in range(width):
        t = x / max(width - 1, 1)
        r = int(r1 + (r2 - r1) * t) >> 8
        g = int(g1 + (g2 - g1) * t) >> 8
        b = int(b1 + (b2 - b1) * t) >> 8
        canvas.create_line(x, y0, x, y0 + height,
                           fill=f"#{r:02x}{g:02x}{b:02x}")


class GradientProgressBar(tk.Frame):
    """Rounded progress bar filled with the active mode's gradient."""

    def __init__(self, parent, width=BAR_W, height=BAR_H, bg=None, **kw):
        super().__init__(parent, bg=(bg or _parent_bg(parent)), **kw)
        self._bar_width = width
        self._bar_height = height
        self._pct = 0.0
        self._grad_start = C_PROGRESS_END
        self._grad_end = C_PROGRESS_START
        self._canvas = tk.Canvas(self, width=width, height=height, bd=0,
                                 highlightthickness=0,
                                 bg=(bg or _parent_bg(parent)))
        self._canvas.pack()
        self._draw()

    def _draw(self):
        c = self._canvas
        c.delete("all")
        w, h = self._bar_width, self._bar_height
        _rr(c, 0, 0, w, h, h / 2, fill=C_DIVIDER, outline=C_DIVIDER)
        fill_w = int(w * self._pct / 100)
        if fill_w <= 0:
            return
        r = h / 2
        r1, g1, b1 = c.winfo_rgb(self._grad_start)
        r2, g2, b2 = c.winfo_rgb(self._grad_end)
        for x in range(fill_w):
            # vertical extent of a pill shape at column x, so both ends of
            # the filled part are rounded like the track under it
            d = min(x + 0.5, fill_w - x - 0.5)
            inset = r - (r * r - (r - d) ** 2) ** 0.5 if d < r else 0.0
            t = x / max(fill_w - 1, 1)
            col = "#%02x%02x%02x" % (int(r1 + (r2 - r1) * t) >> 8,
                                     int(g1 + (g2 - g1) * t) >> 8,
                                     int(b1 + (b2 - b1) * t) >> 8)
            c.create_line(x, inset, x, h - inset, fill=col)

    def set(self, value: float):
        self._pct = max(0.0, min(100.0, value))
        self._draw()

    def set_theme(self, start_colour: str, end_colour: str):
        self._grad_start = start_colour
        self._grad_end = end_colour
        self._draw()


class RoundedSlider(tk.Canvas):
    """Slim slider with a rounded track and a circular thumb."""

    def __init__(self, parent, variable=None, from_=0, to=100,
                 width=460, height=6, radius=3,
                 track_bg=C_DIVIDER, track_fill=None,
                 thumb_fill="white", thumb_border=None,
                 command=None):
        canvas_h = 24
        super().__init__(parent, width=width, height=canvas_h,
                         bg=_parent_bg(parent), bd=0, highlightthickness=0)
        self._var = variable or tk.IntVar(value=from_)
        self._from, self._to = from_, to
        self._width = width
        self._height = height
        self._radius = radius
        self._track_bg = track_bg
        self._track_fill = track_fill or _ACCENT["accent"]
        self._thumb_fill = thumb_fill
        self._thumb_border = thumb_border or _ACCENT["accent"]
        self._command = command
        self._thumb_r = 8
        self._pad_x = self._thumb_r + 2
        self._track_y = canvas_h // 2
        self._draw()
        self.bind("<Button-1>", self._on_click)
        self.bind("<B1-Motion>", self._on_click)
        self.bind("<Configure>", self._on_resize)
        self._var.trace_add("write", lambda *_: self._draw())

    def _on_resize(self, event):
        if event.width > 0 and event.width != self._width:
            self._width = event.width
            self._draw()

    def _value_to_x(self, v):
        span_x = self._width - 2 * self._pad_x
        frac = (v - self._from) / max(1, self._to - self._from)
        return self._pad_x + max(0.0, min(1.0, frac)) * span_x

    def _x_to_value(self, x):
        span_x = self._width - 2 * self._pad_x
        frac = max(0.0, min(1.0, (x - self._pad_x) / max(1, span_x)))
        return int(round(self._from + frac * (self._to - self._from)))

    def _draw(self):
        self.delete("all")
        w, y, r = self._width, self._track_y, self._height / 2
        _rr(self, self._pad_x, y - r, w - self._pad_x, y + r, r,
            fill=self._track_bg, outline=self._track_bg)
        val = int(self._var.get() or self._from)
        tx = self._value_to_x(val)
        if tx > self._pad_x:
            _rr(self, self._pad_x, y - r, tx, y + r, r,
                fill=self._track_fill, outline=self._track_fill)
        tr = self._thumb_r
        self.create_oval(tx - tr, y - tr, tx + tr, y + tr,
                         fill=self._thumb_fill, outline=self._thumb_border,
                         width=2)

    def _on_click(self, event):
        new_v = self._x_to_value(event.x)
        if new_v != int(self._var.get() or self._from):
            self._var.set(new_v)
            if self._command:
                self._command(new_v)


# ══════════════════════════════════════════════════════════════════════════════
#  Help dialog
# ══════════════════════════════════════════════════════════════════════════════

def show_help_dialog(root, title, subtitle, entries, window_title="Help",
                     close_text="Close"):
    """Modal help: a heading, then one collapsible section per entry
    (``(title, body)``), the first one open."""
    from design import F_BODY_B, F_SECTION, SP_1, SP_2, SP_3, SP_4, SP_6
    a = _ACCENT
    win = tk.Toplevel(root)
    win.title(window_title)
    win.configure(bg=C_SURFACE)
    try:
        root.update_idletasks()
        rw, rh = max(600, root.winfo_width()), max(480, root.winfo_height())
        w, h = min(680, int(rw * 0.7)), min(620, int(rh * 0.82))
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = max(20, root.winfo_rooty() + (root.winfo_height() - h) // 3)
        win.geometry(f"{w}x{h}+{x}+{y}")
    except tk.TclError:
        w, h = 640, 560
        win.geometry(f"{w}x{h}")
    win.transient(root)
    win.grab_set()

    head = tk.Frame(win, bg=C_SURFACE)
    head.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))
    tk.Label(head, text=title, font=F_SECTION, fg=C_TEXT, bg=C_SURFACE,
             anchor="w").pack(anchor="w")
    if subtitle:
        tk.Label(head, text=subtitle, font=F_SMALL, fg=C_TEXT_2,
                 bg=C_SURFACE, anchor="w").pack(anchor="w", pady=(2, 0))

    foot = tk.Frame(win, bg=C_SURFACE)
    foot.pack(side="bottom", fill="x", padx=SP_6, pady=(SP_3, SP_4))
    tk.Frame(win, height=1, bg=C_DIVIDER).pack(side="bottom", fill="x")
    RoundedButton(foot, text=close_text, command=win.destroy,
                  variant="primary", min_width=96).pack(side="right")
    tk.Frame(win, height=1, bg=C_DIVIDER).pack(fill="x", pady=(SP_2, 0))

    area = ScrollFrame(win, bg=C_SURFACE)
    area.pack(fill="both", expand=True)
    body = area.inner
    labels = []

    def _wrap(_e=None):
        width = max(260, area.winfo_width() - 2 * SP_6 - 30)
        for lbl in labels:
            try:
                lbl.configure(wraplength=width)
            except tk.TclError:
                pass
    area.bind("<Configure>", _wrap)

    for i, (sec_title, sec_body) in enumerate(entries):
        section = tk.Frame(body, bg=C_SURFACE)
        section.pack(fill="x", padx=SP_6, pady=(SP_4 if i == 0 else SP_2, 0))
        state = {"open": i == 0}
        row = tk.Frame(section, bg=C_SURFACE)
        row.pack(fill="x")
        chevron = tk.Canvas(row, width=14, height=14, bg=C_SURFACE, bd=0,
                            highlightthickness=0)
        chevron.pack(side="left", padx=(0, SP_2))
        title_lbl = tk.Label(row, text=sec_title, font=F_BODY_B, fg=C_TEXT,
                             bg=C_SURFACE, anchor="w", justify="left")
        title_lbl.pack(side="left", fill="x", expand=True)
        body_lbl = tk.Label(section, text=sec_body, font=F_BODY,
                            fg=C_TEXT_2, bg=C_SURFACE, anchor="w",
                            justify="left", wraplength=w - 100)
        labels.append(body_lbl)

        def draw_chevron(c=chevron, st=state):
            c.delete("all")
            if st["open"]:
                c.create_line(3, 5, 7, 9, 11, 5, fill=a["accent"], width=1.8,
                              capstyle="round", joinstyle="round")
            else:
                c.create_line(5, 3, 9, 7, 5, 11, fill=C_TEXT_3, width=1.8,
                              capstyle="round", joinstyle="round")

        def toggle(_e=None, st=state, lbl=body_lbl, draw=draw_chevron):
            st["open"] = not st["open"]
            draw()
            if st["open"]:
                lbl.pack(anchor="w", fill="x", padx=(22, 0), pady=(SP_1, 0))
            else:
                lbl.pack_forget()

        draw_chevron()
        if state["open"]:
            body_lbl.pack(anchor="w", fill="x", padx=(22, 0), pady=(SP_1, 0))
        for widget in (row, chevron, title_lbl):
            widget.bind("<Button-1>", toggle)
    tk.Frame(body, bg=C_SURFACE, height=SP_4).pack(fill="x")
    win.bind("<Escape>", lambda _e: win.destroy())
    return win


def show_settings_dialog(root, on_language, on_appearance, reopen=None):
    """Modal settings: the interface language and the appearance (light,
    dark, or the one the operating system is set to). Choosing an option
    closes the dialog and calls ``on_language(code)`` or
    ``on_appearance(mode)``, which redraw the window in place; *reopen*,
    when given, is then called so the dialog comes back in the new
    language or appearance."""
    from design import (APPEARANCES, F_BODY_B, F_SECTION, SP_1, SP_2, SP_3,
                        SP_4, SP_6, appearance)
    from i18n import LANGUAGES, language, tr
    win = tk.Toplevel(root)
    win.title(tr("Settings"))
    win.configure(bg=C_SURFACE)
    win.resizable(False, False)
    win.transient(root)

    head = tk.Frame(win, bg=C_SURFACE)
    head.pack(fill="x", padx=SP_6, pady=(SP_6, SP_2))
    tk.Label(head, text=tr("Settings"), font=F_SECTION, fg=C_TEXT,
             bg=C_SURFACE, anchor="w").pack(anchor="w")

    def choose(callback, value, current):
        if value == current:
            return
        win.destroy()
        callback(value)
        if reopen is not None:
            root.after(30, reopen)

    def section(title, options, current, callback, note=None):
        box = tk.Frame(win, bg=C_SURFACE)
        box.pack(fill="x", padx=SP_6, pady=(SP_4, 0))
        tk.Label(box, text=title, font=F_BODY_B, fg=C_TEXT, bg=C_SURFACE,
                 anchor="w").pack(anchor="w", pady=(0, SP_2))
        var = tk.StringVar(value=current)
        SegmentedControl(box, options, var, height=30,
                         command=lambda v: choose(callback, v,
                                                  current)).pack(anchor="w")
        if note:
            tk.Label(box, text=note, font=F_SMALL, fg=C_TEXT_2, bg=C_SURFACE,
                     anchor="w", justify="left",
                     wraplength=340).pack(anchor="w", pady=(SP_1, 0))

    section(tr("Language"), list(LANGUAGES), language(), on_language)
    section(tr("Appearance"), [(c, tr(n)) for c, n in APPEARANCES],
            appearance(), on_appearance,
            note=tr("Match system follows the light or dark setting of "
                    "your computer."))

    tk.Frame(win, height=1, bg=C_DIVIDER).pack(fill="x", pady=(SP_6, 0))
    foot = tk.Frame(win, bg=C_SURFACE)
    foot.pack(fill="x", padx=SP_6, pady=(SP_3, SP_4))
    RoundedButton(foot, text=tr("Close"), command=win.destroy,
                  variant="primary", min_width=96).pack(side="right")
    win.bind("<Escape>", lambda _e: win.destroy())
    try:
        win.update_idletasks()
        w, h = max(400, win.winfo_reqwidth()), win.winfo_reqheight()
        x = root.winfo_rootx() + (root.winfo_width() - w) // 2
        y = max(20, root.winfo_rooty() + (root.winfo_height() - h) // 3)
        win.geometry(f"{w}x{h}+{x}+{y}")
        win.grab_set()
    except tk.TclError:
        pass
    return win


def watch_system_appearance(root, on_change):
    """Under the "system" appearance, check the operating system's
    setting whenever the window comes to the front, and call
    ``on_change()`` when it has changed so the window can redraw."""
    from design import refresh_system_appearance

    def check(event):
        if event.widget is not root:
            return
        try:
            changed = refresh_system_appearance()
        except Exception:                           # noqa: BLE001
            changed = False
        if changed:
            root.after_idle(on_change)
    root.bind("<FocusIn>", check, add="+")
