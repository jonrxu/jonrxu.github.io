#!/usr/bin/env python3
"""Generate a white-dot dithered sphere logo on a black background."""

from __future__ import annotations

import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

# --- config ---
SIZE = 1024
MARGIN = 0.12
DOT_STEP = 6          # dense grid — original dither look
DOT_RADIUS = 3.6      # larger dots for visibility
CORNER_RADIUS = 96    # rounded black plate corners
SEED = 7
CLEAR = (0, 0, 0, 0)
BLACK = (0, 0, 0, 255)
DOT = (255, 255, 255, 255)
OUT = Path(__file__).resolve().parents[1] / "images" / "logo.png"


def brightness(nx: float, ny: float, nz: float) -> float:
    """Lambertian shading: bright upper-left, dark lower-right."""
    lx, ly, lz = -0.55, -0.65, 0.55
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln
    diffuse = max(0.0, nx * lx + ny * ly + nz * lz)
    # Soft ambient so the dark side still has sparse dots
    return 0.06 + 0.94 * (diffuse ** 1.15)


def main() -> None:
    rng = random.Random(SEED)
    img = Image.new("RGBA", (SIZE, SIZE), CLEAR)
    draw = ImageDraw.Draw(img)

    # Rounded black plate; corners stay transparent
    draw.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=CORNER_RADIUS, fill=BLACK)

    usable = SIZE * (1 - 2 * MARGIN)
    cx = cy = SIZE / 2
    radius = usable / 2

    # Ordered dither-ish: sample a fine grid, keep dots with probability ~ brightness
    y = MARGIN * SIZE
    while y < SIZE - MARGIN * SIZE:
        x = MARGIN * SIZE
        # Slight row offset for a less rigid lattice (still digital)
        row = int((y - MARGIN * SIZE) / DOT_STEP)
        x_off = (DOT_STEP * 0.5) if row % 2 else 0.0
        while x < SIZE - MARGIN * SIZE:
            px = x + x_off
            py = y
            nx = (px - cx) / radius
            ny = (py - cy) / radius
            r2 = nx * nx + ny * ny
            if r2 <= 1.0:
                nz = math.sqrt(1.0 - r2)
                b = brightness(nx, ny, nz)

                # Rim softens a bit so the silhouette isn't a hard disk
                rim = math.sqrt(r2)
                b *= 1.0 - 0.35 * (rim ** 3)

                # Stochastic threshold → density encodes shade (1-bit dither feel)
                # Blue-noise-ish jitter on threshold
                thresh = rng.random()
                if thresh < b:
                    # Tiny positional jitter so it feels organic like the reference
                    jx = (rng.random() - 0.5) * DOT_STEP * 0.35
                    jy = (rng.random() - 0.5) * DOT_STEP * 0.35
                    dx = px + jx
                    dy = py + jy
                    r = DOT_RADIUS
                    # Occasional slightly larger/smaller dots for texture
                    if rng.random() < 0.08:
                        r *= 1.35
                    elif rng.random() < 0.12:
                        r *= 0.7
                    draw.ellipse([dx - r, dy - r, dx + r, dy + r], fill=DOT)

            x += DOT_STEP
        y += DOT_STEP

    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, "PNG")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
