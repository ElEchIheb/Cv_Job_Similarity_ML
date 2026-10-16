"""Crop the final thesis figures from main.pdf for the light-theme Canva deck.

Each figure is rendered at high DPI from the vector PDF, trimmed and its white
background made transparent so it sits cleanly on light slides.
"""
import sys
from pathlib import Path

import numpy as np
import pymupdf
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "ISI-LaTeX-Template-master/ISI-LaTeX-Template-master/main.pdf"
OUT = ROOT / "soutenance/canva_assets/light"

FIGS = {  # name: (page, caption prefix)
    "cascade": (25, "Figure 1.2"),
    "uc_global": (34, "Figure 2.1"),
    "architecture": (50, "Figure 3.2"),
    "classes": (52, "Figure 3.3"),
    "pipeline": (58, "Figure 4.1"),
    "deploiement": (107, "Figure 6.2"),
}


def figure_rect(page, prefix):
    blocks = page.get_text("blocks")
    cap = next(b for b in blocks if b[4].startswith(prefix))
    cap_top = cap[1]
    shapes = [d["rect"] for d in page.get_drawings()]
    shapes += [page.get_image_bbox(i) for i in page.get_images(full=True)]
    shapes = [r for r in shapes if r.y1 <= cap_top + 1 and r.width > 2]
    # the figure starts below the last body paragraph above the caption
    top = 30.0
    for b in blocks:
        r = pymupdf.Rect(b[:4])
        if r.y1 < cap_top and r.width > 380 and not any(r.intersects(s) for s in shapes):
            top = max(top, r.y1)
    box = None
    for r in shapes + [pymupdf.Rect(b[:4]) for b in blocks if b[1] >= top and b[3] < cap_top]:
        if r.y0 >= top - 1 and r.y1 <= cap_top + 1:
            box = r if box is None else box | r
    return box + (-6, -6, 6, 6)


def to_transparent(img):
    a = np.asarray(img.convert("RGB")).astype(np.int16)
    light = a.min(axis=2)
    alpha = np.clip((255 - light) * 4, 0, 255).astype(np.uint8)
    keep = light < 250
    alpha[keep] = np.maximum(alpha[keep], 255 - (light[keep] // 2))
    rgba = np.dstack([a.astype(np.uint8), alpha])
    out = Image.fromarray(rgba, "RGBA")
    return out.crop(out.getbbox())


def main(names):
    doc = pymupdf.open(PDF)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, (pno, prefix) in FIGS.items():
        if names and name not in names:
            continue
        page = doc[pno - 1]
        rect = figure_rect(page, prefix)
        pix = page.get_pixmap(clip=rect, dpi=330)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        to_transparent(img).save(OUT / f"{name}.png")
        print(name, rect, img.size)


if __name__ == "__main__":
    main(sys.argv[1:])
