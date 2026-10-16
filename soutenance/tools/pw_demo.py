"""Enregistreur de la demonstration JobTest (Playwright, Chrome installe).

Reutilise la session du profil persistant pw-profile/ (connexion faite par
l'utilisateur via pw_login.py). Chaque scene est enregistree dans sa propre
video (demo/raw/<scene>.webm) avec un journal de reperes temporels
(demo/raw/<scene>.json) utilise ensuite par le montage.

Usage : python pw_demo.py [scene ...]   (sans argument : toutes les scenes)
"""
import json
import os
import math
import sys
import time
import traceback
from pathlib import Path

from playwright.sync_api import sync_playwright

from demo_data import CVS, JOB_DESC, JOB_SKILLS, JOB_TITLE, cv_text

BASE = os.environ.get("JOBTEST_BASE", "https://jobtest-pfe-iheb.eastus.cloudapp.azure.com")
HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("JOBTEST_DEMO_DIR", HERE.parent / "demo"))
RAW, SHOTS = ROOT / "raw", ROOT / "screenshots"
CVDIR = HERE.parent / "demo" / "cvs"  # CV fictifs generes par make_cvs.py
THEME = os.environ.get("JOBTEST_THEME", "dark")
THEME_JS = "try{localStorage.setItem('jobtest-theme','%s')}catch(e){}" % THEME
PROFILE = HERE / "pw-profile"
VW, VH, DSF = 1600, 900, 1.2

CURSOR_JS = r"""
(() => {
  const install = () => {
    if (document.getElementById('__cur')) return;
    const c = document.createElement('div');
    c.id = '__cur';
    const svg = "<svg xmlns='http://www.w3.org/2000/svg' width='26' height='26' viewBox='0 0 24 24'><path d='M4 2 L4 19 L8.6 14.8 L11.6 21.6 L14.4 20.4 L11.4 13.8 L17.6 13.8 Z' fill='white' stroke='%23111827' stroke-width='1.4' stroke-linejoin='round'/></svg>";
    c.style.cssText = "position:fixed;left:0;top:0;width:26px;height:26px;margin:-2px 0 0 -4px;z-index:2147483647;pointer-events:none;background:url(\"data:image/svg+xml;utf8," + svg + "\") no-repeat;transform:translate(-200px,-200px);filter:drop-shadow(0 2px 3px rgba(0,0,0,.5))";
    document.documentElement.appendChild(c);
    const r = document.createElement('div');
    r.id = '__rip';
    r.style.cssText = "position:fixed;left:0;top:0;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;z-index:2147483646;pointer-events:none;border:3px solid rgba(34,211,238,.95);opacity:0;transform:translate(-200px,-200px) scale(.3)";
    document.documentElement.appendChild(r);
    addEventListener('mousemove', e => { c.style.transform = `translate(${e.clientX}px,${e.clientY}px)`; }, true);
    addEventListener('mousedown', e => {
      r.style.transition = 'none'; r.style.opacity = '1';
      r.style.transform = `translate(${e.clientX}px,${e.clientY}px) scale(.3)`;
      requestAnimationFrame(() => { r.style.transition = 'transform .45s ease-out, opacity .45s ease-out';
        r.style.transform = `translate(${e.clientX}px,${e.clientY}px) scale(1.25)`; r.style.opacity = '0'; });
    }, true);
  };
  if (document.documentElement) install();
  document.addEventListener('DOMContentLoaded', install);
})();
"""


class Scene:
    def __init__(self, ctx, name):
        self.name = name
        self.page = ctx.new_page()
        self.t0 = time.time()
        self.marks = []
        self.mx, self.my = VW * 0.6, VH * 0.55

    # -- journal -------------------------------------------------------
    def mark(self, label):
        t = round(time.time() - self.t0, 2)
        self.marks.append({"t": t, "label": label})
        print(f"  [{self.name} {t:7.2f}s] {label}", flush=True)

    def wait(self, sec):
        self.page.wait_for_timeout(int(sec * 1000))

    def shot(self, name):
        self.page.screenshot(path=str(SHOTS / f"{name}.png"))
        self.mark(f"shot:{name}")

    # -- souris --------------------------------------------------------
    def glide(self, x, y, dur=0.7):
        n = max(8, int(dur * 60))
        sx, sy = self.mx, self.my
        for i in range(1, n + 1):
            k = i / n
            e = 0.5 - 0.5 * math.cos(math.pi * k)
            self.page.mouse.move(sx + (x - sx) * e, sy + (y - sy) * e)
            self.page.wait_for_timeout(int(dur * 1000 / n))
        self.mx, self.my = x, y

    def center(self, loc):
        loc.scroll_into_view_if_needed(timeout=8000)
        b = loc.bounding_box()
        return b["x"] + b["width"] / 2, b["y"] + b["height"] / 2

    def hover(self, loc, dur=0.7, pause=0.3):
        x, y = self.center(loc)
        self.glide(x, y, dur)
        self.wait(pause)

    def click(self, loc, dur=0.7, pause=0.25, after=0.5):
        self.hover(loc, dur, pause)
        self.page.mouse.down()
        self.page.wait_for_timeout(70)
        self.page.mouse.up()
        self.wait(after)

    def type(self, loc, text, delay=28):
        self.click(loc, after=0.15)
        self.page.keyboard.type(text, delay=delay)
        self.wait(0.25)

    def scroll(self, dy, dur=1.6):
        """Defilement doux (roue) avec la souris au-dessus du contenu."""
        if self.mx < 320:
            self.glide(VW * 0.62, VH * 0.6, 0.4)
        n = max(6, int(dur * 50))
        acc = 0.0
        for i in range(1, n + 1):
            k = i / n
            target = dy * (0.5 - 0.5 * math.cos(math.pi * k))
            step = target - acc
            acc = target
            self.page.mouse.wheel(0, step)
            self.page.wait_for_timeout(int(dur * 1000 / n))

    def scroll_to(self, loc, offset=170, dur=1.6):
        y = loc.evaluate("e => e.getBoundingClientRect().top")
        self.scroll(y - offset, dur)

    def nav(self, href):
        """Clique sur l'entree de la barre laterale (transition vers la scene suivante)."""
        link = self.page.locator(f"aside a[href='{href}']").first
        self.click(link, dur=0.9, after=1.4)

    def close(self):
        v = self.page.video
        self.page.close()
        out = RAW / f"{self.name}.webm"
        if v:
            v.save_as(str(out))
            try:
                v.delete()
            except Exception:
                pass
        (RAW / f"{self.name}.json").write_text(json.dumps(self.marks, indent=1), encoding="utf-8")
        print(f"  saved {out.name}", flush=True)


def select_job(s, select_loc):
    val = select_loc.evaluate(
        "(sel, t) => { const o=[...sel.options].filter(o=>o.text.includes(t)); return o.length? o[o.length-1].value : null }", JOB_TITLE)
    if val is None:
        raise RuntimeError("job offer not found in select")
    s.hover(select_loc)
    select_loc.select_option(val)
    s.wait(0.7)


# ---------------------------------------------------------------- scenes
def sc_overview(s):
    p = s.page
    p.goto(BASE + "/overview", wait_until="domcontentloaded")
    p.get_by_text("Recent analyses").first.wait_for(timeout=30000)
    s.mark("loaded")
    s.wait(3.5)
    s.shot("overview")
    s.glide(VW * 0.6, VH * 0.5, 0.8)
    s.scroll(620, 2.6)
    s.wait(1.8)
    s.shot("overview_2")
    s.scroll(-620, 1.6)
    s.wait(0.6)
    s.mark("nav")
    s.nav("/jobs")


def sc_jobs(s):
    p = s.page
    p.goto(BASE + "/jobs", wait_until="domcontentloaded")
    p.get_by_role("button", name="Add New Job").first.wait_for(timeout=30000)
    s.wait(2.2)
    s.mark("loaded")
    exists = p.get_by_text(JOB_TITLE, exact=True).count() > 0
    if not exists:
        s.click(p.get_by_role("button", name="Add New Job").first, after=0.9)
        s.mark("modal")
        s.type(p.get_by_placeholder("e.g. Senior ML Engineer"), JOB_TITLE, 45)
        s.type(p.get_by_placeholder("Describe the role, responsibilities and requirements…"), JOB_DESC, 7)
        s.type(p.get_by_placeholder("Python, PyTorch, Docker, AWS"), JOB_SKILLS, 18)
        s.wait(0.8)
        s.shot("add_job_offer")
        s.click(p.get_by_role("button", name="Create Job Offer"), after=0.4)
        s.mark("created")
        p.get_by_text(JOB_TITLE, exact=True).first.wait_for(timeout=20000)
        s.wait(2.6)
    else:
        s.mark("job already exists")
    s.shot("job_offers")
    s.hover(p.get_by_text(JOB_TITLE, exact=True).first, 0.8, 1.2)
    s.mark("nav")
    s.nav("/analysis")


def sc_analysis(s):
    p = s.page
    c = CVS["Amira_Khelifi"]
    p.goto(BASE + "/analysis", wait_until="domcontentloaded")
    p.get_by_role("button", name="Run Evaluation").wait_for(timeout=30000)
    s.wait(2.0)
    s.mark("loaded")
    select_job(s, p.locator("select").first)
    s.type(p.get_by_placeholder("e.g. Alice Martin"), c["name"], 45)
    s.type(p.get_by_placeholder("alice@example.com"), os.environ.get("JOBTEST_CV_EMAIL", c["email"]), 30)
    s.click(p.get_by_role("button", name="Upload"), after=0.8)
    p.locator("input[type=file]").set_input_files(str(CVDIR / "Amira_Khelifi.pdf"))
    s.hover(p.get_by_text("Amira_Khelifi.pdf"), 0.7, 1.0)
    s.shot("analysis_form")
    s.click(p.get_by_role("button", name="Run Evaluation"), after=0.3)
    s.mark("eval_start")
    s.wait(1.5)
    try:
        s.shot("analysis_running")
    except Exception:
        pass
    p.get_by_role("button", name="Export PDF").wait_for(timeout=240000)
    s.mark("eval_done")
    s.glide(VW * 0.42, VH * 0.5, 0.8)
    s.wait(4.5)
    s.shot("result_score")
    s.scroll(430, 2.2)
    s.wait(2.2)
    s.shot("result_breakdown")
    tabs = p.get_by_role("button", name="Skills Match")
    s.scroll_to(tabs, 190, 1.6)
    s.wait(2.0)
    s.shot("result_skills_map")
    s.click(p.get_by_role("button", name="List", exact=True), after=1.8)
    s.shot("result_skills_list")
    s.click(p.get_by_role("button", name="Strengths & Gaps"), after=2.4)
    s.shot("result_gaps")
    s.click(p.get_by_role("button", name="Recommended Actions"), after=2.6)
    s.shot("result_actions")
    deep = p.get_by_text("AI Deep Analysis", exact=True).first
    s.scroll_to(deep, 190, 1.8)
    s.mark("deep_wait_start")
    s.wait(1.5)
    try:
        s.shot("deep_loading")
    except Exception:
        pass
    # "Career trajectory" figure aussi dans l'ecran d'attente : attendre une section propre au resultat
    done = p.get_by_text("Tailored interview questions").or_(p.get_by_text("AI analysis unavailable"))
    done.first.wait_for(timeout=300000)
    s.mark("deep_done")
    ok = p.get_by_text("Tailored interview questions").count() > 0
    s.mark("deep_status:" + ("ok" if ok else "unavailable"))
    s.wait(2.5)
    s.scroll_to(deep, 190, 0.8)
    s.wait(1.0)
    s.shot("deep_analysis")
    if ok:
        s.scroll(430, 3.0)
        s.wait(2.4)
        s.shot("deep_analysis_2")
        s.scroll(520, 3.2)
        s.wait(2.6)
        s.shot("deep_analysis_3")
    s.mark("pdf_click")
    btn = p.get_by_role("button", name="Export PDF")
    s.hover(btn, 0.9, 0.3)
    with p.expect_download(timeout=60000) as dl:
        p.mouse.down(); p.wait_for_timeout(70); p.mouse.up()
    d = dl.value
    d.save_as(str(ROOT / d.suggested_filename))
    s.mark("pdf_saved:" + d.suggested_filename)
    s.wait(2.6)
    s.shot("pdf_exported")
    s.mark("nav")
    s.nav("/leaderboard")


def sc_leaderboard(s):
    p = s.page
    p.goto(BASE + "/leaderboard", wait_until="domcontentloaded")
    p.get_by_role("button", name="Rank All Candidates").wait_for(timeout=30000)
    s.wait(2.0)
    s.mark("loaded")
    select_job(s, p.locator("select").first)
    files = [str(CVDIR / f"{k}.pdf") for k in CVS]
    p.locator("input[type=file]").set_input_files(files)
    s.wait(0.8)
    s.hover(p.get_by_text("Karim_Jaziri.pdf").first, 0.8, 1.0)
    s.shot("leaderboard_form")
    s.click(p.get_by_role("button", name="Rank All Candidates"), after=0.3)
    s.mark("rank_start")
    s.wait(2.0)
    try:
        s.shot("leaderboard_running")
    except Exception:
        pass
    p.get_by_role("button", name="Export CSV").wait_for(timeout=420000)
    s.mark("rank_done")
    s.glide(VW * 0.6, VH * 0.5, 0.6)
    s.wait(2.0)
    s.scroll_to(p.get_by_role("button", name="Rank All Candidates"), 60, 1.6)
    s.wait(4.0)
    s.shot("leaderboard_podium")
    s.scroll(520, 2.6)
    s.wait(2.6)
    s.shot("leaderboard_2")
    s.scroll(560, 2.6)
    s.wait(2.6)
    s.shot("leaderboard_3")
    csv = p.get_by_role("button", name="Export CSV")
    s.hover(csv, 0.9, 0.3)
    with p.expect_download(timeout=30000) as dl:
        p.mouse.down(); p.wait_for_timeout(70); p.mouse.up()
    dl.value.save_as(str(ROOT / dl.value.suggested_filename))
    s.mark("csv_saved")
    s.wait(1.6)
    s.mark("nav")
    s.nav("/candidates")


def sc_candidates(s):
    p = s.page
    p.goto(BASE + "/candidates", wait_until="domcontentloaded")
    p.get_by_text("Amira Khelifi").first.wait_for(timeout=30000)
    s.wait(2.4)
    s.mark("loaded")
    s.shot("candidates")
    row = p.locator("tr", has_text="Amira Khelifi").first
    s.click(row.locator("button[title=Edit]"), after=1.0)
    s.mark("modal")
    sel = p.locator("[role=dialog] select").last
    s.hover(sel)
    sel.select_option("SHORTLISTED")
    s.wait(1.0)
    s.shot("candidate_edit")
    s.click(p.get_by_role("button", name="Save Changes"), after=2.6)
    s.mark("saved")
    s.shot("candidates_after")
    s.mark("nav")
    s.nav("/history")


def sc_history(s):
    p = s.page
    p.goto(BASE + "/history", wait_until="domcontentloaded")
    p.get_by_text("Filter Analyses").wait_for(timeout=30000)
    s.wait(2.6)
    s.mark("loaded")
    s.shot("analysis_history")
    s.type(p.get_by_placeholder("e.g. Engineer"), "Machine", 60)
    s.wait(1.6)
    s.shot("analysis_history_filtered")
    s.scroll(560, 2.4)
    s.wait(2.4)
    s.shot("analysis_history_detail")
    s.scroll(-560, 1.4)
    s.mark("nav")
    s.nav("/insights")


def sc_insights(s):
    p = s.page
    p.goto(BASE + "/insights", wait_until="domcontentloaded")
    p.get_by_role("button", name="Compare All Methods").wait_for(timeout=30000)
    s.wait(2.0)
    s.mark("loaded")
    cv = p.get_by_placeholder("Paste the candidate's CV here.")
    jd = p.get_by_placeholder("Paste the job description here.")
    s.click(cv, after=0.2)
    cv.fill(cv_text("Mehdi_Gharbi"))
    s.wait(0.9)
    s.click(jd, after=0.2)
    jd.fill(JOB_DESC + "\nRequired skills: " + JOB_SKILLS)
    s.wait(1.0)
    s.shot("insights_form")
    s.click(p.get_by_role("button", name="Compare All Methods"), after=0.3)
    s.mark("compare_start")
    p.get_by_text("Score comparison").wait_for(timeout=240000)
    s.mark("compare_done")
    s.wait(1.2)
    s.scroll_to(p.get_by_text("Score comparison"), 150, 1.6)
    s.wait(3.0)
    s.shot("insights_result")
    s.scroll(520, 2.6)
    s.wait(2.6)
    s.shot("insights_table")
    s.mark("nav")
    s.scroll(-2000, 1.0)
    s.nav("/quality")


def sc_quality(s):
    p = s.page
    p.goto(BASE + "/quality", wait_until="domcontentloaded")
    p.get_by_text("AI Quality Center").first.wait_for(timeout=30000)
    s.wait(4.0)
    s.mark("loaded")
    s.shot("quality")
    s.scroll(520, 2.6)
    s.wait(2.6)
    s.shot("quality_2")
    s.scroll(560, 2.6)
    s.wait(2.6)
    s.shot("quality_3")
    s.scroll(-2000, 1.2)
    s.mark("nav")
    s.nav("/settings")


def sc_settings(s):
    p = s.page
    p.goto(BASE + "/settings", wait_until="domcontentloaded")
    p.get_by_text("Decision thresholds").first.wait_for(timeout=30000)
    s.wait(2.4)
    s.mark("loaded")
    s.shot("settings")
    s.hover(p.locator("input[type=range]").first, 0.9, 1.0)
    s.hover(p.locator("input[type=range]").nth(1), 0.6, 1.0)
    for tab, shot in (("AI Models", "settings_models"), ("System Status", "settings_system"), ("About", "settings_about")):
        s.click(p.get_by_role("button", name=tab, exact=True), after=2.2)
        s.shot(shot)
    s.click(p.get_by_role("button", name="Decision Thresholds", exact=True), after=1.2)
    s.mark("theme")
    s.click(p.locator("button[aria-label^='Switch to']").first, after=2.4)
    s.shot("theme_switched")
    s.click(p.locator("button[aria-label^='Switch to']").first, after=1.6)
    s.mark("search")
    s.click(p.get_by_role("button", name="Search…").first, after=0.9)
    p.keyboard.type("leader", delay=110)
    s.wait(1.6)
    s.shot("search")
    p.keyboard.press("Escape")
    s.wait(1.2)
    s.mark("end")


def sc_mobile(s):
    """Captures uniquement (vue mobile)."""
    p = s.page
    p.set_viewport_size({"width": 390, "height": 844})
    for path, name in (("/overview", "mobile_overview"), ("/analysis", "mobile_analysis"), ("/jobs", "mobile_jobs"), ("/history", "mobile_history")):
        p.goto(BASE + path, wait_until="domcontentloaded")
        s.wait(4.0)
        s.shot(name)


SCENES = [
    ("01_overview", sc_overview), ("02_jobs", sc_jobs), ("03_analysis", sc_analysis),
    ("04_leaderboard", sc_leaderboard), ("05_candidates", sc_candidates), ("06_history", sc_history),
    ("07_insights", sc_insights), ("08_quality", sc_quality), ("09_settings", sc_settings),
    ("10_mobile", sc_mobile),
]


def record_login():
    """Ecran de connexion, contexte vierge (aucune saisie d'identifiants)."""
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True, channel="chrome")
        ctx = b.new_context(viewport={"width": VW, "height": VH}, device_scale_factor=DSF, color_scheme=THEME,
                            record_video_dir=str(RAW / "_tmp"), record_video_size={"width": 1920, "height": 1080})
        ctx.add_init_script(CURSOR_JS)
        ctx.add_init_script(THEME_JS)
        s = Scene(ctx, "00_login")
        try:
            s.page.goto(BASE + "/login", wait_until="domcontentloaded")
            s.page.get_by_role("button", name="Sign in").wait_for(timeout=30000)
            s.wait(3.5)
            s.mark("loaded")
            s.shot("login")
            s.hover(s.page.locator("input[type=email]"), 1.0, 0.8)
            s.hover(s.page.locator("input[type=password]"), 0.6, 0.8)
            s.hover(s.page.get_by_role("button", name="Sign in"), 0.6, 1.4)
            s.mark("register")
            s.click(s.page.get_by_text("Create one"), 0.8, after=1.6)  # formulaire d'inscription, rien n'est saisi
            s.shot("register")
            for ph in ("Jane Recruiter", "you@company.com"):
                s.hover(s.page.get_by_placeholder(ph), 0.6, 0.6)
            s.hover(s.page.get_by_role("button", name="Create account"), 0.6, 1.4)
            s.mark("end")
        except Exception:
            traceback.print_exc()
        s.close()
        ctx.close()
        b.close()


def main():
    wanted = sys.argv[1:]
    for d in (RAW, SHOTS):
        d.mkdir(parents=True, exist_ok=True)
    if not wanted or "00_login" in wanted:
        print("== 00_login", flush=True)
        record_login()
    todo = [(n, f) for n, f in SCENES if not wanted or n in wanted]
    if not todo:
        return
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(PROFILE), headless=True, channel="chrome",
            viewport={"width": VW, "height": VH}, device_scale_factor=DSF, color_scheme=THEME, accept_downloads=True,
            record_video_dir=str(RAW / "_tmp"), record_video_size={"width": 1920, "height": 1080})
        ctx.add_init_script(CURSOR_JS)
        ctx.add_init_script(THEME_JS)
        for p0 in ctx.pages:
            p0.close()
        for name, fn in todo:
            print(f"== {name}", flush=True)
            s = Scene(ctx, name)
            try:
                fn(s)
                s.mark("OK")
            except Exception as e:
                s.mark("ERROR " + repr(e)[:300])
                traceback.print_exc()
                try:
                    s.page.screenshot(path=str(SHOTS / f"_error_{name}.png"))
                except Exception:
                    pass
            s.close()
        ctx.close()
    print("ALL_DONE", flush=True)


if __name__ == "__main__":
    main()
