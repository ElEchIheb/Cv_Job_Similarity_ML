"""Prepare the images placed in the Canva deck (white-on-transparent figures for the dark template)."""
import os

import numpy as np
import pymupdf
import qrcode
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(ROOT, "..", "ISI-LaTeX-Template-master", "ISI-LaTeX-Template-master")
IMG = os.path.join(REP, "img")
OUT = os.path.join(ROOT, "canva_assets")
FONT = r"C:\Windows\Fonts\segoeui.ttf"
FONTB = r"C:\Windows\Fonts\segoeuib.ttf"
BLUE, DEEP, MINT = (0, 113, 201), (20, 93, 160), (23, 227, 178)


def to_white(im, gain=1.7):
    """Dark strokes on a light background -> white strokes on transparent."""
    a = np.asarray(im.convert("RGB")).astype(float)
    lum = a @ np.array([0.299, 0.587, 0.114])
    alpha = np.clip((255 - lum) * gain, 0, 255).astype(np.uint8)
    out = np.dstack([np.full_like(alpha, 255)] * 3 + [alpha])
    return Image.fromarray(out, "RGBA")


def trim(im, pad=12):
    box = im.getchannel("A").point(lambda v: 255 if v > 20 else 0).getbbox()
    box = (max(box[0] - pad, 0), max(box[1] - pad, 0), min(box[2] + pad, im.width), min(box[3] + pad, im.height))
    return im.crop(box)


def pdf_figure(doc, page, caption_top, name):
    p = doc[page - 1]
    rects = [d["rect"] for d in p.get_drawings() if d["rect"].y1 < caption_top]
    # drop the running-header rule (a thin full-width line)
    rects = [r for r in rects if not (r.height < 2 and r.width > 350 and r.y0 < 90)]
    box = pymupdf.Rect(min(r.x0 for r in rects), min(r.y0 for r in rects), max(r.x1 for r in rects), max(r.y1 for r in rects))
    # labels drawn next to the shapes are text, not drawings: widen the box to keep them
    for w in p.get_text("words"):
        if w[1] > box.y0 - 6 and w[3] < caption_top - 2:
            box |= pymupdf.Rect(w[:4])
    pm = p.get_pixmap(dpi=400, clip=box + (-10, -8, 10, 8))
    im = Image.frombytes("RGB", (pm.width, pm.height), pm.samples)
    trim(to_white(im)).save(os.path.join(OUT, name))


def logo_white(src, name, scale=1, from_white_bg=False):
    im = Image.open(src).convert("RGBA")
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    rgb, al = a[..., :3].copy(), a[..., 3]
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    sat = rgb.max(-1) - rgb.min(-1)
    if from_white_bg:
        al = np.clip((255 - rgb.min(-1)) * 3, 0, 255)
    dark = ((lum < 110) & (sat < 90)) | (lum < 70)
    rgb[dark] = 255
    out = np.dstack([rgb, al]).astype(np.uint8)
    trim(Image.fromarray(out, "RGBA"), 6).save(os.path.join(OUT, name))


def wrap(draw, text, font, width):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if draw.textlength(t, font=font) <= width or not cur:
                cur = t
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def table(rows, widths, name, fs=30, hi_col=None, hi_row=None, pad=18, center_from=1, mint=False):
    f, fb = ImageFont.truetype(FONT, fs), ImageFont.truetype(FONTB, fs)
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    lh = int(fs * 1.32)
    cells, heights = [], []
    for r, row in enumerate(rows):
        line_sets = []
        for c, txt in enumerate(row):
            bold = r == 0 or c == 0 or c == hi_col or r == hi_row
            line_sets.append((wrap(tmp, txt, fb if bold else f, widths[c] - 2 * pad), bold))
        cells.append(line_sets)
        heights.append(max(len(l) for l, _ in line_sets) * lh + 2 * pad)
    im = Image.new("RGBA", (sum(widths) + 4, sum(heights) + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 2
    for r, row in enumerate(cells):
        x = 2
        for c, (lines, bold) in enumerate(row):
            hi = r != 0 and (c == hi_col or r == hi_row)
            fill = BLUE + (255,) if r == 0 else DEEP + (255,) if hi else (255, 255, 255, 14) if r % 2 == 0 else None
            if fill:
                d.rectangle([x, y, x + widths[c], y + heights[r]], fill=fill)
            d.rectangle([x, y, x + widths[c], y + heights[r]], outline=(255, 255, 255, 70), width=2)
            ty = y + (heights[r] - len(lines) * lh) // 2
            for ln in lines:
                font = fb if bold else f
                tx = x + pad if c < center_from else x + (widths[c] - d.textlength(ln, font=font)) / 2
                col = MINT if (mint and hi and c >= center_from) else (255, 255, 255) if bold else (219, 231, 255)
                d.text((tx, ty), ln, font=font, fill=col + (255,))
                ty += lh
            x += widths[c]
        y += heights[r]
    im.save(os.path.join(OUT, name))
    return im


def bars(name):
    data = [("TF-IDF", 0.95, 0.98), ("Embeddings", 0.85, 0.81), ("Compétences", 0.93, 0.95), ("Hybride", 0.93, 0.96)]
    W, H = 760, 480
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    f, fb = ImageFont.truetype(FONT, 26), ImageFont.truetype(FONTB, 26)
    x0, x1 = 190, W - 80
    d.rectangle([x0, 8, x0 + 22, 30], fill=BLUE)
    d.text((x0 + 32, 0), "F1", font=f, fill="white")
    d.rectangle([x0 + 110, 8, x0 + 132, 30], fill=(140, 190, 255))
    d.text((x0 + 142, 0), "AUC-ROC", font=f, fill="white")
    y = 64
    for label, f1, auc in data:
        hi = label == "Hybride"
        font = fb if hi else f
        d.text((x0 - 16 - d.textlength(label, font=font), y + 18), label, font=font, fill="white")
        for k, (v, col) in enumerate([(f1, MINT if hi else BLUE), (auc, (140, 190, 255))]):
            yy = y + k * 38
            d.rounded_rectangle([x0, yy, x0 + (x1 - x0) * v, yy + 30], 6, fill=col)
            d.text((x0 + (x1 - x0) * v + 10, yy - 3), f"{v:.2f}".replace(".", ","), font=f, fill="white")
        y += 104
    im.save(os.path.join(OUT, name))
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    doc = pymupdf.open(os.path.join(REP, "main.pdf"))
    pdf_figure(doc, 28, 300, "cascade_w.png")
    pdf_figure(doc, 63, 499, "seq_deep_w.png")
    pdf_figure(doc, 64, 237, "seq_pdf_w.png")
    pdf_figure(doc, 67, 467, "pipeline_w.png")
    for src, name in [("05_evaluation_cv.png", "uc04_w.png"), ("06_analyse_approfondie.png", "uc05_w.png")]:
        im = Image.open(os.path.join(IMG, "jobtest_use_cases", src)).convert("RGB")
        trim(to_white(im.crop((0, 110, im.width, im.height)))).save(os.path.join(OUT, name))

    # deep analysis + PDF report sequences side by side
    a, b = Image.open(os.path.join(OUT, "seq_deep_w.png")), Image.open(os.path.join(OUT, "seq_pdf_w.png"))
    b = b.resize((int(b.width * a.height / b.height * 0.8), int(a.height * 0.8)), Image.LANCZOS)
    duo = Image.new("RGBA", (a.width + b.width + 160, a.height), (0, 0, 0, 0))
    duo.paste(a, (0, 0))
    duo.paste(b, (a.width + 160, (a.height - b.height) // 2))
    duo.save(os.path.join(OUT, "seq_deep_pdf_w.png"))

    logo_white(os.path.join(IMG, "Logo_ISI_Kef.png"), "logo_isi_w.png")
    logo_white(os.path.join(IMG, "Logo_UJ.png"), "logo_uj_w.png", scale=2)
    # the only CyberCloud logo available is 200 px wide: keep it as is, on its white tile
    cy = Image.open(os.path.join(IMG, "Logo_CyberCloud.png")).convert("RGB")
    cy.resize((600, 600), Image.LANCZOS).save(os.path.join(OUT, "logo_cyber.png"))

    table([
        ["Critère", "LinkedIn Recruiter", "Workable", "Greenhouse", "JobTest"],
        ["Correspondance CV/offre", "Recherche IA + recommandations", "Tri best match", "Talent Matching pondéré", "Hybride : lexical + sémantique + compétences"],
        ["Éléments explicatifs", "Synthèse IA, granularité non doc.", "Score IA non décomposé", "Scorecards", "Sous-scores + écarts + recommandations"],
        ["Écarts de compétences", "Non documenté", "Non documenté", "Non documenté", "Trouvées / manquantes / critiques"],
        ["Classement & export", "Export non documenté", "Export non documenté", "Rapport XLS", "Multi-CV + historique + rapport PDF"],
        ["Contrôle & données", "Non documenté", "Doc. sécurité générique", "Non documenté", "Cloisonnement par recruteur, VM Azure"],
    ], [330, 330, 300, 300, 440], "benchmark_w.png", fs=28, hi_col=4, center_from=9)

    t = table([
        ["Méthode", "Seuil", "Exact.", "Préc.", "Rappel", "F1", "AUC-ROC"],
        ["TF-IDF", "0,04", "0,93", "0,93", "0,97", "0,95", "0,98"],
        ["Embeddings", "0,54", "0,78", "0,81", "0,89", "0,85", "0,81"],
        ["Compétences", "0,00", "0,89", "0,89", "0,97", "0,93", "0,95"],
        ["Hybride", "0,26", "0,91", "0,94", "0,93", "0,93", "0,96"],
    ], [230, 120, 120, 120, 130, 110, 160], "resultats_table.png", fs=30, hi_row=4, mint=True)
    b = bars("resultats_bars.png")
    res = Image.new("RGBA", (t.width + 90 + b.width, max(t.height, b.height)), (0, 0, 0, 0))
    res.paste(t, (0, (res.height - t.height) // 2))
    res.paste(b, (t.width + 90, (res.height - b.height) // 2))
    res.save(os.path.join(OUT, "resultats_w.png"))

    qr = qrcode.QRCode(border=2, box_size=20, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data("http://20.51.167.202/")
    qr.make()
    qr.make_image(fill_color="#051d40", back_color="white").save(os.path.join(OUT, "qr.png"))

    # preview sheet on the template background
    skip = ("resultats_table.png", "resultats_bars.png", "seq_deep_w.png", "seq_pdf_w.png")
    names = [n for n in sorted(os.listdir(OUT)) if n.endswith(".png") and n not in skip]
    sheet = Image.new("RGB", (2400, 400 * ((len(names) + 3) // 4)), (5, 29, 64))
    for i, n in enumerate(names):
        im = Image.open(os.path.join(OUT, n)).convert("RGBA")
        print(n, im.size)
        im.thumbnail((580, 380))
        sheet.paste(im, (10 + (i % 4) * 600, 10 + (i // 4) * 400), im)
    sheet.save(os.path.join(OUT, "_preview.jpg"), quality=85)


if __name__ == "__main__":
    main()
