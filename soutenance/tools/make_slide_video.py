"""Montage court (~3 min 10, limite 3 min 30) de la demonstration JobTest pour la slide video du deck.

Entrees : <JOBTEST_DEMO_DIR>/raw/<scene>.webm + <scene>.json (reperes de pw_demo.py).
Sortie  : <JOBTEST_DEMO_DIR>/JobTest_Demo_slide.mp4 (H.264, sans son : le presentateur commente).

Contrairement a make_video.py (EDL a horodatage fixe), les coupes sont calculees a partir
des reperes enregistres : chaque segment va d'un repere a un autre et recoit une duree cible ;
la vitesse en decoule et un badge « accéléré ×N » signale honnetement les passages accelerés.
Habillage aux couleurs du deck : marine #14304F, turquoise #0E9F94, corail #F07A5A.
"""
import base64
import json
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from playwright.sync_api import sync_playwright

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = Path(__file__).resolve().parent
DEMO = Path(os.environ.get("JOBTEST_DEMO_DIR", HERE.parent / "demo_https"))
RAW, WORK = DEMO / "raw", DEMO / "work_slide"
QR_B64 = base64.b64encode((HERE.parent / "canva_assets" / "light" / "qr_demo.png").read_bytes()).decode()
URL = "jobtest-pfe-iheb.eastus.cloudapp.azure.com"
FPS = 30

# (scene, repere debut, repere fin, duree cible en s, legende, etape)
# Un repere peut etre decale : "nav+1.5". "start" = 1 s apres l'ouverture de la page.
PLAN = [
    ("00_login", "start", "register", 4.0, "Connexion sécurisée — HTTPS + JWT", "1"),
    ("00_login", "register", "end", 4.0, "Création de compte recruteur", "1"),
    ("01_overview", "loaded-0.5", "nav+1.4", 9.0, "Tableau de bord du recruteur", "2"),
    ("02_jobs", "loaded-0.5", "modal", 2.5, "Création d'une offre d'emploi", "3"),
    ("02_jobs", "modal", "created", 5.0, "Création d'une offre d'emploi", "3"),
    ("02_jobs", "created", "nav+1.4", 3.5, "Offre créée", "3"),
    ("03_analysis", "loaded-0.5", "eval_start", 6.0, "Évaluation d'un CV au format PDF", "4"),
    ("03_analysis", "eval_start", "eval_done", 3.0, "Calcul : TF-IDF + sémantique + compétences", "4"),
    ("03_analysis", "eval_done", "deep_wait_start", 30.0, "Score calibré, verdict et compétences expliqués", "5"),
    ("03_analysis", "deep_wait_start", "deep_done", 3.0, "Analyse approfondie — LLM local (Ollama)", "6"),
    ("03_analysis", "deep_done", "pdf_click", 18.0, "Le LLM commente, le score ne change pas", "6"),
    ("03_analysis", "pdf_click", "nav+1.4", 5.0, "Export du rapport PDF", "7"),
    ("04_leaderboard", "loaded-0.5", "rank_start", 4.0, "Classement de 4 CV pour une offre", "8"),
    ("04_leaderboard", "rank_start", "rank_done", 3.0, "Classement de 4 CV pour une offre", "8"),
    ("04_leaderboard", "rank_done", "nav+1.4", 20.0, "Podium, détail par candidat, export CSV", "8"),
    ("05_candidates", "loaded-0.5", "nav+1.4", 9.0, "Suivi des candidats — statuts", "9"),
    ("06_history", "loaded-0.5", "nav+1.4", 9.0, "Historique des analyses et filtres", "10"),
    ("07_insights", "loaded-0.5", "compare_start", 4.0, "Comparer les 4 méthodes de scoring", "11"),
    ("07_insights", "compare_start", "compare_done", 2.5, "Comparer les 4 méthodes de scoring", "11"),
    ("07_insights", "compare_done", "nav+1.4", 11.0, "Comparer les 4 méthodes de scoring", "11"),
    ("08_quality", "loaded-0.5", "nav+1.4", 11.0, "AI Quality Center — benchmark du moteur", "12"),
    ("09_settings", "loaded-0.5", "theme", 11.0, "Paramètres — seuils de décision et modèles", "13"),
    ("09_settings", "theme", "end+1.0", 8.0, "Thème clair / sombre et recherche rapide", "13"),
]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700;800&display=swap');
*{margin:0;padding:0;box-sizing:border-box}html,body{width:1920px;height:1080px;background:transparent;font-family:Inter,sans-serif}
.cap{position:absolute;left:50%;bottom:34px;transform:translateX(-50%);display:flex;align-items:center;gap:18px;padding:12px 32px 12px 12px;border-radius:999px;
 background:rgba(20,48,79,.94);border:2px solid #0E9F94;box-shadow:0 14px 40px rgba(20,48,79,.35);white-space:nowrap}
.n{min-width:50px;height:50px;padding:0 12px;border-radius:999px;background:#0E9F94;display:grid;place-items:center;font:800 24px Inter;color:#fff}
.t{font:600 30px Inter;color:#fff}
.sp{position:absolute;right:36px;top:36px;padding:10px 24px;border-radius:999px;background:#F07A5A;color:#fff;font:700 26px Inter;box-shadow:0 8px 24px rgba(240,122,90,.35)}
.card{width:1920px;height:1080px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;background:#F9FEFF}
.k{font:700 26px Inter;letter-spacing:.2em;color:#0E9F94}
.h{font:800 150px/1 Inter;letter-spacing:-.03em;color:#14304F}
.bar{width:120px;height:10px;border-radius:5px;background:#F07A5A}
.s{font:600 40px Inter;color:#14304F}.m{font:500 28px Inter;color:#475569}
.url{font:700 34px Inter;color:#0B7F76}
.qr{background:#fff;border:2px solid #DCE5EE;border-radius:24px;padding:14px}
"""


def run(args):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:])
        raise SystemExit("ffmpeg a échoué")


def marks(scene):
    f = RAW / f"{scene}.json"
    m = {}
    for e in json.loads(f.read_text(encoding="utf-8")):
        m.setdefault(e["label"], e["t"])  # premier passage
    return m


def at(m, ref):
    if ref == "start":
        return 1.0
    for op in ("+", "-"):
        if op in ref[1:]:
            name, off = ref.rsplit(op, 1)
            base = m.get(name)
            return None if base is None else base + (float(off) if op == "+" else -float(off))
    return m.get(ref)


def edl():
    out = []
    for scene, a, b, target, cap, step in PLAN:
        if not (RAW / f"{scene}.webm").exists():
            print("  manquant :", scene)
            continue
        m = marks(scene)
        ta, tb = at(m, a), at(m, b)
        if ta is None or tb is None or tb - ta < 0.3:
            print(f"  ignore {scene} {a}->{b} (repere absent)")
            continue
        ta = max(0.0, ta)
        speed = max(1.0, (tb - ta) / target)
        out.append((scene, ta, tb, speed, cap, step))
    return out


def render_overlays(plan):
    WORK.mkdir(parents=True, exist_ok=True)
    caps = sorted({(c, s) for *_, c, s in plan})
    speeds = sorted({round(v) for _, _, _, v, _, _ in plan if v >= 1.95})
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, channel="chrome")
        pg = b.new_page(viewport={"width": 1920, "height": 1080})

        def shot(html, path, transparent=True):
            pg.set_content(f"<style>{CSS}</style>{html}", wait_until="networkidle")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(250)
            pg.screenshot(path=str(path), omit_background=transparent)
        for i, (c, s) in enumerate(caps):
            shot(f'<div class="cap"><span class="n">{s}</span><span class="t">{c}</span></div>', WORK / f"cap_{i}.png")
        for v in speeds:
            shot(f'<div class="sp">accéléré ×{v}</div>', WORK / f"sp_{v}.png")
        shot('<div class="card"><div class="k">DÉMONSTRATION EN DIRECT · MICROSOFT AZURE</div><div class="h">JobTest</div><div class="bar"></div>'
             '<div class="s">Parcours complet du recruteur</div>'
             '<div class="m">CV de démonstration fictifs · plateforme déployée en HTTPS</div></div>', WORK / "intro.png", False)
        shot('<div class="card"><div class="k">13 FONCTIONNALITÉS · UN SEUL PARCOURS</div>'
             f'<div class="qr"><img src="data:image/png;base64,{QR_B64}" style="width:240px;height:240px;display:block"></div>'
             f'<div class="url">{URL}</div><div class="m">Scannez pour tester la plateforme</div></div>', WORK / "outro.png", False)
        b.close()
    return {cs: i for i, cs in enumerate(caps)}


def still(png, out, dur):
    run(["-loop", "1", "-t", f"{dur}", "-i", str(png), "-vf", f"fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.4,fade=t=out:st={dur-0.4}:d=0.4",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(out)])


def build(plan, capidx):
    parts = []
    intro = WORK / "p_000_intro.mp4"
    still(WORK / "intro.png", intro, 3.0)
    parts.append((intro, 3.0))
    for i, (scene, a, bb, v, cap, step) in enumerate(plan, 1):
        out = WORK / f"p_{i:03d}_{scene}.mp4"
        dur = (bb - a) / v
        inputs = ["-ss", f"{a:.2f}", "-t", f"{bb - a:.2f}", "-i", str(RAW / f"{scene}.webm"), "-i", str(WORK / f"cap_{capidx[(cap, step)]}.png")]
        fc = f"[0:v]crop=1600:900:0:0,setpts=(PTS-STARTPTS)/{v:.4f},fps={FPS},scale=1920:1080:flags=lanczos[v0];[v0][1:v]overlay=0:0[v1]"
        last = "v1"
        if v >= 1.95:
            inputs += ["-i", str(WORK / f"sp_{round(v)}.png")]
            fc += ";[v1][2:v]overlay=0:0[v2]"
            last = "v2"
        fades = []
        if i == 1 or plan[i - 2][0] != scene:
            fades.append("fade=t=in:st=0:d=0.3")
        if i == len(plan) or plan[i][0] != scene:
            fades.append(f"fade=t=out:st={max(0, dur - 0.3):.2f}:d=0.3")
        fc += f";[{last}]{','.join(fades) if fades else 'null'},format=yuv420p[vo]"
        run([*inputs, "-filter_complex", fc, "-map", "[vo]", "-an", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
             "-pix_fmt", "yuv420p", "-r", str(FPS), str(out)])
        parts.append((out, dur))
        print(f"  {i:02d}/{len(plan)} {scene} {a:6.1f}-{bb:6.1f}s x{v:4.1f} -> {dur:4.1f}s  {cap}", flush=True)
    outro = WORK / "p_999_outro.mp4"
    still(WORK / "outro.png", outro, 4.0)
    parts.append((outro, 4.0))
    return parts


def main():
    plan = edl()
    if not plan:
        raise SystemExit("aucun enregistrement")
    capidx = render_overlays(plan)
    parts = build(plan, capidx)
    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p, _ in parts), encoding="utf-8")
    out = DEMO / "JobTest_Demo_slide.mp4"
    run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", "-movflags", "+faststart", str(out)])
    total = sum(d for _, d in parts)
    print("OK", out, f"{total:.1f}s", f"{out.stat().st_size / 1e6:.1f} Mo")


if __name__ == "__main__":
    sys.exit(main())
