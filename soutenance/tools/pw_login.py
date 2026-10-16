"""Phase A : ouvre une fenetre Chromium sur la page de connexion JobTest.
L'utilisateur se connecte lui-meme ; la session reste dans le profil persistant
(pw-profile/) et sera reutilisee par l'enregistreur de demo. Aucun identifiant
n'est lu ni ecrit par ce script."""
import os, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE = os.environ.get("JOBTEST_BASE", "https://jobtest-pfe-iheb.eastus.cloudapp.azure.com")
PROFILE = Path(__file__).parent / "pw-profile"
WAIT_MIN = int(sys.argv[1]) if len(sys.argv) > 1 else 45

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(PROFILE), headless=False, channel="chrome", viewport={"width": 1280, "height": 720},
        args=["--window-size=1300,820", "--window-position=60,40"])
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto(BASE + "/login", wait_until="domcontentloaded")
    print("WAITING_FOR_LOGIN", flush=True)
    deadline = time.time() + WAIT_MIN * 60
    ok = False
    while time.time() < deadline:
        try:
            if "/login" not in page.url:
                ok = True
                break
            page.wait_for_timeout(1000)
        except Exception as e:
            print("WINDOW_CLOSED", e, flush=True)
            break
    if ok:
        page.wait_for_timeout(2500)
        print("LOGGED_IN", page.url, flush=True)
    else:
        print("NO_LOGIN", flush=True)
    ctx.close()
