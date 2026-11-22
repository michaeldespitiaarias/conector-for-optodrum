"""
OptoDrum Connector colour identity, on top of the tokens in design.py.

OptoDrum Connector is an independent tool with one job (turning OptoDrum
`.summary` exports into one table), so it has one hue and no ladder of
mode tones: a neutral slate grey. Its eight-token family follows the same
blend formula the VisoLab apps use (primary_dark = mix(primary, black,
0.35); grad_end = mix(primary, white, 0.25); halo = 0.88; light_bg =
0.93; light_hover = 0.85; glow = 0.55; glow_soft = 0.70 toward white).

DO NOT add helper functions here; widgets live in widgets.py.
"""
from __future__ import annotations

from design import *            # noqa: F401,F403  (re-exported)
from design import (C_APP_BG, C_SURFACE, C_TEXT_2, F_BODY, F_BODY_B,
                    F_BUTTON, F_CAPTION, F_PAGE, F_SECTION, F_SMALL,
                    WIN_MIN_H, accent_set)

APP_HUE_NAME = "slate"

C_SLATE            = "#5A6169"
C_SLATE_DARK       = "#3A3F45"
C_SLATE_END        = "#8A9098"
C_SLATE_HALO       = "#E9EAEC"
C_SLATE_LIGHT      = "#F2F3F3"
C_SLATE_HOVER      = "#E3E4E6"
C_SLATE_GLOW       = "#ACAFB3"
C_SLATE_GLOW_SOFT  = "#C6C8CB"

# Progress bar, named for its role so widgets.py never names a hue.
C_PROGRESS_START = C_SLATE_END
C_PROGRESS_END   = C_SLATE_DARK


def _family(primary, dark, end, halo, light, hover, glow, glow_soft):
    fam = {"primary": primary, "primary_dark": dark, "grad_dark": dark,
           "grad_end": end, "halo": halo, "glow": glow,
           "glow_soft": glow_soft, "light_bg": light, "light_hover": hover}
    fam.update(accent_set(primary, dark))
    return fam


# One entry: the welcome screen, Home and the run all wear the same hue.
_MODE_THEMES = {
    "home": _family(C_SLATE, C_SLATE_DARK, C_SLATE_END, C_SLATE_HALO,
                    C_SLATE_LIGHT, C_SLATE_HOVER, C_SLATE_GLOW,
                    C_SLATE_GLOW_SOFT),
}

# ── Names older code used, mapped onto the tokens ────────────────────────
C_TILE       = C_SURFACE
C_BODY_BG    = C_APP_BG
C_MUTED      = C_TEXT_2
FONT_TITLE   = F_PAGE
FONT_SECTION = F_SECTION
FONT_LABEL   = F_BODY_B
FONT_NORMAL  = F_BODY
FONT_SMALL   = F_SMALL
FONT_MICRO   = F_CAPTION
FONT_BTN     = F_BUTTON
WIN_H_MIN    = WIN_MIN_H
BAR_W        = 520
BAR_H        = 6
PAD_X        = 28
PAD_Y_SEC    = 14
