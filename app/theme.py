"""
OptoDrum Connector theme + typography + layout tokens.

A single light palette read by the GUI, holding constants only, no
helper functions. Widgets live in ``widgets.py``; the help dialog
lives in ``help_modal.py``. The GUI does ``from theme import *`` at
boot so every closure resolves the tokens by their original names, so
``widgets.py`` keeps importing the token names it expects.

OptoDrum Connector stays independent, with its own single brand hue: a
neutral slate grey rather than an accent tied to a mode, since there
is only one function here (parsing OptoDrum `.summary` exports) and
therefore no ladder of mode tones to derive. The eight token family
below follows a fixed blend formula, not chosen by eye: primary_dark =
35% toward black; grad_end = 25% toward white; halo = 88% toward
white; light_bg = 93% toward white; light_hover = 85% toward white;
glow = 55% toward white; glow_soft = 70% toward white.
"""
from __future__ import annotations


# ── Brand palette ──────────────────────────────────────────────────────────
# C_SLATE is the one anchor this whole app is built on: the identity
# colour (splash, Home) doubling as the colour of its one function,
# since there is no separate earlier stage to anchor a lighter tone.
C_SLATE            = "#5A6169"
C_SLATE_DARK       = "#3A3F45"   # mix(primary, black, 0.35)
C_SLATE_END        = "#8A9098"   # mix(primary, white, 0.25)
C_SLATE_HALO       = "#E9EAEC"   # mix(primary, white, 0.88)
C_SLATE_LIGHT      = "#F2F3F3"   # mix(primary, white, 0.93)
C_SLATE_HOVER      = "#E3E4E6"   # mix(primary, white, 0.85)
C_SLATE_GLOW       = "#ACAFB3"   # mix(primary, white, 0.55)
C_SLATE_GLOW_SOFT  = "#C6C8CB"   # mix(primary, white, 0.70)

# Structural neutrals (glyph strokes, dialog chrome, body background):
# generic tones alongside the brand family above.
C_TILE        = "#FFFFFF"    # widget background
C_BODY_BG     = "#FBFBFC"    # near white body
C_TEXT        = "#20242A"
C_MUTED       = "#6B7178"
C_BORDER      = "#DCDEE1"
C_DIVIDER     = "#E9EAEC"

# Progress bar gradient. Named for its role so widgets.py never has to
# change when the brand colour does.
C_PROGRESS_START = C_SLATE_END
C_PROGRESS_END   = C_SLATE_DARK

# One mode only: OptoDrum Connector has a single function, so "home" is
# also the (only) working mode's own theme. Home and the splash both
# read from the same entry.
_MODE_THEMES = {
    "home": {"primary":      C_SLATE,
             "primary_dark": C_SLATE_DARK,
             "grad_dark":    C_SLATE_DARK,
             "grad_end":     C_SLATE_END,
             "halo":         C_SLATE_HALO,
             "glow":         C_SLATE_GLOW,
             "glow_soft":    C_SLATE_GLOW_SOFT,
             "light_bg":     C_SLATE_LIGHT,
             "light_hover":  C_SLATE_HOVER},
}


# ── Typography ────────────────────────────────────────────────────────────
FONT_TITLE   = ("Helvetica", 30, "bold")
FONT_SECTION = ("Helvetica", 16, "bold")
FONT_LABEL   = ("Helvetica", 16, "bold")
FONT_NORMAL  = ("Helvetica", 16)
FONT_SMALL   = ("Helvetica", 16)
FONT_MICRO   = ("Helvetica", 16, "bold")
FONT_BTN     = ("Helvetica", 16, "bold")


# ── Layout constants ──────────────────────────────────────────────────────
WIN_W       = 900
WIN_H       = 720
WIN_H_MIN   = 660
BAR_W       = 650
BAR_H       = 7
ICON_SIZE   = 44
PAD_X       = 26
PAD_Y_SEC   = 16
