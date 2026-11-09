"""Turn assets/avatar.png (transparent background) into coloured ASCII art.

Writes two grids of the same size:
  assets/ascii-art.txt     the characters
  assets/ascii-colors.txt  one palette letter per character (see PALETTE)

build_card.py reads both and colours each run of characters, with the
actual colours picked per theme there.

Only needed when the avatar changes. Needs Pillow + numpy:
    pip install pillow numpy
    python tools/make_ascii.py
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "assets" / "avatar.png"
OUT_ART = ROOT / "assets" / "ascii-art.txt"
OUT_COL = ROOT / "assets" / "ascii-colors.txt"

COLS = 62
CELL_ASPECT = 0.54          # must match ART_CELL_ASPECT in build_card.py

# Reference colours sampled from the avatar. Each cell takes the nearest one.
PALETTE = {
    "O": (25, 18, 35),      # black outline / pupils
    "W": (245, 245, 250),   # eye whites
    "L": (255, 226, 165),   # light upper face
    "Y": (255, 196, 70),    # yellow lower face
    "P": (88, 52, 185),     # purple hat + suit
    "D": (50, 28, 110),     # dark purple hat band
    "G": (78, 88, 96),      # grey tie
}

# Glyphs from light to dense ink.
OUTLINE_RAMP = "=#%@"
FILL_RAMP = ".:-=+*"


def main() -> None:
    im = Image.open(SRC).convert("RGBA")
    a = np.asarray(im).astype(float)
    h, w = a.shape[:2]
    cell_w = w / COLS
    cell_h = cell_w / CELL_ASPECT
    rows = int(h / cell_h)

    names = list(PALETTE)
    ref = np.array([PALETTE[n] for n in names], dtype=float)

    art, cols = [], []
    for r in range(rows):
        line, cline = [], []
        for c in range(COLS):
            y0, y1 = int(r * cell_h), int((r + 1) * cell_h)
            x0, x1 = int(c * cell_w), int((c + 1) * cell_w)
            cell = a[y0:y1, x0:x1].reshape(-1, 4)
            inside = cell[cell[:, 3] > 128]
            cover = len(inside) / max(len(cell), 1)
            if cover < 0.35:
                line.append(" ")
                cline.append(" ")
                continue
            rgb = inside[:, :3]
            lum = rgb.mean(axis=1)
            dark = (lum < 80).mean()
            if dark > 0.3:
                glyph = OUTLINE_RAMP[min(int(dark * len(OUTLINE_RAMP)), len(OUTLINE_RAMP) - 1)]
                key = "O"
            else:
                mean = rgb[lum >= 80].mean(axis=0)
                key = names[int(np.argmin(((ref - mean) ** 2).sum(axis=1)))]
                if key == "O":
                    key = "D"
                # brighter fill -> denser glyph, so the face reads as solid
                t = float(np.clip(mean.max() / 255, 0, 1)) * 0.8
                glyph = FILL_RAMP[min(int(t * len(FILL_RAMP)), len(FILL_RAMP) - 1)]
                if cover < 0.7:
                    glyph = "."      # soften the silhouette edge
            line.append(glyph)
            cline.append(key)
        art.append("".join(line).rstrip())
        cols.append("".join(cline)[: len(art[-1])])

    # trim empty rows top and bottom
    while art and not art[0].strip():
        art.pop(0), cols.pop(0)
    while art and not art[-1].strip():
        art.pop(), cols.pop()

    OUT_ART.write_text("\n".join(art) + "\n", encoding="utf-8")
    OUT_COL.write_text("\n".join(cols) + "\n", encoding="utf-8")
    print(f"wrote {len(art)} rows x {COLS} cols")


if __name__ == "__main__":
    main()
