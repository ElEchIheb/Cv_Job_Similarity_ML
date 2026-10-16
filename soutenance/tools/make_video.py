"""Montage de la video de demonstration JobTest.

Entrees : demo/raw/<scene>.webm (enregistrements Playwright 1080p).
Sorties : demo/JobTest_Demo.mp4 (H.264 + AAC, musique d'ambiance synthetisee).

- chaque segment est coupe, accelere si besoin, legende (bandeau bas) ;
- les attentes (frappe, calculs, LLM) sont accelerees et signalees par un badge « xN » ;
- cartons d'intro / de fin rendus en HTML ; musique douce generee par numpy (aucun fichier tiers).
"""
import math
import subprocess
import sys
import wave
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from playwright.sync_api import sync_playwright

FF = imageio_ffmpeg.get_ffmpeg_exe()
HERE = Path(__file__).resolve().parent
DEMO = HERE.parent / "demo"
RAW, WORK = DEMO / "raw", DEMO / "work"
QR = HERE.parent / "deck" / "out" / "assets" / "qr.png"
FPS = 30
QR_B64 = __import__("base64").b64encode(QR.read_bytes()).decode()
BASE = 1.3  # acceleration generale des passages « normaux »

# (scene, debut, fin, vitesse, legende, etape)
EDL = [
    ("00_login", 1.2, 13.6, 1.25, "Connexion sécurisée — session JWT", "1"),
    ("01_overview", 1.0, 27.0, BASE, "Vue d'ensemble — indicateurs du recruteur", "2"),
    ("02_jobs", 2.0, 6.3, 1.0, "Création d'une offre d'emploi", "3"),
    ("02_jobs", 6.3, 37.0, 3.2, "Création d'une offre d'emploi", "3"),
    ("02_jobs", 37.0, 50.5, 1.1, "Offre créée — code attribué automatiquement", "3"),
    ("03_analysis", 2.0, 21.2, 1.5, "Évaluation d'un CV — fichier PDF", "4"),
    ("03_analysis", 21.2, 39.0, 5.0, "Calcul : TF-IDF + embeddings + compétences", "4"),
    ("03_analysis", 39.0, 62.0, 1.0, "Résultat explicable — score, verdict, radar", "5"),
    ("03_analysis", 62.0, 95.0, BASE, "Compétences, forces et écarts, recommandations", "5"),
    ("03_analysis", 95.0, 106.0, 3.0, "Analyse approfondie — LLM local (Ollama)", "6"),
    ("03_analysis", 106.0, 131.5, 1.05, "Analyse approfondie — le score ne change pas", "6"),
    ("03_analysis", 131.5, 146.5, 1.15, "Export du rapport PDF", "7"),
    ("04_leaderboard", 2.0, 14.2, BASE, "Talent Leaderboard — 4 CV, une offre", "8"),
    ("04_leaderboard", 14.2, 19.5, 1.0, "Classement multi-CV", "8"),
    ("04_leaderboard", 19.5, 58.5, BASE, "Podium, détail par candidat, export CSV", "8"),
    ("05_candidates", 2.0, 22.0, 1.2, "Suivi des candidats — pipeline de statuts", "9"),
    ("06_history", 2.0, 25.5, BASE, "Historique des analyses — filtres et détail", "10"),
    ("07_insights", 2.0, 12.6, 1.4, "AI Insights — comparer les 4 méthodes", "11"),
    ("07_insights", 12.6, 38.0, BASE, "AI Insights — comparer les 4 méthodes", "11"),
    ("08_quality", 3.0, 30.5, 1.35, "AI Quality Center — benchmark du moteur", "12"),
    ("09_settings", 2.0, 26.0, BASE, "Paramètres — seuils de décision, modèles, état", "13"),
    ("09_settings", 26.0, 42.6, 1.15, "Thème clair / sombre et recherche rapide", "13"),
]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&family=Space+Grotesk:wght@600;700&family=JetBrains+Mono:wght@600;700&display=swap');
*{margin:0;padding:0;box-sizing:border-box}html,body{width:1920px;height:1080px;background:transparent;font-family:Inter,sans-serif;color:#F4F4FA}
.g{background:linear-gradient(90deg,#8B5CF6,#22D3EE);-webkit-background-clip:text;color:transparent}
.cap{position:absolute;left:50%;bottom:34px;transform:translateX(-50%);display:flex;align-items:center;gap:18px;padding:13px 30px 13px 14px;border-radius:999px;
 background:rgba(10,10,20,.90);border:1.5px solid rgba(139,92,246,.75);box-shadow:0 16px 50px rgba(0,0,0,.6);white-space:nowrap}
.n{min-width:48px;height:48px;padding:0 12px;border-radius:999px;background:linear-gradient(135deg,#8B5CF6,#22D3EE);display:grid;place-items:center;font:700 24px 'Space Grotesk';color:#fff}
.t{font:600 30px Inter}
.sp{position:absolute;right:36px;top:92px;padding:10px 22px;border-radius:999px;background:rgba(245,158,11,.94);color:#1a1205;font:700 26px 'JetBrains Mono'}
.card{width:1920px;height:1080px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:26px;
 background:radial-gradient(1000px 640px at 88% -10%,rgba(139,92,246,.30),transparent 62%),radial-gradient(900px 600px at -6% 110%,rgba(34,211,238,.18),transparent 62%),linear-gradient(135deg,#0A0A14,#12121F)}
.k{font:700 24px 'JetBrains Mono';letter-spacing:.24em;color:#22D3EE}
.h{font:700 150px/1 'Space Grotesk';letter-spacing:-.02em;padding-bottom:10px}
.s{font:600 40px 'Space Grotesk';color:#D7D7E6}.m{font:500 28px Inter;color:#A9A9C0}
.url{font:700 42px 'JetBrains Mono';color:#22D3EE}
"""


def run(args):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        print(r.stderr[-1500:])
        raise SystemExit("ffmpeg a échoué")


def render_overlays():
    WORK.mkdir(parents=True, exist_ok=True)
    caps = sorted({(c, s) for *_, c, s in EDL})
    speeds = sorted({round(v) for _, _, _, v, _, _ in EDL if v >= 2})
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
        shot('<div class="card"><div class="k">DÉMONSTRATION DE LA PLATEFORME</div><div class="h g">JobTest</div>'
             '<div class="s">Aide au recrutement · mise en correspondance CV / offres</div>'
             '<div class="m">Projet de fin d\'études 2025–2026 · Iheb El Ech · CyberCloud Solutions</div></div>', WORK / "intro.png", False)
        shot('<div class="card"><div class="k">13 FONCTIONNALITÉS · 1 SEUL PARCOURS</div><div class="h g" style="font-size:120px">Merci</div>'
             f'<div style="background:#fff;border-radius:20px;padding:12px"><img src="data:image/png;base64,{QR_B64}" style="width:200px;height:200px;display:block"></div>'
             '<div class="url">http://20.51.167.202/</div><div class="m">CV de démonstration fictifs · plateforme déployée sur Microsoft Azure</div></div>', WORK / "outro.png", False)
        b.close()
    return {cs: i for i, cs in enumerate(caps)}


def still(png, out, dur):
    run(["-loop", "1", "-t", f"{dur}", "-i", str(png), "-vf", f"fps={FPS},format=yuv420p,fade=t=in:st=0:d=0.5,fade=t=out:st={dur-0.5}:d=0.5",
         "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", str(out)])


def build_segments(capidx):
    parts = []
    intro = WORK / "p_000_intro.mp4"
    still(WORK / "intro.png", intro, 3.6)
    parts.append((intro, 3.6))
    prev_scene = None
    for i, (scene, a, bb, v, cap, step) in enumerate(EDL, 1):
        out = WORK / f"p_{i:03d}_{scene}.mp4"
        dur = (bb - a) / v
        inputs = ["-ss", f"{a}", "-t", f"{bb - a}", "-i", str(RAW / f"{scene}.webm"), "-i", str(WORK / f"cap_{capidx[(cap, step)]}.png")]
        fc = f"[0:v]crop=1600:900:0:0,setpts=PTS/{v},fps={FPS},scale=1920:1080:flags=lanczos[v0];[v0][1:v]overlay=0:0[v1]"
        last = "v1"
        if v >= 2:
            inputs += ["-i", str(WORK / f"sp_{round(v)}.png")]
            fc += f";[v1][2:v]overlay=0:0[v2]"
            last = "v2"
        fades = []
        if scene != prev_scene:
            fades.append("fade=t=in:st=0:d=0.35")
        nxt = EDL[i][0] if i < len(EDL) else None
        if nxt != scene:
            fades.append(f"fade=t=out:st={max(0, dur - 0.35):.2f}:d=0.35")
        fc += f";[{last}]{','.join(fades) if fades else 'null'},format=yuv420p[vo]"
        if not out.exists():  # reprise possible : un segment termine n'est pas recalcule
            tmp = out.with_suffix(".tmp.mp4")
            run([*inputs, "-filter_complex", fc, "-map", "[vo]", "-an", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                 "-pix_fmt", "yuv420p", "-r", str(FPS), str(tmp)])
            tmp.replace(out)
        parts.append((out, dur))
        prev_scene = scene
        print(f"  segment {i:02d}/{len(EDL)} {scene} {a}-{bb} x{v} -> {dur:.1f}s", flush=True)
    outro = WORK / "p_999_outro.mp4"
    still(WORK / "outro.png", outro, 4.5)
    parts.append((outro, 4.5))
    return parts


def music(seconds, path, sr=44100):
    """Nappe d'ambiance douce : accords tenus + notes cristallines lentes, reverb simple."""
    rng = np.random.default_rng(7)
    n = int(seconds * sr)
    t = np.arange(n) / sr
    out = np.zeros((n, 2))
    f = lambda m: 440.0 * 2 ** ((m - 69) / 12)
    chords = [[48, 55, 60, 64, 67, 71], [45, 52, 57, 60, 64, 67], [41, 48, 53, 57, 60, 64], [43, 50, 55, 59, 62, 67]]  # Cmaj7 Am7 Fmaj7 G
    bar = 8.0
    nb = int(math.ceil(seconds / bar)) + 1
    for bi in range(nb):
        ch = chords[bi % 4]
        st = bi * bar
        i0, i1 = int(st * sr), min(n, int((st + bar + 3.0) * sr))
        if i0 >= n:
            break
        tt = t[i0:i1] - st
        env = np.clip(tt / 2.6, 0, 1) * np.clip((bar + 3.0 - tt) / 3.0, 0, 1)
        env = np.sin(env * np.pi / 2) ** 2
        for k, m in enumerate(ch):
            fr = f(m)
            amp = 0.060 if k < 2 else 0.042
            pan = 0.5 + 0.32 * math.sin(k * 1.9 + bi)
            for det in (-0.25, 0.22):
                ph = rng.uniform(0, 2 * np.pi)
                w = np.sin(2 * np.pi * (fr + det) * tt + ph) + 0.22 * np.sin(2 * np.pi * 2 * (fr + det) * tt + ph * 1.7)
                w *= amp * env * (1 + 0.08 * np.sin(2 * np.pi * 0.11 * tt + k))
                out[i0:i1, 0] += w * (1 - pan)
                out[i0:i1, 1] += w * pan
        # notes cristallines : une toutes les 2 temps, tirees de l'accord a l'octave superieure
        for j in range(4):
            m = ch[2 + (j * 2 + bi) % 4] + 12
            ps = st + j * 2.0 + 0.5
            j0, j1 = int(ps * sr), min(n, int((ps + 3.2) * sr))
            if j0 >= n:
                continue
            pt = t[j0:j1] - ps
            w = np.sin(2 * np.pi * f(m) * pt) * np.exp(-pt * 1.7) * np.clip(pt / 0.012, 0, 1) * 0.055
            pan = 0.3 + 0.4 * ((j + bi) % 2)
            out[j0:j1, 0] += w * (1 - pan)
            out[j0:j1, 1] += w * pan
    # reverb : quelques echos filtres
    wet = np.zeros_like(out)
    for d, g in ((0.089, .42), (0.137, .34), (0.211, .27), (0.337, .2), (0.523, .14)):
        k = int(d * sr)
        wet[k:] += out[:-k][:, ::-1] * g
    out = out * 0.8 + wet * 0.55
    # passe-bas doux (moyenne glissante) + fondu
    k = 9
    ker = np.ones(k) / k
    out[:, 0] = np.convolve(out[:, 0], ker, mode="same")
    out[:, 1] = np.convolve(out[:, 1], ker, mode="same")
    fade = np.clip(t / 2.5, 0, 1) * np.clip((seconds - t) / 4.0, 0, 1)
    out *= fade[:, None]
    out *= 0.30 / max(1e-9, np.abs(out).max())
    pcm = (out * 32767).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes())


def main():
    print("rendu des habillages…", flush=True)
    capidx = render_overlays()
    for f in WORK.glob("*.tmp.mp4"):
        f.unlink()
    print("segments…", flush=True)
    parts = build_segments(capidx)
    total = sum(d for _, d in parts)
    lst = WORK / "concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p, _ in parts), encoding="utf-8")
    silent = WORK / "video_silent.mp4"
    run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
    print(f"musique… ({total:.1f}s)", flush=True)
    wav = WORK / "music.wav"
    music(total + 0.5, wav)
    out = DEMO / "JobTest_Demo.mp4"
    run(["-i", str(silent), "-i", str(wav), "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(out)])
    print("OK", out, f"{total:.1f}s", f"{out.stat().st_size/1e6:.1f} Mo")


if __name__ == "__main__":
    sys.exit(main())
