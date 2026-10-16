"""Render an exported deck PDF into contact sheets (12 slides each) for visual review."""
import sys
import pymupdf
from PIL import Image

pdf, out = sys.argv[1], sys.argv[2]
doc = pymupdf.open(pdf)
W, H = 640, 360
print(len(doc), doc[0].rect)
for s in range(0, len(doc), 12):
    sheet = Image.new("RGB", (3 * W, 4 * H), "#333333")
    for i in range(s, min(s + 12, len(doc))):
        pm = doc[i].get_pixmap(matrix=pymupdf.Matrix(W / doc[i].rect.width, H / doc[i].rect.height))
        im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
        k = i - s
        sheet.paste(im, ((k % 3) * W, (k // 3) * H))
    sheet.save(f"{out}_{s // 12 + 1}.jpg", quality=82)
