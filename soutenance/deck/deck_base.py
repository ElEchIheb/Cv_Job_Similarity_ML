"""Systeme de design + helpers du deck de soutenance JobTest (1920x1080)."""
import math
import random

TOTAL = 38
FOOT = "JobTest — PFE 2025/2026"

CSS = r"""
@page{size:1920px 1080px;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
:root{--bg0:#0A0A14;--bg1:#12121F;--vio:#8B5CF6;--vio2:#A78BFA;--cy:#22D3EE;--ink:#F4F4FA;--mut:#A9A9C0;--dim:#6F7086;
--line:rgba(255,255,255,.11);--card:rgba(255,255,255,.045);--green:#10B981;--green2:#34D399;--orange:#F59E0B;--orange2:#FBBF24;--red:#EF4444;--red2:#F87171}
html,body{background:#05050A}
body{font-family:'Inter',sans-serif;color:var(--ink);-webkit-font-smoothing:antialiased}
.slide{width:1920px;height:1080px;position:relative;overflow:hidden;background:#0A0A14;page-break-after:always;break-after:page}
.slide::before{content:"";position:absolute;inset:0;background:
 radial-gradient(980px 640px at 92% -10%,rgba(139,92,246,.24),transparent 62%),
 radial-gradient(860px 600px at -8% 112%,rgba(34,211,238,.14),transparent 62%),
 linear-gradient(135deg,#0A0A14 0%,#12121F 100%)}
.slide::after{content:"";position:absolute;inset:0;background:url(assets/bg.svg) center/cover no-repeat;opacity:.5}
.inner{position:absolute;inset:0;padding:52px 84px 84px;display:flex;flex-direction:column;z-index:2}
.kicker{font:600 19px/1 'JetBrains Mono',monospace;letter-spacing:.17em;color:var(--cy);text-transform:uppercase;display:flex;align-items:center;gap:14px}
.kicker::before{content:"";width:34px;height:3px;border-radius:3px;background:linear-gradient(90deg,var(--vio),var(--cy))}
h1{font:700 54px/1.14 'Space Grotesk',sans-serif;margin-top:14px;letter-spacing:-.012em}
.g{background:linear-gradient(90deg,#8B5CF6 0%,#22D3EE 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
.body{flex:1;margin-top:30px;min-height:0;display:flex;flex-direction:column;position:relative}
.foot{position:absolute;left:84px;right:84px;bottom:26px;display:flex;justify-content:space-between;align-items:center;font:500 18px 'Inter';color:#74758C;z-index:3}
.foot b{font:600 17px 'JetBrains Mono';color:#9A9BB2}
.foot .bar{position:absolute;left:0;right:0;top:-14px;height:2px;background:rgba(255,255,255,.07);border-radius:2px}
.foot .bar i{display:block;height:100%;border-radius:2px;background:linear-gradient(90deg,var(--vio),var(--cy))}
.row{display:flex;gap:24px}.col{display:flex;flex-direction:column;gap:20px}
.ac{align-items:center}.jc{justify-content:center}.jb{justify-content:space-between}.f1{flex:1;min-width:0}.wrap{flex-wrap:wrap}
.grid{display:grid;gap:22px}
.card{background:var(--card);border:1.5px solid var(--line);border-radius:22px;padding:26px 28px;position:relative}
.card.v{border-color:rgba(139,92,246,.55);background:rgba(139,92,246,.09)}
.card.c{border-color:rgba(34,211,238,.5);background:rgba(34,211,238,.06)}
.card.r{border-color:rgba(239,68,68,.55);background:rgba(239,68,68,.07)}
.card.gr{border-color:rgba(16,185,129,.5);background:rgba(16,185,129,.06)}
.card.o{border-color:rgba(245,158,11,.5);background:rgba(245,158,11,.06)}
.ct{font:700 31px/1.2 'Space Grotesk'}
.lbl{font:600 18px/1.2 'JetBrains Mono';letter-spacing:.14em;text-transform:uppercase;color:var(--mut)}
.mut{color:var(--mut)}.dim{color:var(--dim)}.cy{color:var(--cy)}.vi{color:var(--vio2)}.gn{color:var(--green2)}.or{color:var(--orange2)}.rd{color:var(--red2)}
.mono{font-family:'JetBrains Mono',monospace}
.big{font:700 86px/1 'Space Grotesk';letter-spacing:-.02em}
.t22{font-size:22px}.t24{font-size:24px}.t26{font-size:26px}.t28{font-size:28px}.t30{font-size:30px}.t32{font-size:32px}.t34{font-size:34px}.t36{font-size:36px}.t20{font-size:20px}.t18{font-size:18px}
.fill{flex:1;min-height:0}.gfill{flex:1;min-height:0;grid-auto-rows:1fr}
.b{font-weight:700}.sb{font-weight:600}
ul.pl{list-style:none;display:flex;flex-direction:column;gap:11px}
ul.pl li{position:relative;padding-left:28px;font-size:27px;line-height:1.3;color:#DDDDEA}
ul.pl li::before{content:"";position:absolute;left:2px;top:.52em;width:9px;height:9px;border-radius:50%;background:linear-gradient(135deg,var(--vio),var(--cy))}
.bd{display:inline-flex;align-items:center;gap:9px;border-radius:999px;padding:10px 22px;font:600 24px/1.15 'Inter';border:1.5px solid;white-space:nowrap}
.bd.sm{font-size:20px;padding:7px 16px}
.bd.lg{font-size:28px;padding:13px 28px}
.bd-g{color:#6EE7B7;border-color:rgba(16,185,129,.6);background:rgba(16,185,129,.13)}
.bd-o{color:#FCD34D;border-color:rgba(245,158,11,.6);background:rgba(245,158,11,.13)}
.bd-r{color:#FCA5A5;border-color:rgba(239,68,68,.6);background:rgba(239,68,68,.13)}
.bd-v{color:#C4B5FD;border-color:rgba(139,92,246,.65);background:rgba(139,92,246,.15)}
.bd-c{color:#67E8F9;border-color:rgba(34,211,238,.6);background:rgba(34,211,238,.10)}
.bd-n{color:#D7D7E6;border-color:rgba(255,255,255,.2);background:rgba(255,255,255,.05)}
.bd-solid{color:#fff;border-color:transparent;background:linear-gradient(90deg,var(--vio),var(--cy))}
code,.code{font-family:'JetBrains Mono',monospace;color:var(--cy);font-size:.92em}
.ic{display:inline-grid;place-items:center;border-radius:16px;background:rgba(139,92,246,.16);border:1.5px solid rgba(139,92,246,.4);color:#C4B5FD;width:72px;height:72px;flex:none}
.ic.c{background:rgba(34,211,238,.11);border-color:rgba(34,211,238,.4);color:#67E8F9}
.ic.g{background:rgba(16,185,129,.12);border-color:rgba(16,185,129,.45);color:#6EE7B7}
.ic.r{background:rgba(239,68,68,.12);border-color:rgba(239,68,68,.45);color:#FCA5A5}
.ic.o{background:rgba(245,158,11,.12);border-color:rgba(245,158,11,.45);color:#FCD34D}
.ic.sm{width:56px;height:56px;border-radius:14px}
.ic svg.lucide{width:52%;height:52%;stroke-width:1.8}
svg.lucide{width:1em;height:1em;stroke-width:2;vertical-align:-.14em}
.arr{flex:none;display:inline-flex;align-items:center}
table.t{border-collapse:separate;border-spacing:0;width:100%;font-size:25px}
table.t th,table.t td{padding:14px 18px;border-bottom:1px solid rgba(255,255,255,.09);text-align:left;vertical-align:middle;line-height:1.28}
table.t th{font:600 21px 'JetBrains Mono';letter-spacing:.06em;text-transform:uppercase;color:var(--mut);background:rgba(255,255,255,.05)}
table.t th:first-child{border-radius:14px 0 0 0}table.t th:last-child{border-radius:0 14px 0 0}
table.t td.hl,table.t th.hl{background:rgba(139,92,246,.2);color:#fff;border-left:1.5px solid rgba(139,92,246,.6);border-right:1.5px solid rgba(139,92,246,.6)}
table.t th.hl{color:#DDD6FE;border-top:1.5px solid rgba(139,92,246,.6)}
table.t tr:last-child td.hl{border-bottom:1.5px solid rgba(139,92,246,.6);border-radius:0 0 14px 0}
.num{font-variant-numeric:tabular-nums}
.glow{box-shadow:0 0 0 1px rgba(139,92,246,.35),0 24px 80px -20px rgba(139,92,246,.55)}
.hr{height:1px;background:var(--line);width:100%}
.logo-pill{background:#fff;border-radius:18px;display:flex;align-items:center;justify-content:center;padding:14px 26px;height:92px}
.logo-pill img{max-height:62px;max-width:300px;display:block}
.shot{border-radius:14px;overflow:hidden;border:1.5px solid rgba(255,255,255,.14);background:#0d0d18;box-shadow:0 18px 50px -18px rgba(0,0,0,.8)}
.shot img{display:block;width:100%;height:100%;object-fit:cover;object-position:top left}
"""


def ic(name, cls="", size=None):
    st = f' style="width:{size}px;height:{size}px"' if size else ""
    return f'<span class="ic {cls}"{st}><i data-lucide="{name}"></i></span>'


def li(name, style=""):
    return f'<i data-lucide="{name}" style="{style}"></i>'


def bd(text, color="n", cls="", icon=None):
    i = li(icon) if icon else ""
    return f'<span class="bd bd-{color} {cls}">{i}{text}</span>'


def arrow(w=60, color="#22D3EE", dashed=False, vertical=False, h=18, sw=3):
    dash = ' stroke-dasharray="7 7"' if dashed else ""
    if vertical:
        return (f'<span class="arr"><svg width="{h}" height="{w}" viewBox="0 0 {h} {w}">'
                f'<line x1="{h/2}" y1="0" x2="{h/2}" y2="{w-9}" stroke="{color}" stroke-width="{sw}"{dash} stroke-linecap="round"/>'
                f'<path d="M{h/2-7},{w-11} L{h/2},{w-1} L{h/2+7},{w-11} Z" fill="{color}"/></svg></span>')
    return (f'<span class="arr"><svg width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<line x1="0" y1="{h/2}" x2="{w-9}" y2="{h/2}" stroke="{color}" stroke-width="{sw}"{dash} stroke-linecap="round"/>'
            f'<path d="M{w-11},{h/2-7} L{w-1},{h/2} L{w-11},{h/2+7} Z" fill="{color}"/></svg></span>')


def slide(n, kicker, title, body, cls="", head=True):
    pct = n / TOTAL * 100
    h = f'<div class="kicker">{kicker}</div><h1>{title}</h1>' if head else ""
    return (f'<section class="slide {cls}" id="s{n}"><div class="inner">{h}<div class="body">{body}</div></div>'
            f'<div class="foot"><div class="bar"><i style="width:{pct:.2f}%"></i></div><span>{FOOT}</span>'
            f'<b>{n:02d} / {TOTAL}</b></div></section>')


def bg_svg(seed=7, w=1920, h=1080, n=95):
    """Reseau de points connectes (clin d'oeil a l'ecran de login)."""
    rnd = random.Random(seed)
    pts = []
    for _ in range(n):
        # densite plus forte sur les bords, centre plus calme
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        cx, cy = abs(x - w / 2) / (w / 2), abs(y - h / 2) / (h / 2)
        if max(cx, cy) < 0.45 and rnd.random() < 0.7:
            continue
        pts.append((x, y, rnd.uniform(1.4, 3.4)))
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">']
    for i, (x1, y1, _) in enumerate(pts):
        for (x2, y2, _) in pts[i + 1:]:
            d = math.hypot(x1 - x2, y1 - y2)
            if d < 190:
                o = (1 - d / 190) * 0.42
                col = "#8B5CF6" if (x1 + x2) / 2 > w * 0.5 else "#22D3EE"
                out.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{col}" stroke-width="1" opacity="{o:.2f}"/>')
    for (x, y, r) in pts:
        col = "#A78BFA" if x > w * 0.5 else "#67E8F9"
        out.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r:.1f}" fill="{col}" opacity=".75"/>')
    out.append("</svg>")
    return "".join(out)


# ----------------------------------------------------------- diagrammes SVG
def seq_svg(w, h, actors, msgs, fs=20, top=64, step=62, first=40, frames=None, colors=None):
    """Diagramme de sequence epure. msgs: (src, dst, label, kind) kind in call|ret|self|note."""
    n = len(actors)
    xs = [w * (i + 0.5) / n for i in range(n)]
    bw = min(250, w / n - 22)
    o = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="display:block;font-family:Inter,sans-serif">',
         '<defs><marker id="ah" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11 Z" fill="#22D3EE"/></marker>'
         '<marker id="ahr" markerWidth="12" markerHeight="12" refX="10" refY="6" orient="auto"><path d="M1,1 L11,6 L1,11" fill="none" stroke="#A78BFA" stroke-width="2"/></marker></defs>']
    for i, (x, a) in enumerate(zip(xs, actors)):
        col = (colors or {}).get(i, "rgba(139,92,246,.55)")
        o.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{h-6}" stroke="rgba(255,255,255,.22)" stroke-width="2" stroke-dasharray="6 8"/>')
        o.append(f'<rect x="{x-bw/2}" y="4" width="{bw}" height="{top-8}" rx="14" fill="#191930" stroke="{col}" stroke-width="2"/>')
        o.append(f'<text x="{x}" y="{top/2+7}" text-anchor="middle" fill="#F4F4FA" font-size="{fs+1}" font-weight="700">{a}</text>')
    y = top + first
    for fr in (frames or []):
        fx1, fx2, fy1, fy2, lab, col = fr
        o.append(f'<rect x="{fx1}" y="{fy1}" width="{fx2-fx1}" height="{fy2-fy1}" rx="12" fill="rgba(255,255,255,.025)" stroke="{col}" stroke-width="2" stroke-dasharray="8 6"/>')
        tw = len(lab) * 12 + 26
        o.append(f'<rect x="{fx2-tw}" y="{fy1}" width="{tw}" height="30" rx="8" fill="{col}"/>')
        o.append(f'<text x="{fx2-tw+13}" y="{fy1+21}" fill="#0A0A14" font-size="17" font-weight="800" font-family="JetBrains Mono,monospace">{lab}</text>')
    for (s, d, lab, kind) in msgs:
        if kind == "gap":
            y += lab
            continue
        x1, x2 = xs[s], xs[d]
        if kind == "self":
            o.append(f'<path d="M{x1},{y-14} h46 v30 h-40" fill="none" stroke="#22D3EE" stroke-width="2.5" marker-end="url(#ah)"/>')
            o.append(f'<text x="{x1+58}" y="{y+7}" fill="#E7E7F3" font-size="{fs}" font-weight="500">{lab}</text>')
        else:
            dash = ' stroke-dasharray="8 6"' if kind == "ret" else ""
            col = "#A78BFA" if kind == "ret" else "#22D3EE"
            mk = "ahr" if kind == "ret" else "ah"
            pad = 4 if x2 > x1 else -4
            o.append(f'<line x1="{x1}" y1="{y}" x2="{x2-pad}" y2="{y}" stroke="{col}" stroke-width="2.5"{dash} marker-end="url(#{mk})"/>')
            fam = ' font-family="JetBrains Mono,monospace"' if lab.startswith(("POST", "GET", "/")) else ""
            fill = "#67E8F9" if fam else ("#D9CFFF" if kind == "ret" else "#E7E7F3")
            o.append(f'<text x="{(x1+x2)/2}" y="{y-11}" text-anchor="middle" fill="{fill}" font-size="{fs}" font-weight="500"{fam}>{lab}</text>')
        y += step
    o.append("</svg>")
    return "".join(o)


def fr(v, nd=2):
    return f"{v:.{nd}f}".replace(".", ",")


def bars_svg(rows, w=760, h=330, bh=26, gap=74, fs=21):
    """Barres groupees F1 / AUC. rows: (label, f1, auc, highlight)."""
    left, top = 200, 20
    sc = (w - left - 80)
    o = [f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" style="display:block;font-family:Inter,sans-serif">',
         '<defs><linearGradient id="gv" x1="0" x2="1"><stop offset="0" stop-color="#8B5CF6"/><stop offset="1" stop-color="#A78BFA"/></linearGradient>'
         '<linearGradient id="gc" x1="0" x2="1"><stop offset="0" stop-color="#0EA5C4"/><stop offset="1" stop-color="#22D3EE"/></linearGradient></defs>']
    for t in (0, .25, .5, .75, 1):
        x = left + sc * t
        o.append(f'<line x1="{x}" y1="{top-6}" x2="{x}" y2="{top+gap*len(rows)-12}" stroke="rgba(255,255,255,.10)" stroke-width="1.5"/>')
        o.append(f'<text x="{x}" y="{top+gap*len(rows)+14}" text-anchor="middle" fill="#8E8FA6" font-size="18">{str(t).replace(".", ",")}</text>')
    for i, (lab, f1, auc, hl) in enumerate(rows):
        y = top + i * gap
        o.append(f'<text x="{left-16}" y="{y+bh+2}" text-anchor="end" fill="{"#fff" if hl else "#D7D7E6"}" font-size="{fs+2}" font-weight="{800 if hl else 600}">{lab}</text>')
        o.append(f'<rect x="{left}" y="{y}" width="{sc*f1}" height="{bh}" rx="6" fill="url(#gv)"/>')
        o.append(f'<text x="{left+sc*f1+8}" y="{y+bh-6}" fill="#C4B5FD" font-size="{fs}" font-weight="700">{fr(f1)}</text>')
        o.append(f'<rect x="{left}" y="{y+bh+4}" width="{sc*auc}" height="{bh}" rx="6" fill="url(#gc)"/>')
        o.append(f'<text x="{left+sc*auc+8}" y="{y+2*bh-2}" fill="#67E8F9" font-size="{fs}" font-weight="700">{fr(auc)}</text>')
    o.append("</svg>")
    return "".join(o)
