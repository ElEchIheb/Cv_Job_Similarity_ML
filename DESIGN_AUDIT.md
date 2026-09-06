# NeuralHire — Design Audit

_Product-wide UI/UX audit performed before the design overhaul. Scope: the entire
Streamlit frontend (`frontend/`), its design system (`frontend/styles/theme.py`),
shared components (`frontend/components/ui.py`), and every page under
`frontend/pages/`._

---

## 1. Current UI inventory (100% surface map)

**Entry & chrome**
- `frontend/app.py` — single-page app, custom sidebar navigation (10 routes), executive top bar (breadcrumb, disabled search, status pill, avatar), auth gate, model loading, `run_match()` core.
- `frontend/styles/theme.py` — the entire design system: ~1,600 lines of CSS in one string constant (`PREMIUM_CSS`) + an `ICONS` dict of inline Lucide-style SVGs.
- `frontend/components/ui.py` — renderers: `page_header`, `section_label`, `stat_row`, `score_hero`, `skill_section`, `swot_section`, `recommendations_section`, `ranking_card`, `feature_card`, `architecture_table`, `premium_table`, `empty_state`, `progress_mini`, `badge_html`, and 5 matplotlib chart functions.
- `.streamlit/config.toml` — hides Streamlit's auto nav, headless server.

**Pages / routes**
| Route | File | Purpose |
|---|---|---|
| Overview | `dashboard.py` | Hero, KPI stat row, pipeline, feature cards, tech table, getting-started |
| Candidate History | `candidate_history.py` | KPI row + premium table of candidates |
| Job Offers | `job_offers.py` | KPI row + premium table of positions |
| Analysis History | `analysis_history.py` | KPI row + premium table of past matches + raw JSON viewer |
| Candidate Analysis | `single_match.py` | **Flagship** — CV/JD input, score ring, radar, AI insight, skills/gaps/actions tabs, PDF export |
| Talent Leaderboard | `ranking.py` | Multi-CV upload, ranked candidate cards, distribution chart, CSV export |
| AI Insights | `model_comparison.py` | Runs all 4 methods, comparison chart, per-method cards |
| Bulk Candidate Evaluation | `batch_analysis.py` | Spreadsheet upload, batch run, histogram, filterable results, CSV/XLSX export |
| AI Quality Center | `evaluation_metrics.py` | Benchmark table, highlight stats, figures, statistical analysis tabs |
| Settings | `settings.py` | Threshold sliders, model cards, system diagnostics, about |
| Auth | `auth.py` | Login / register forms (pre-gate) |

## 2. Current visual language
- **Palette:** "Void Black" (`#020712`–`#0E1C33`) surfaces + neon accents (blue `#00BFFF`, purple `#8B5CF6`, cyan `#00FFC8`, amber `#FFB020`, red `#FF4560`).
- **Type:** Space Grotesk (display), Inter (body), JetBrains Mono (numerics/code).
- **Geometry:** radius scale 4–28px; pill badges.
- **Depth:** heavy glow shadows + drop-shadow filters on text, icons, arcs.
- **Motion:** animated background grid pulse, perpetual icon glow pulse, status-dot pulse, button shimmer sweep, reveal/slide-in on headers & results.

## 3. Problems identified

### Critical
1. **No light mode at all.** The brief requires light *and* dark as first-class. `:root` defines only a dark palette; there is no `[data-theme]` / `prefers-color-scheme` handling and no toggle. This is the single largest gap.
2. **Reads as a "gaming/cyberpunk" site, not enterprise SaaS.** Pure void-black + saturated neon + perpetual glow/pulse animations are exactly the aesthetic the brief warns against ("Do NOT make the application look like a gaming website"). It undercuts the "trust / precision / professional" goal.
3. **Broken CSS tokens.** `var(--nh-border)` (`app.py:241`) and `var(--nh-text-secondary)` (`auth.py:14,53`) reference tokens that do not exist (real names are `--border-dim`, `--text-secondary`). They silently resolve to nothing — the auth subtitle and a divider fall back to defaults.
4. **Hundreds of hardcoded inline hex colors** across pages (`#EEF2FF`, `#8B9BBE`, `#3E4E6A`, `#7DD3FA`, `rgba(0,191,255,…)`, etc.). Because they bypass tokens, they cannot adapt to a light theme — the root cause blocking a real light mode and a source of contrast bugs.

### High
5. **Charts are dark-only.** All 5 matplotlib charts hardcode `#050B17` backgrounds and dark tick colors; on a light page they render as dark rectangles. Fails "charts work in dark mode *and* light mode."
6. **`page_header()` misuse.** `candidate_history.py`, `job_offers.py`, `analysis_history.py` pass `ICONS[...]` (raw SVG) as the `badge` text argument, so the eyebrow badge renders a stray icon instead of an uppercase label.
7. **Undefined `.nh-text` class** used in `evaluation_metrics.py` — no styling applied.
8. **Emoji leak** in `evaluation_metrics.py` tab labels (`📊 ⚖️ 🔍`) contradicts the emoji-free system and mixes icon languages.

### Medium
9. Disabled, non-functional search box in the top bar reads as dead UI.
10. Over-thin (3px) scrollbars hurt usability/accessibility.
11. Inconsistent empty states — some are the polished `nh-empty`, others are bare `st.caption`/`st.info`.
12. Radar/label contrast is low (`#8B9BBE` on near-black at 7.5pt).
13. Score/decision language ("Strong/Potential/Low Fit") is good and must be preserved; confidence is shown via a plain progress bar labeled ambiguously — must **not** be presented as a calibrated hire probability.
14. Repeated ad-hoc "colored-dot + uppercase label" markup inlined in several pages instead of a shared component.

### Low
15. Mixed shadow/border/radius values via one-off inline styles.
16. Footer version strings duplicated in multiple places.

## 4. Constraints honored
- **No backend / AI / scoring / threshold / API / DB changes.** This is purely a visual/presentation overhaul.
- All `.nh-*` class names and all `ui.py` function signatures are **preserved** so page logic keeps working; the transformation happens in the shared layer.
- The Match Score vs. Decision vs. Decision Confidence distinction is preserved; confidence is never relabeled as a probability of hire.

---

## 5. Overhaul direction (decided, no user input required)
- **One token-driven design system** with **two complete palettes** (dark + light) and a runtime theme toggle (Streamlit session-state driven, no JS needed), defaulting to dark.
- **Aesthetic recalibration** toward restrained enterprise premium (Linear / Stripe / Vercel register): deep slate surfaces instead of pure black, an indigo→violet brand accent, crisp hairline borders, tasteful depth, and *far* less glow/pulse. Motion kept fast, subtle, purposeful.
- **Semantic colors** unified (success = emerald, warning = amber, danger = rose, info = blue) and used consistently in both themes.
- **Charts made theme-aware** so they read correctly in light and dark.
- **All the bugs above fixed** and inline hardcoded colors routed through tokens so both themes are readable end-to-end.

See the final overhaul summary (in the delivery message) for exactly what changed.
