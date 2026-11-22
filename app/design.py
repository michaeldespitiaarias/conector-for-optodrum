"""
Design tokens shared by every VisoLab application.

Identical in every app (vendored, not linked): neutrals, text colours,
status colours, the type scale and the layout grid. Each app's own
``theme.py`` adds its brand hue on top and re-exports everything here, so
a screen in VisoTrace and the same screen in VisoStats differ only in the
accent colour.

Rules the tokens encode:

* The accent (the app's hue) marks what can be acted on or where the user
  is: the primary button, the active step, focus, links, selection. Text,
  headings and borders stay neutral, so the accent keeps its meaning.
* One type family per platform (the operating system's own interface
  face), one scale. Hierarchy comes from size and weight, never from
  colour alone.
* Spacing on a 4-pixel grid.

Appearance: the tokens below are the light appearance, and every colour
in the apps is written in light terms. The dark appearance is not a
second set of names: ``dark_variant`` translates a light colour into its
dark counterpart by the role it plays (a background, text, or a mark
such as a border or a line), and widgets.py applies that translation at
the one place every colour reaches Tk. A neutral swaps lightness; a pale
tint of a hue becomes a deep tint of the same hue; a saturated colour (an
accent fill, a group colour, a status fill) keeps its value, so the
colours that carry meaning in a figure or a swatch never change.
"""
from __future__ import annotations

import colorsys
import sys

# ── Neutrals ─────────────────────────────────────────────────────────────────
# A cool, very slightly blue-leaning grey ramp: reads as deliberate next to
# every app hue (blue, green, purple, crimson, slate) without tinting any.
C_APP_BG        = "#F5F6F8"   # window / content background
C_SURFACE       = "#FFFFFF"   # cards, inputs, dialogs
C_SURFACE_ALT   = "#FAFBFC"   # zebra rows, subtle wells
C_SIDEBAR       = "#EDEFF2"   # navigation column
C_SIDEBAR_HOVER = "#E3E6EA"
C_BORDER        = "#D9DDE3"   # card and input outlines
C_BORDER_STRONG = "#BFC6CF"   # secondary-button outline, hovered input
C_DIVIDER       = "#E4E7EB"   # hairlines inside a card

C_TEXT          = "#1B2230"   # primary text, headings
C_TEXT_2        = "#4E5867"   # secondary text, descriptions
C_TEXT_3        = "#7F8896"   # captions, placeholders, inactive steps
C_DISABLED_BG   = "#E8EBEF"
C_DISABLED_FG   = "#A2AAB5"

# ── Status (never used as an app accent) ─────────────────────────────────────
C_WARN          = "#8A5300"   # text on light backgrounds (AA contrast)
C_WARN_BG       = "#FFF6E6"
C_WARN_BORDER   = "#F2D3A0"
C_DANGER        = "#B42318"
C_DANGER_BG     = "#FEF1F0"
C_SUCCESS       = "#1D7A4B"
C_SUCCESS_BG    = "#ECF8F1"

# ── Typography ───────────────────────────────────────────────────────────────
# Tk resolves ".AppleSystemUIFont" to San Francisco on macOS; Segoe UI is
# the Windows interface face; DejaVu Sans ships with every common Linux
# desktop. Sizes are in points; runtime_support.apply_platform_scaling
# keeps one point equal to one pixel on every platform, so the same size
# renders at the same proportion everywhere.
if sys.platform == "darwin":
    UI_FONT, MONO_FONT = ".AppleSystemUIFont", "Menlo"
elif sys.platform.startswith("win"):
    UI_FONT, MONO_FONT = "Segoe UI", "Consolas"
else:
    UI_FONT, MONO_FONT = "DejaVu Sans", "DejaVu Sans Mono"

F_DISPLAY  = (UI_FONT, 26, "bold")    # welcome screen
F_PAGE     = (UI_FONT, 20, "bold")    # page title
F_SECTION  = (UI_FONT, 14, "bold")    # section heading inside a page
F_BODY     = (UI_FONT, 13)
F_BODY_B   = (UI_FONT, 13, "bold")
F_SMALL    = (UI_FONT, 12)
F_SMALL_B  = (UI_FONT, 12, "bold")
F_CAPTION  = (UI_FONT, 11, "bold")    # uppercase group labels
F_BUTTON   = (UI_FONT, 13, "bold")
F_MONO     = (MONO_FONT, 12)

# ── Layout ───────────────────────────────────────────────────────────────────
SP_1, SP_2, SP_3, SP_4, SP_6, SP_8 = 4, 8, 12, 16, 24, 32

CONTROL_H   = 30     # buttons, entries, dropdowns
CONTROL_R   = 6      # corner radius of every control
CARD_PAD    = 20     # inner padding of a card
LABEL_W     = 200    # label column in a form row
SIDEBAR_W   = 232
CONTENT_MAX = 880    # text measure of long paragraphs, in pixels

WIN_W       = 1120
WIN_H       = 780
WIN_MIN_W   = 900
WIN_MIN_H   = 620    # fits a 1366x768 laptop with the dock or taskbar


def mix(a: str, b: str, t: float) -> str:
    """Blend hex colour *a* toward *b* by *t* (0 = a, 1 = b)."""
    a, b = a.lstrip("#"), b.lstrip("#")
    ca = [int(a[i:i + 2], 16) for i in (0, 2, 4)]
    cb = [int(b[i:i + 2], 16) for i in (0, 2, 4)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(ca, cb))


def accent_set(primary: str, primary_dark: str) -> dict:
    """Everything a widget needs from an accent, derived from one hue.

    ``subtle`` is the selected-row / active-step background; ``subtle_hover``
    its hover; ``ring`` the focus outline; ``on`` the text colour placed on
    a filled accent surface.
    """
    return {
        "accent": primary,
        "accent_hover": primary_dark,
        "subtle": mix(primary, "#FFFFFF", 0.90),
        "subtle_hover": mix(primary, "#FFFFFF", 0.83),
        "ring": mix(primary, "#FFFFFF", 0.35),
        "on": "#FFFFFF",
    }


# ── Appearance (light / dark / system) ───────────────────────────────────────
APPEARANCES = (("light", "Light mode"), ("dark", "Dark mode"),
               ("system", "Match system"))

_appearance = {"mode": "system", "effective": "light"}


def system_appearance() -> str:
    """The appearance the operating system is set to, "dark" or "light".
    Read from the macOS or Windows setting; anything that cannot be read
    counts as light."""
    import sys
    try:
        if sys.platform == "darwin":
            import subprocess
            out = subprocess.run(
                ["defaults", "read", "-g", "AppleInterfaceStyle"],
                capture_output=True, text=True, timeout=2)
            return "dark" if out.stdout.strip().lower() == "dark" else "light"
        if sys.platform.startswith("win"):
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes"
                r"\Personalize")
            value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            return "light" if value else "dark"
    except Exception:                               # noqa: BLE001
        pass
    return "light"


def set_appearance(mode: str) -> str:
    """Choose "light", "dark" or "system" (follow the operating system;
    anything else is system). Returns the choice in force. Widgets drawn
    from then on use the appearance it resolves to."""
    mode = mode if mode in ("light", "dark") else "system"
    _appearance["mode"] = mode
    _appearance["effective"] = (system_appearance() if mode == "system"
                                else mode)
    return mode


def appearance() -> str:
    """The choice in force: "light", "dark" or "system"."""
    return _appearance["mode"]


def effective_appearance() -> str:
    """What is drawn: "light" or "dark", with "system" resolved."""
    return _appearance["effective"]


def refresh_system_appearance() -> bool:
    """Under "system", read the operating system's setting again. True
    when the appearance drawn has to change."""
    if _appearance["mode"] != "system":
        return False
    now = system_appearance()
    if now == _appearance["effective"]:
        return False
    _appearance["effective"] = now
    return True


def is_dark() -> bool:
    return _appearance["effective"] == "dark"


# Exact counterparts for the tokens above, so the dark appearance is
# designed rather than computed wherever a token is used. Surfaces and
# borders (role "bg" or "mark" on a light colour):
_DARK_SURFACES = {
    "#F5F6F8": "#14171C",   # C_APP_BG
    "#FFFFFF": "#1D2128",   # C_SURFACE
    "#FAFBFC": "#21252D",   # C_SURFACE_ALT
    "#EDEFF2": "#181B21",   # C_SIDEBAR
    "#E3E6EA": "#252A32",   # C_SIDEBAR_HOVER, segmented track
    "#D8DCE2": "#2E343D",   # segmented hover
    "#F1F3F5": "#272C34",   # secondary button hover
    "#D9DDE3": "#353B45",   # C_BORDER
    "#BFC6CF": "#4A525E",   # C_BORDER_STRONG
    "#E4E7EB": "#2A2F37",   # C_DIVIDER
    "#E8EBEF": "#272B33",   # C_DISABLED_BG
    "#FFF6E6": "#2F2616",   # C_WARN_BG
    "#F2D3A0": "#6A5228",   # C_WARN_BORDER
    "#FEF1F0": "#361D1B",   # C_DANGER_BG
    "#ECF8F1": "#15291D",   # C_SUCCESS_BG
}
# Text (role "fg", or "mark" on a dark colour):
_DARK_INKS = {
    "#1B2230": "#E5E8ED",   # C_TEXT
    "#4E5867": "#B2B9C4",   # C_TEXT_2
    "#7F8896": "#8B94A1",   # C_TEXT_3
    "#A2AAB5": "#5F6773",   # C_DISABLED_FG
    "#8A5300": "#E8B464",   # C_WARN
    "#B42318": "#F2867B",   # C_DANGER
    "#1D7A4B": "#5FC793",   # C_SUCCESS
    "#000000": "#E5E8ED",
}
_NAMED = {"white": "#FFFFFF", "black": "#000000", "gray": "#808080",
          "grey": "#808080"}
_dark_cache: dict = {}
_dark_made: set = set()


def _norm_hex(colour):
    """'#rrggbb' in upper case, or None when *colour* is not a plain
    colour (empty, a system colour name, a 12-digit Tk colour)."""
    if not isinstance(colour, str) or not colour:
        return None
    c = _NAMED.get(colour.lower(), colour)
    if not c.startswith("#"):
        return None
    c = c[1:]
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    if len(c) != 6:
        return None
    try:
        int(c, 16)
    except ValueError:
        return None
    return "#" + c.upper()


def _hls_hex(h, l, s):
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, min(1.0, l)),
                                  max(0.0, min(1.0, s)))
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def dark_variant(colour, role="bg"):
    """The dark-appearance counterpart of light colour *colour*.

    *role* is what the colour does: "bg" (a widget's background: only a
    light colour changes), "fg" (text and icons: only a dark colour
    changes) or "mark" (a border, a line or a shape on a canvas: a light
    neutral darkens, a dark neutral lightens, and a hue keeps its value). Applying it to a colour it
    already produced returns that colour unchanged, so a colour read back
    from a widget can be passed on safely.
    """
    hexc = _norm_hex(colour)
    if hexc is None or hexc in _dark_made:
        return colour
    key = (hexc, role)
    hit = _dark_cache.get(key)
    if hit is not None:
        return hit
    r, g, b = (int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    chroma = max(r, g, b) - min(r, g, b)
    out = hexc
    light = l > 0.5
    if role in ("bg", "mark") and light:
        if hexc in _DARK_SURFACES:
            out = _DARK_SURFACES[hexc]
        elif chroma < 0.22:
            # A pale neutral or a pale tint of a hue: a deep tint of the
            # same hue, as far from the dark ground as it was from white.
            base = 0.10 if role == "bg" else 0.14
            out = _hls_hex(h, base + (1 - l) * (0.55 if role == "bg"
                                                else 0.75), s * 0.35)
    elif role in ("fg", "mark") and not light:
        if hexc in _DARK_INKS:
            out = _DARK_INKS[hexc]
        elif chroma < 0.12:
            out = _hls_hex(h, 0.93 - l * 0.6, s * 0.5)
        elif role == "fg" and l < 0.62:
            # A dark hue (an accent link, a status word): lighter, same hue.
            out = _hls_hex(h, 0.68, min(s, 0.85))
    _dark_cache[key] = out
    if out != hexc:
        _dark_made.add(out)
    return out


def themed(colour, role="bg"):
    """*colour* in the appearance in force: unchanged in light, translated
    by ``dark_variant`` in dark."""
    if _appearance["effective"] != "dark":
        return colour
    return dark_variant(colour, role)
