"""
Custom widgets.

Custom tkinter widgets. Every class here is at module scope; the GUI
does ``from widgets import *`` at boot so every closure keeps finding
the classes by their names.

Five widgets live here:
  * ``GradientProgressBar``: thin canvas based progress bar that
    fills with the active workflow's gradient.
  * ``RoundedButton``: tk.Canvas button with truly rounded
    corners, hover state and a disabled state.
  * ``RoundedEntry``: tk.Entry wrapped in a rounded canvas
    border so it visually matches the buttons.
  * ``RoundedCombobox``: dropdown with rounded borders that
    emits an on_select callback.
  * ``RoundedSlider``: slim numeric slider with rounded
    track and circular thumb.

Plus one helper:
  * ``_make_gradient``: paints a linear gradient across a
    Canvas region (used by GradientProgressBar and any other
    caller that wants the same look).

Design rule: NO business logic here. These are UI primitives that
know nothing about this app's own processing or metadata modules. If
a widget needs colour tokens, it imports them from ``theme.py``
(below). Any tokens missing from ``theme.py`` should land there,
never in this file.
"""
from __future__ import annotations

import tkinter as tk

from theme import (BAR_H, BAR_W, C_PROGRESS_END, C_PROGRESS_START,
                    C_TEXT, C_TILE)


# Height of the input dialogs on Home (project name, data / output folder,
# recent projects). Bumped alongside the global font size boost so the
# text still fits comfortably inside the rounded background.
_ENTRY_HEIGHT = 32


# ══════════════════════════════════════════════════════════════════════════════
#  Gradient progress bar (branded)
# ══════════════════════════════════════════════════════════════════════════════

def _make_gradient(canvas, width, height, color_left, color_right):
    r1, g1, b1 = canvas.winfo_rgb(color_left)
    r2, g2, b2 = canvas.winfo_rgb(color_right)
    for x in range(width):
        t = x / max(width - 1, 1)
        r = int(r1 + (r2 - r1) * t) >> 8
        g = int(g1 + (g2 - g1) * t) >> 8
        b = int(b1 + (b2 - b1) * t) >> 8
        canvas.create_line(x, 0, x, height, fill=f"#{r:02x}{g:02x}{b:02x}")


class GradientProgressBar(tk.Frame):
    def __init__(self, parent, width=BAR_W, height=BAR_H, bg=None, **kw):
        super().__init__(parent, bg=(bg or C_TILE), **kw)
        self._bar_width  = width
        self._bar_height = height
        self._pct        = 0.0
        # Theme colours can be swapped at runtime (per active mode).
        self._grad_start = C_PROGRESS_END
        self._grad_end   = C_PROGRESS_START
        self._canvas = tk.Canvas(self, width=width, height=height,
                                  bd=0, highlightthickness=0,
                                  bg="#DDE7F5")
        self._canvas.pack()

    def _draw(self):
        c = self._canvas
        c.delete("all")
        c.create_rectangle(0, 0, self._bar_width, self._bar_height,
                            fill="#DDE7F5", outline="")
        fill_w = int(self._bar_width * self._pct / 100)
        if fill_w > 0:
            _make_gradient(c, fill_w, self._bar_height,
                             self._grad_start, self._grad_end)

    def set(self, value: float):
        self._pct = max(0.0, min(100.0, value))
        self._draw()

    def set_theme(self, start_colour: str, end_colour: str):
        """Recolour the gradient. Called by the GUI so the bar matches
        the active mode's own tone of the app's brand hue."""
        self._grad_start = start_colour
        self._grad_end   = end_colour
        self._draw()


# ══════════════════════════════════════════════════════════════════════════════
#  Rounded custom widgets
# ══════════════════════════════════════════════════════════════════════════════

class RoundedButton(tk.Canvas):
    """Canvas based button with truly rounded corners + hover / disabled."""
    def __init__(self, parent, text="", command=None,
                 bg="#1656B0", hover_bg="#103B7A",
                 disabled_bg="#B8C2D0",
                 fg="white", disabled_fg="#EEF2F7",
                 width=170, height=44, radius=14, font=None):
        super().__init__(parent, width=width, height=height,
                          bg=parent.cget("bg"),
                          bd=0, highlightthickness=0)
        self._text        = text
        self._command     = command
        self._bg          = bg
        self._hover_bg    = hover_bg
        self._disabled_bg = disabled_bg
        self._fg          = fg
        self._disabled_fg = disabled_fg
        self._btn_w, self._btn_h = width, height
        self._r                   = radius
        self._font        = font or ("Helvetica", 16, "bold")
        self._state       = "normal"
        self._hovered     = False
        self._draw()
        self.bind("<Enter>",   self._on_enter)
        self.bind("<Leave>",   self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def _draw(self):
        self.delete("all")
        if self._state == "disabled":
            bg, fg = self._disabled_bg, self._disabled_fg
        elif self._hovered:
            bg, fg = self._hover_bg, self._fg
        else:
            bg, fg = self._bg, self._fg
        r, w, h = self._r, self._btn_w, self._btn_h
        self.create_oval(0,       0,       2*r,    2*r,    fill=bg, outline=bg)
        self.create_oval(w - 2*r, 0,       w,      2*r,    fill=bg, outline=bg)
        self.create_oval(0,       h - 2*r, 2*r,    h,      fill=bg, outline=bg)
        self.create_oval(w - 2*r, h - 2*r, w,      h,      fill=bg, outline=bg)
        self.create_rectangle(r, 0, w - r, h, fill=bg, outline=bg)
        self.create_rectangle(0, r, w, h - r, fill=bg, outline=bg)
        self.create_text(w / 2, h / 2, text=self._text,
                          fill=fg, font=self._font)

    def _on_enter(self, _e):
        if self._state == "normal":
            self._hovered = True
            self._draw()

    def _on_leave(self, _e):
        if self._state == "normal" and self._hovered:
            self._hovered = False
            self._draw()

    def _on_click(self, _e):
        if self._state == "normal" and self._command:
            self._command()

    def configure(self, cnf=None, **kw):
        redraw = False
        if "state" in kw:
            new_state = kw.pop("state")
            if new_state != self._state:
                self._state = new_state
                self._hovered = False
                redraw = True
        if "text" in kw:
            new_text = kw.pop("text")
            if new_text != self._text:
                self._text = new_text
                redraw = True
        if "command" in kw:
            self._command = kw.pop("command")
        # Colour attributes: intercept so they update the button's fill /
        # hover / text colours instead of leaking to the tk.Canvas bg.
        for key in ("bg", "hover_bg", "fg",
                     "disabled_bg", "disabled_fg"):
            if key in kw:
                setattr(self, f"_{key}", kw.pop(key))
                redraw = True
        if kw:
            super().configure(**kw)
        if redraw:
            self._draw()
    config = configure


class RoundedEntry(tk.Frame):
    """Text entry with rounded corners. Expands fluidly unless fixed_width set."""
    def __init__(self, parent, textvariable=None, font=None,
                 height=34, radius=8,
                 bg="white",
                 border=None, focus=None,
                 fg=None,
                 fixed_width=None):
        super().__init__(parent, bg=parent.cget("bg"))
        self._height     = height
        self._radius     = radius
        self._bg         = bg
        self._border     = border or "#C7D3E4"
        self._focus      = focus  or C_PROGRESS_START
        self._cur_border = self._border
        self._cur_width  = 1
        self._last_resize_w = None

        if fixed_width:
            self.canvas = tk.Canvas(self, height=height, width=fixed_width,
                                      bg=parent.cget("bg"),
                                      bd=0, highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas = tk.Canvas(self, height=height,
                                      bg=parent.cget("bg"),
                                      bd=0, highlightthickness=0)
            self.canvas.pack(fill="x", expand=True)

        # width=1 keeps tk.Entry's natural minimum (based on character
        # count) at the floor; the actual display width comes from the
        # canvas window size set on <Configure>. This lets a RoundedEntry
        # shrink to whatever space its parent layout allocates.
        self.entry = tk.Entry(self.canvas, textvariable=textvariable,
                                font=(font or ("Helvetica", 16)),
                                relief="flat", bd=0, width=1,
                                bg=bg, fg=(fg or C_TEXT),
                                insertbackground=C_PROGRESS_END,
                                insertwidth=2,
                                highlightthickness=0)
        inner_pad = radius + 6
        self._inner_pad = inner_pad
        self._entry_id = self.canvas.create_window(
            inner_pad, height // 2,
            window=self.entry,
            width=200,
            anchor="w", tags=("entry_win",))

        self.entry.bind("<FocusIn>",
                          lambda _e: self._paint(self._focus, width=2))
        self.entry.bind("<FocusOut>",
                          lambda _e: self._paint(self._border, width=1))
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        # A resized ancestor fires several <Configure> events per widget
        # while Tk's geometry managers settle, several of them repeating
        # the same width before landing on the true final one, so skip
        # the repaint (oval/arc/line redraw) entirely when nothing
        # actually changed.
        if event.width == self._last_resize_w:
            return
        self._last_resize_w = event.width
        self.canvas.itemconfig(self._entry_id,
                                 width=event.width - 2 * self._inner_pad)
        self._paint(self._cur_border, self._cur_width)

    def _paint(self, border, width=1):
        self._cur_border = border
        self._cur_width  = width
        c = self.canvas
        c.delete("bg")
        c.delete("stroke")
        r = self._radius
        w = c.winfo_width() or 200
        h = self._height
        c.create_oval(0, 0, 2*r, 2*r, fill=self._bg, outline=self._bg, tags="bg")
        c.create_oval(w-2*r, 0, w, 2*r, fill=self._bg, outline=self._bg, tags="bg")
        c.create_oval(0, h-2*r, 2*r, h, fill=self._bg, outline=self._bg, tags="bg")
        c.create_oval(w-2*r, h-2*r, w, h, fill=self._bg, outline=self._bg, tags="bg")
        c.create_rectangle(r, 0, w-r, h, fill=self._bg, outline=self._bg, tags="bg")
        c.create_rectangle(0, r, w, h-r, fill=self._bg, outline=self._bg, tags="bg")
        c.create_arc(0, 0, 2*r, 2*r, start=90,  extent=90,
                      style="arc", outline=border, width=width, tags="stroke")
        c.create_arc(w-2*r, 0, w, 2*r, start=0,   extent=90,
                      style="arc", outline=border, width=width, tags="stroke")
        c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90,
                      style="arc", outline=border, width=width, tags="stroke")
        c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90,
                      style="arc", outline=border, width=width, tags="stroke")
        c.create_line(r, 0, w-r, 0,   fill=border, width=width, tags="stroke")
        c.create_line(r, h, w-r, h,   fill=border, width=width, tags="stroke")
        c.create_line(0, r, 0, h-r,   fill=border, width=width, tags="stroke")
        c.create_line(w, r, w, h-r,   fill=border, width=width, tags="stroke")
        c.tag_raise("stroke")
        c.tag_raise("entry_win")


class RoundedCombobox(tk.Frame):
    """Dropdown with rounded borders. Emits on_select(value) callback."""
    def __init__(self, parent, values=None, textvariable=None,
                 height=34, radius=10,
                 bg="white", border=None, focus=None,
                 fg=None, on_select=None, fixed_width=None):
        super().__init__(parent, bg=parent.cget("bg"))
        self._values     = list(values or [])
        self._var        = textvariable or tk.StringVar()
        self._height     = height
        self._radius     = radius
        self._bg         = bg
        self._border     = border or "#C7D3E4"
        self._focus      = focus  or C_PROGRESS_START
        self._fg         = fg     or C_TEXT
        self._on_select  = on_select
        self._state      = "readonly"
        self._hovered    = False
        self._last_resize_w = None

        if fixed_width:
            self.canvas = tk.Canvas(self, height=height, width=fixed_width,
                                      bg=parent.cget("bg"),
                                      bd=0, highlightthickness=0)
            self.canvas.pack()
        else:
            self.canvas = tk.Canvas(self, height=height,
                                      bg=parent.cget("bg"),
                                      bd=0, highlightthickness=0)
            self.canvas.pack(fill="x", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Button-1>",  self._on_click)
        self.canvas.bind("<Enter>",     self._on_enter)
        self.canvas.bind("<Leave>",     self._on_leave)
        self._var.trace_add("write", lambda *_: self._draw())

    def _on_resize(self, event):
        # A resized ANCESTOR reliably fires several <Configure> events
        # per widget while Tk's geometry managers settle, several of
        # them repeating the same width before landing on the true
        # final one, so skip the repaint entirely when nothing actually
        # changed. A fixed_width combobox never resizes at all, so this
        # also fully suppresses the (still fired) event that occurs the
        # first time an ancestor's layout is established.
        if event.width == self._last_resize_w:
            return
        self._last_resize_w = event.width
        self._draw()

    def _on_enter(self, _e):
        if self._state != "disabled":
            self._hovered = True
            self._draw()

    def _on_leave(self, _e):
        self._hovered = False
        self._draw()

    def _on_click(self, _e):
        if self._state == "disabled" or not self._values:
            return
        menu = tk.Menu(self, tearoff=0, font=("Helvetica", 16))
        for v in self._values:
            menu.add_command(label=v, command=lambda vv=v: self._select(vv))
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
        if kw:
            super().configure(**kw)
        if redraw:
            self._draw()
    config = configure

    def get(self):
        return self._var.get()

    def _draw(self):
        c = self.canvas
        c.delete("all")
        r = self._radius
        w = c.winfo_width() or 300
        h = self._height
        if self._state == "disabled":
            bg, fg, bd = "#F1F4F8", "#8090A5", "#DDE7F5"
        elif self._hovered:
            bg, fg, bd = self._bg, self._fg, self._focus
        else:
            bg, fg, bd = self._bg, self._fg, self._border
        c.create_oval(0, 0, 2*r, 2*r, fill=bg, outline=bg)
        c.create_oval(w-2*r, 0, w, 2*r, fill=bg, outline=bg)
        c.create_oval(0, h-2*r, 2*r, h, fill=bg, outline=bg)
        c.create_oval(w-2*r, h-2*r, w, h, fill=bg, outline=bg)
        c.create_rectangle(r, 0, w-r, h, fill=bg, outline=bg)
        c.create_rectangle(0, r, w, h-r, fill=bg, outline=bg)
        stroke_w = 2 if self._hovered else 1
        c.create_arc(0, 0, 2*r, 2*r, start=90, extent=90,
                      style="arc", outline=bd, width=stroke_w)
        c.create_arc(w-2*r, 0, w, 2*r, start=0, extent=90,
                      style="arc", outline=bd, width=stroke_w)
        c.create_arc(0, h-2*r, 2*r, h, start=180, extent=90,
                      style="arc", outline=bd, width=stroke_w)
        c.create_arc(w-2*r, h-2*r, w, h, start=270, extent=90,
                      style="arc", outline=bd, width=stroke_w)
        c.create_line(r, 0, w-r, 0, fill=bd, width=stroke_w)
        c.create_line(r, h, w-r, h, fill=bd, width=stroke_w)
        c.create_line(0, r, 0, h-r, fill=bd, width=stroke_w)
        c.create_line(w, r, w, h-r, fill=bd, width=stroke_w)
        text = self._var.get() or ""
        pad_l = r + 6
        pad_r = 24
        max_w = w - pad_l - pad_r
        display = text
        approx_char_w = 8
        max_chars = max(3, max_w // approx_char_w)
        if len(display) > max_chars:
            display = "…" + display[-(max_chars - 1):]
        c.create_text(pad_l, h // 2, text=display, anchor="w",
                       font=("Helvetica", 16), fill=fg)
        c.create_text(w - 12, h // 2, text="▾", anchor="e",
                       font=("Helvetica", 16, "bold"), fill=bd)


class RoundedSlider(tk.Canvas):
    """Slim slider with rounded track + circular thumb. Fluid width when packed
    with fill="x": <Configure> updates the internal width and redraws."""
    def __init__(self, parent, variable=None, from_=0, to=100,
                 width=460, height=32, radius=8,
                 track_bg="#E1E9F4", track_fill=C_PROGRESS_END,
                 thumb_fill="white", thumb_border=C_PROGRESS_END,
                 command=None):
        canvas_h = max(height + 12, 26)
        super().__init__(parent, width=width, height=canvas_h,
                          bg=parent.cget("bg"),
                          bd=0, highlightthickness=0)
        self._var        = variable or tk.IntVar(value=from_)
        self._from       = from_
        self._to         = to
        self._width      = width
        self._height     = height
        self._canvas_h   = canvas_h
        self._radius     = radius
        self._track_bg   = track_bg
        self._track_fill = track_fill
        self._thumb_fill = thumb_fill
        self._thumb_border = thumb_border
        self._command    = command
        self._thumb_r    = max(6, height // 2 + 2)
        self._pad_x      = self._thumb_r + 4
        self._track_y    = canvas_h // 2
        self._draw()
        self.bind("<Button-1>",   self._on_click)
        self.bind("<B1-Motion>",  self._on_click)
        self.bind("<Configure>",  self._on_resize)
        self._var.trace_add("write", lambda *_: self._draw())

    def _on_resize(self, event):
        if event.width > 0 and event.width != self._width:
            self._width = event.width
            self._draw()

    def _value_to_x(self, v):
        span_x  = self._width - 2 * self._pad_x
        span_v  = max(1, self._to - self._from)
        frac    = (v - self._from) / span_v
        frac    = max(0.0, min(1.0, frac))
        return self._pad_x + frac * span_x

    def _x_to_value(self, x):
        span_x  = self._width - 2 * self._pad_x
        frac    = (x - self._pad_x) / max(1, span_x)
        frac    = max(0.0, min(1.0, frac))
        v       = self._from + frac * (self._to - self._from)
        return int(round(v))

    def _draw(self):
        self.delete("all")
        w, h = self._width, self._height
        r    = self._radius
        y    = self._track_y
        y0   = y - r
        y1   = y + r
        self.create_oval(self._pad_x - r, y0, self._pad_x + r, y1,
                          fill=self._track_bg, outline=self._track_bg)
        self.create_oval(w - self._pad_x - r, y0, w - self._pad_x + r, y1,
                          fill=self._track_bg, outline=self._track_bg)
        self.create_rectangle(self._pad_x, y0,
                                w - self._pad_x, y1,
                                fill=self._track_bg, outline=self._track_bg)
        val = int(self._var.get() or self._from)
        tx  = self._value_to_x(val)
        self.create_oval(self._pad_x - r, y0, self._pad_x + r, y1,
                          fill=self._track_fill, outline=self._track_fill)
        self.create_rectangle(self._pad_x, y0, tx, y1,
                                fill=self._track_fill, outline=self._track_fill)
        tr = self._thumb_r
        self.create_oval(tx - tr, y - tr, tx + tr, y + tr,
                          fill=self._thumb_fill,
                          outline=self._thumb_border, width=3)

    def _on_click(self, event):
        new_v = self._x_to_value(event.x)
        cur   = int(self._var.get() or self._from)
        if new_v != cur:
            self._var.set(new_v)
            if self._command:
                self._command(new_v)
