"""
Regenerates assets/Optodrum_logo.png.

A simple, original mark: the black/white vertical striped drum an
OptoDrum rig rotates around the animal (the visual stimulus itself),
with a small dark pupil at the centre standing for the eye tracking
half of the measurement. Clipped to a circle and rendered in the app's own grey
theme (see app/theme.py) rather than true black/white, so the mark reads
as this app's identity rather than a literal photo of the rig.

Run directly to regenerate:  python3 assets/_generate_logo.py
"""
import os

from PIL import Image, ImageDraw

_OUT = os.path.join(os.path.dirname(__file__), "Optodrum_logo.png")

# Matches app/theme.py's own C_SLATE family.
_STRIPE_DARK = (58, 63, 69, 255)     # C_SLATE_DARK
_STRIPE_LIGHT = (242, 243, 243, 255)  # C_SLATE_LIGHT
_RING = (90, 97, 105, 255)           # C_SLATE
_PUPIL = (32, 36, 42, 255)           # C_TEXT

SIZE = 640
SUPERSAMPLE = 4


def build_logo():
    s = SIZE * SUPERSAMPLE
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = s / 2, s / 2
    r = s * 0.46

    # Vertical stripes clipped to the drum's own circle.
    n_stripes = 10
    stripe_w = (2 * r) / n_stripes
    for i in range(n_stripes):
        x0 = cx - r + i * stripe_w
        colour = _STRIPE_DARK if i % 2 == 0 else _STRIPE_LIGHT
        draw.rectangle([x0, cy - r, x0 + stripe_w, cy + r], fill=colour)

    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    drum = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    drum.paste(img, (0, 0), mask)

    out = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    out.paste(drum, (0, 0), drum)
    d = ImageDraw.Draw(out)
    ring_w = s * 0.018
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=_RING,
              width=int(ring_w))

    # Pupil: the eye tracking half of an OptoDrum measurement.
    pr = r * 0.22
    d.ellipse([cx - pr, cy - pr, cx + pr, cy + pr], fill=_PUPIL,
              outline=_STRIPE_LIGHT, width=int(ring_w * 0.8))

    out = out.resize((SIZE, SIZE), Image.LANCZOS)
    out.save(_OUT)
    print(f"Saved: {_OUT}")


if __name__ == "__main__":
    build_logo()
