"""Capture the thesis screenshots from a LOCAL JobTest instance (final code).

Prerequisites (see scripts/seed_demo_screens.py):
  * API on http://127.0.0.1:8000 started on a throwaway database and seeded;
  * frontend on http://localhost:3000 (``npm --prefix web run dev``);
  * optionally Ollama for the deep-analysis screen.

All data visible on the captures is fictitious (seed script, fictitious PDF CVs
of ``D:/education/pfe/pdfs test``). Rendered by the locally installed Google Chrome (fresh profile), no retouching.

Usage: python scripts/capture_screens.py [--out <dir>] [--only name1,name2]
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from seed_demo_screens import DEMO_EMAIL, DEMO_PASSWORD  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
WEB = "http://localhost:3000"
PDF_DIR = Path("D:/education/pfe/pdfs test")
DEFAULT_OUT = ROOT / "ISI-LaTeX-Template-master" / "ISI-LaTeX-Template-master" / "img" / "interfaces"

FULLSTACK_CV = (
    "PROFILE\nWeb developer with 3 years of experience building web applications.\n\n"
    "EXPERIENCE\nWeb Developer (3 years): built React and JavaScript front ends, REST APIs with Node.js and "
    "Express.js, stored data in MySQL with SQL queries, versioned code with Git; pages in HTML and CSS.\n\n"
    "EDUCATION\nBachelor in computer science\n\n"
    "SKILLS\nJavaScript, React, Node.js, Express.js, SQL, MySQL, Git, HTML, CSS"
)
STUFFED_CV = (
    "PROFILE\nGraphic designer with 3 years of experience in branding.\n\n"
    "EXPERIENCE\nDesigner (3 years): produced visual identities and print layouts.\n\n"
    "SKILLS\nPython, SQL, Apache Airflow, Apache Spark, Docker, Kafka, AWS, dbt, Adobe Illustrator"
)


def settle(page: Page, secs: float = 1.2) -> None:
    page.wait_for_load_state("networkidle")
    time.sleep(secs)


# Dashboard screens whose left navigation bar is cropped for legibility in the
# thesis (the bar is identical on every page and shown on the overview capture).
CROP_SIDEBAR = {
    "job_offers", "add_job_offer", "condidate_history", "analysis_history", "plateform_settings",
    "condidate_anal_1", "condidate_anal_2", "condidate_anal_3", "condidate_anal_4", "condidate_anal_5",
    "evidence_check", "talent_leader_1", "talent_leader_2", "talent_leader_3", "talent_leader_4",
    "insights", "quality_1", "quality_2", "quality_3",
}
SIDEBAR_CSS_PX = 261  # sidebar width in CSS pixels (border at x = 260)


def crop_sidebar(path: Path, scale: float = 1.25) -> None:
    from PIL import Image

    im = Image.open(path)
    im.crop((round(SIDEBAR_CSS_PX * scale), 0, im.width, im.height)).save(path)


# The thesis shows no date of any work: dates, timestamps, the year in job codes
# and the date inside the calibration identifier are masked with bullets on the
# rendered page just before each capture (visible redaction, nothing else changes).
MASK_DATES_JS = r"""
() => {
  const bullets = (m) => m.replace(/[0-9A-Za-zÀ-ÿ]/g, "•");
  const rules = [
    [/JOB-\d{4}-/g, (m) => "JOB-••••-"],
    [/(synthetic-v\d+-)\d{4}-\d{2}-\d{2}/g, (m, p) => p + "••••-••-••"],
    [/\b\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?/g, bullets],
    [/\b\d{1,2}\/\d{1,2}\/\d{2,4}(?:,? \d{1,2}:\d{2})?/g, bullets],
    [/\b\d{1,2} [A-Za-zÀ-ÿ]{3,9}\.? \d{4}(?:,? \d{1,2}:\d{2})?/g, bullets],
    [/\b(?:19|20)\d{2}\b/g, bullets],
  ];
  const mask = (s) => rules.reduce((acc, [re, fn]) => acc.replace(re, fn), s);
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let n = walker.nextNode(); n; n = walker.nextNode()) {
    const v = mask(n.nodeValue);
    if (v !== n.nodeValue) n.nodeValue = v;
  }
  document.querySelectorAll("input[placeholder], textarea[placeholder]").forEach((el) => {
    el.placeholder = mask(el.placeholder);
  });
  document.querySelectorAll("option").forEach((o) => { o.textContent = mask(o.textContent); });
}
"""


def shot(page: Page, out: Path, name: str, only: set[str] | None) -> None:
    if only and name not in only:
        return
    path = out / f"{name}.png"
    page.evaluate(MASK_DATES_JS)
    page.screenshot(path=str(path))
    if name in CROP_SIDEBAR:
        crop_sidebar(path)
    print("captured", name)


def select_offer(page: Page, title: str) -> None:
    sel = page.locator("select").first
    value = sel.evaluate(
        "(el, t) => [...el.options].find(o => o.textContent.includes(t))?.value", title)
    sel.select_option(value)


def scroll_to_text(page: Page, text: str, offset: int = 110) -> None:
    page.get_by_text(text, exact=True).first.evaluate(
        "(el, off) => window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - off)", offset)
    time.sleep(0.8)


def login(page: Page) -> None:
    page.goto(f"{WEB}/login")
    settle(page)
    page.fill("input[type=email]", DEMO_EMAIL)
    page.fill("input[type=password]", DEMO_PASSWORD)
    page.get_by_role("button", name="Sign in").click()
    page.wait_for_url("**/overview", timeout=30000)
    settle(page)


def desktop(pw, out: Path, only: set[str] | None) -> None:
    browser = pw.chromium.launch(channel="chrome")
    ctx = browser.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1.25,
                              color_scheme="dark", reduced_motion="reduce")
    page = ctx.new_page()

    page.goto(f"{WEB}/login")
    settle(page)
    shot(page, out, "login", only)
    page.get_by_role("button", name="No account yet?").click()
    time.sleep(0.8)
    shot(page, out, "register", only)

    login(page)
    shot(page, out, "overview", only)
    page.keyboard.press("Control+K")
    time.sleep(0.8)
    shot(page, out, "search", only)
    page.keyboard.press("Escape")

    page.goto(f"{WEB}/jobs"); settle(page)
    shot(page, out, "job_offers", only)
    page.get_by_role("button", name="Add New Job").first.click(); time.sleep(0.8)
    shot(page, out, "add_job_offer", only)
    page.keyboard.press("Escape")

    page.goto(f"{WEB}/candidates"); settle(page)
    shot(page, out, "condidate_history", only)
    page.goto(f"{WEB}/history"); settle(page)
    shot(page, out, "analysis_history", only)

    page.goto(f"{WEB}/settings"); settle(page)
    shot(page, out, "plateform_settings", only)

    page.goto(f"{WEB}/quality"); settle(page, 2.5)
    shot(page, out, "quality_1", only)
    scroll_to_text(page, "1. Quality of the displayed verdicts (synthetic test split)", 90)
    shot(page, out, "quality_2", only)
    scroll_to_text(page, "3. Robustness to manipulated CVs (synthetic validation split)", 90)
    shot(page, out, "quality_3", only)

    # Candidate analysis — fictitious full-stack CV
    if not only or only & {"condidate_anal_1", "condidate_anal_2", "condidate_anal_3", "condidate_anal_4", "condidate_anal_5"}:
        page.goto(f"{WEB}/analysis"); settle(page)
        select_offer(page, "Full Stack Web Developer")
        page.get_by_placeholder("e.g. Alice Martin").fill("Marc Dubois")
        page.get_by_placeholder("alice@example.com").fill("marc.dubois@example.com")
        page.get_by_placeholder("Paste the candidate's CV text here…").fill(FULLSTACK_CV)
        time.sleep(0.5)
        shot(page, out, "condidate_anal_1", only)
        page.get_by_role("button", name="Run Evaluation").click()
        page.get_by_role("button", name="Export PDF").wait_for(timeout=180000)
        settle(page, 2.0)
        page.evaluate("window.scrollTo(0, 0)"); time.sleep(0.6)
        shot(page, out, "condidate_anal_2", only)
        scroll_to_text(page, "Score breakdown", 170)
        shot(page, out, "condidate_anal_3", only)
        scroll_to_text(page, "Skills Match", 170)
        shot(page, out, "condidate_anal_4", only)
        try:
            page.get_by_text("Recruiter summary").first.wait_for(timeout=420000)
        except Exception:  # noqa: BLE001 — capture whatever state Layer 2 reached
            print("deep analysis did not finish; capturing its current state")
        time.sleep(1.0)
        scroll_to_text(page, "AI Deep Analysis", 170)
        shot(page, out, "condidate_anal_5", only)

    # Evidence check — keyword-stuffed fictitious CV
    if not only or "evidence_check" in only:
        page.goto(f"{WEB}/analysis"); settle(page)
        select_offer(page, "Data Engineer")
        page.get_by_placeholder("e.g. Alice Martin").fill("Paul Lambert")
        page.get_by_placeholder("alice@example.com").fill("paul.lambert@example.com")
        page.get_by_placeholder("Paste the candidate's CV text here…").fill(STUFFED_CV)
        page.get_by_role("button", name="Run Evaluation").click()
        page.get_by_role("button", name="Export PDF").wait_for(timeout=180000)
        settle(page, 2.0)
        page.evaluate("window.scrollTo(0, 0)"); time.sleep(0.6)
        shot(page, out, "evidence_check", only)

    # Talent leaderboard — 18 fictitious PDF CVs
    if not only or only & {"talent_leader_1", "talent_leader_2", "talent_leader_3", "talent_leader_4"}:
        page.goto(f"{WEB}/leaderboard"); settle(page)
        select_offer(page, "Full Stack Web Developer")
        page.set_input_files("input[type=file]", sorted(str(p) for p in PDF_DIR.glob("cv_*.pdf")))
        time.sleep(0.8)
        shot(page, out, "talent_leader_1", only)
        page.get_by_role("button", name="Rank All Candidates").click()
        page.get_by_text("Score distribution").wait_for(timeout=600000)
        settle(page, 2.0)
        scroll_to_text(page, "Score distribution", 90)
        shot(page, out, "talent_leader_2", only)
        scroll_to_text(page, "Podium · Top 3", 90)
        shot(page, out, "talent_leader_3", only)
        page.evaluate("window.scrollBy(0, 520)"); time.sleep(0.8)
        shot(page, out, "talent_leader_4", only)

    if not only or "insights" in only:
        page.goto(f"{WEB}/insights"); settle(page)
        page.get_by_placeholder("Paste the candidate's CV here.").fill(FULLSTACK_CV)
        page.get_by_placeholder("Paste the job description here.").fill(
            "Full Stack Web Developer. Required: JavaScript, TypeScript, React, Node.js, Express.js, REST API, SQL, "
            "Git, Docker, HTML, CSS. Build REST APIs and modern web applications.")
        page.get_by_role("button", name="Compare All Methods").click()
        page.get_by_text("Calibrated score comparison (/100)").wait_for(timeout=180000)
        settle(page, 1.5)
        scroll_to_text(page, "Calibrated score comparison (/100)", 90)
        shot(page, out, "insights", only)
    browser.close()


def mobile(pw, out: Path, only: set[str] | None) -> None:
    if only and not only & {"phone_1", "phone_2"}:
        return
    browser = pw.chromium.launch(channel="chrome")
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True,
                              has_touch=True, color_scheme="dark", reduced_motion="reduce")
    page = ctx.new_page()
    login(page)
    shot(page, out, "phone_1", only)
    page.goto(f"{WEB}/history"); settle(page)
    shot(page, out, "phone_2", only)
    browser.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    only = {s.strip() for s in args.only.split(",") if s.strip()} or None
    with sync_playwright() as pw:
        desktop(pw, out, only)
        mobile(pw, out, only)
