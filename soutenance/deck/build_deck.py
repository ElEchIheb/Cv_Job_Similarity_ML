"""Assemble le deck HTML, rend chaque slide en PNG (2x) + un PDF vectoriel.

Usage : python build_deck.py [--only 3,7] [--no-pdf] [--scale 2]
"""
import argparse
import importlib
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

import deck_base

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
ASSETS = OUT / "assets"
IMG = HERE.parent.parent / "ISI-LaTeX-Template-master" / "ISI-LaTeX-Template-master" / "img"
SHOTS = HERE.parent / "demo" / "screenshots"
URL = "http://20.51.167.202/"

HEAD = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>JobTest — Soutenance PFE</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<script src="https://unpkg.com/lucide@0.468.0/dist/umd/lucide.min.js"></script>
<style>%s</style></head><body>
"""
TAIL = """<script>
if (window.lucide) lucide.createIcons();
window.__missing = [...document.querySelectorAll('i[data-lucide]')].map(e => e.getAttribute('data-lucide'));
</script></body></html>"""


def prepare_assets():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for f in ("Logo_ISI_Kef.png", "Logo_UJ.png"):
        shutil.copy(IMG / f, ASSETS / f)
    from PIL import Image, ImageChops
    cc = Image.open(IMG / "Logo_CyberCloud.png").convert("RGB")
    box = ImageChops.difference(cc, Image.new("RGB", cc.size, (255, 255, 255))).getbbox()
    cc = cc.crop((40, 78, 158, 114))  # zone utile du logo (le reste est blanc)
    cc = cc.resize((cc.width * 4, cc.height * 4), Image.LANCZOS)
    cc.save(ASSETS / "Logo_CyberCloud.png")
    (ASSETS / "bg.svg").write_text(deck_base.bg_svg(), encoding="utf-8")
    import qrcode
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=20, border=2)
    qr.add_data(URL)
    qr.make(fit=True)
    qr.make_image(fill_color="#0A0A14", back_color="white").save(ASSETS / "qr.png")
    # captures : celles de la demo enregistree, sinon celles du rapport
    sd = ASSETS / "shots"
    sd.mkdir(exist_ok=True)
    if SHOTS.exists():
        for f in SHOTS.glob("*.png"):
            if not f.name.startswith("_"):
                shutil.copy(f, sd / f.name)
    fb = ASSETS / "report"
    fb.mkdir(exist_ok=True)
    for f in (IMG / "interfaces").glob("*"):
        if f.suffix.lower() in (".png", ".jpg"):
            shutil.copy(f, fb / f.name)
    for f in (IMG / "ai").glob("*.png"):
        shutil.copy(f, fb / f.name.replace(" ", "_"))


def all_slides():
    fns = []
    for mod in ("slides_a", "slides_b", "slides_c"):
        try:
            m = importlib.import_module(mod)
        except ModuleNotFoundError:
            continue
        fns += m.SLIDES
    return fns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--no-pdf", action="store_true")
    ap.add_argument("--scale", type=float, default=2)
    a = ap.parse_args()
    prepare_assets()
    fns = all_slides()
    html = HEAD % deck_base.CSS + "\n".join(f() for f in fns) + TAIL
    (OUT / "deck.html").write_text(html, encoding="utf-8")
    only = {int(x) for x in a.only.split(",") if x}
    (OUT / "slides").mkdir(exist_ok=True)
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, channel="chrome")
        pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=a.scale)
        pg.goto((OUT / "deck.html").as_uri(), wait_until="networkidle")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(600)
        miss = pg.evaluate("window.__missing")
        if miss:
            print("ICONES MANQUANTES:", sorted(set(miss)))
        broken = pg.evaluate("[...document.images].filter(i => !i.complete || !i.naturalWidth).map(i => i.getAttribute('src'))")
        if broken:
            print("IMAGES CASSEES:", broken)
        # detection de debordement : tout element qui depasse la zone utile de sa slide
        over = pg.evaluate("""() => { const out = [];
          document.querySelectorAll('.slide').forEach(s => { const r = s.getBoundingClientRect(); let worst = 0, wr = 0;
            s.querySelectorAll('.body *').forEach(e => { const b = e.getBoundingClientRect(); if (!b.width) return;
              worst = Math.max(worst, b.bottom - (r.bottom - 62)); wr = Math.max(wr, b.right - (r.right - 60), (r.left + 60) - b.left); });
            if (worst > 1 || wr > 1) out.push(s.id + ' bas:' + Math.round(worst) + ' cote:' + Math.round(wr)); });
          return out; }""")
        if over:
            print("DEBORDEMENTS:", over)
        n = pg.locator(".slide").count()
        for i in range(1, n + 1):
            num = int(pg.locator(".slide").nth(i - 1).get_attribute("id")[1:])
            if only and num not in only:
                continue
            pg.locator(f"#s{num}").screenshot(path=str(OUT / "slides" / f"slide_{num:02d}.png"))
        print("slides rendues:", n)
        if not a.no_pdf:
            pg.pdf(path=str(OUT / "JobTest_Soutenance_PFE.pdf"), width="1920px", height="1080px", print_background=True)
        b.close()


if __name__ == "__main__":
    sys.exit(main())
