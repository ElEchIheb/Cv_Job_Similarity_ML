"""Images for the final 24-page defense deck (Canva design DAHXP_jZ7rA, 2026-10-11).

Sources only: the final thesis PDF (TikZ figures), the regenerated use-case diagram, the local
captures of the FINAL application (img/interfaces, fictitious demo data) and the verified results
of evaluation/results/calibration_report.json. Nothing is invented: the pipeline diagram below
draws the call chain of src/matching/service.py (evidence screening -> 3 signals -> fusion ->
calibration -> decision with the evidence cap -> explanation), the table copies the report.
Output: soutenance/canva_assets/final/
"""
import json
import os

import pymupdf
from PIL import Image, ImageDraw, ImageFont

import prep_canva_assets as base
from prep_canva_assets import BLUE, FONT, FONTB, MINT, REP, IMG, to_white, trim

OUT = os.path.join(base.ROOT, "canva_assets", "final")
SHOTS = os.path.join(IMG, "interfaces")
RES = os.path.join(base.ROOT, "..", "evaluation", "results", "calibration_report.json")


def ratio_crop(im, ratio=16 / 9, top=0):
    """Crop to the frame ratio, keeping the full width and the top of the screen."""
    h = round(im.width / ratio)
    if h <= im.height - top:
        return im.crop((0, top, im.width, top + h))
    w = round(im.height * ratio)
    return im.crop((0, 0, w, im.height))


def shot(name):
    return Image.open(os.path.join(SHOTS, name)).convert("RGB")


def pipeline(name):
    """Final evaluation chain, as implemented in src/matching/service.py."""
    steps = [
        ("CV + offre", "texte, PDF ou DOCX"),
        ("Contrôle des preuves", "copie de l'offre, négations,\ndéclaré / démontré"),
        ("3 signaux", "TF-IDF · embeddings\n· compétences"),
        ("Fusion", "0,2 / 0,4 / 0,4\n= score brut"),
        ("Calibration", "versionnée\n→ score sur 100"),
        ("Décision", "55 / 75\nHIRE plafonné si\npreuves insuffisantes"),
    ]
    W, H, bw, bh, gap = 2560, 640, 370, 250, 56
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ft, fs = ImageFont.truetype(FONTB, 32), ImageFont.truetype(FONT, 25)
    x0 = (W - (len(steps) * bw + (len(steps) - 1) * gap)) // 2
    y0 = 40
    for i, (title, sub) in enumerate(steps):
        x = x0 + i * (bw + gap)
        hi = title in ("Contrôle des preuves", "Calibration")
        d.rounded_rectangle([x, y0, x + bw, y0 + bh], 22, fill=(0, 113, 201, 90 if not hi else 170),
                            outline=MINT + (255,) if hi else (255, 255, 255, 200), width=4)
        d.text((x + bw / 2, y0 + 60), title, font=ft, fill="white", anchor="mm")
        d.multiline_text((x + bw / 2, y0 + 155), sub, font=fs, fill=(219, 231, 255), anchor="mm", align="center")
        if i:
            ax = x - gap + 8
            d.line([ax, y0 + bh / 2, x - 10, y0 + bh / 2], fill="white", width=5)
            d.polygon([(x - 8, y0 + bh / 2), (x - 26, y0 + bh / 2 - 12), (x - 26, y0 + bh / 2 + 12)], fill="white")
    # outputs and optional layer 2
    xd = x0 + 5 * (bw + gap) + bw / 2
    yb = y0 + bh + 70
    d.line([xd, y0 + bh, xd, yb - 6], fill="white", width=5)
    out_box = [x0 + 3 * (bw + gap), yb, x0 + 6 * (bw + gap) - gap, yb + 110]
    d.rounded_rectangle(out_box, 22, outline=(255, 255, 255, 200), width=4)
    d.text(((out_box[0] + out_box[2]) / 2, yb + 55), "Explication · historique · rapport PDF", font=ft, fill="white",
           anchor="mm")
    l2 = [x0, yb, x0 + 3 * (bw + gap) - gap - 40, yb + 110]
    for k in range(l2[0], l2[2], 28):
        d.line([k, yb, min(k + 14, l2[2]), yb], fill=(255, 255, 255, 170), width=3)
        d.line([k, yb + 110, min(k + 14, l2[2]), yb + 110], fill=(255, 255, 255, 170), width=3)
    d.text(((l2[0] + l2[2]) / 2, yb + 55), "Couche 2 locale (Ollama) : commente, ne décide pas", font=fs,
           fill=(219, 231, 255), anchor="mm")
    trim(im, 10).save(os.path.join(OUT, name))


def results_table(name):
    rows = json.load(open(RES, encoding="utf-8"))["rows"]

    def fr(x, nd=3):
        return f"{x:.{nd}f}".replace(".", ",")

    def line(label, block):
        tc, ci = block["three_class"], block["bootstrap"]["macro_f1_95ci"]
        vc = tc["verdict_counts"]
        return [label, f"{fr(tc['macro_f1'])}  [{fr(ci[0])}–{fr(ci[1])}]",
                f"{vc['REJECT']:,} / {vc['CONSIDER']} / {vc['HIRE']}".replace(",", " ")]

    after = rows["AFTER_product_shipped_calibrated"]["three_class"]["per_class"]
    ref = f"{after['REJECT']['support']} / {after['CONSIDER']['support']} / {after['HIRE']['support']}"
    return base.table([
        ["Configuration (test synthétique, 1 800 paires)", "Macro-F1 3 classes [IC 95 %]", "Verdicts R / C / H"],
        line("Hybride, score brut × 100 (avant calibration)", rows["BEFORE_product_documented_hybrid_raw_x100"]),
        line("Hybride calibré (version livrée)", rows["AFTER_product_shipped_calibrated"]),
        line("TF-IDF seul, calibré", rows["candidate_tfidf_validation_cuts"]),
        ["Référence : classes synthétiques", "—", ref],
    ], [700, 520, 420], name, fs=32, hi_row=2, center_from=1, mint=True)


def main():
    os.makedirs(OUT, exist_ok=True)
    base.OUT = OUT  # helpers save next to the other final assets
    doc = pymupdf.open(os.path.join(REP, "main.pdf"))
    base.pdf_figure(doc, 51, 403, "classes_w.png")
    uc = Image.open(os.path.join(IMG, "jobtest_use_cases", "01_global.png")).convert("RGB")
    trim(to_white(uc)).save(os.path.join(OUT, "uc_global_w.png"))
    pipeline("pipeline_final_w.png")
    results_table("resultats_final_w.png")

    # captures of the final application (16:9 frames, or the 720x548 score frame)
    shot("condidate_anal_2.png").save(os.path.join(OUT, "score_card.png"))
    ratio_crop(shot("evidence_check.png")).save(os.path.join(OUT, "evidence_check_169.png"))
    ratio_crop(shot("condidate_anal_5.png")).save(os.path.join(OUT, "deep_analysis_169.png"))
    ratio_crop(shot("condidate_anal_2.png")).save(os.path.join(OUT, "result_169.png"))
    # ranking + Quality Center side by side, centred on a 16:9 canvas of the template colour
    lb, qc = shot("talent_leader_3.png"), shot("quality_2.png")
    w = lb.width + qc.width + 40
    duo = Image.new("RGB", (w, round(w * 9 / 16)), (5, 29, 64))
    y = (duo.height - lb.height) // 2
    duo.paste(lb, (0, y))
    duo.paste(qc, (lb.width + 40, y))
    duo.save(os.path.join(OUT, "ranking_quality_169.png"))

    sheet = Image.new("RGB", (2400, 1300), (5, 29, 64))
    names = sorted(n for n in os.listdir(OUT) if n.endswith(".png"))
    for i, n in enumerate(names):
        im = Image.open(os.path.join(OUT, n)).convert("RGBA")
        print(n, im.size)
        im.thumbnail((580, 400))
        sheet.paste(im, (10 + (i % 4) * 600, 10 + (i // 4) * 430), im)
    sheet.save(os.path.join(OUT, "_preview.jpg"))


if __name__ == "__main__":
    main()
