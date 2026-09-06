"""
frontend/styles/theme.py
NeuralHire — Design System v5.0  ("Calm Intelligence")

A single, token-driven design system with TWO complete, first-class palettes
(dark + light) selected at runtime via ``build_css(theme)``. Every colour is a
CSS custom property, so the whole product re-themes coherently with no hardcoded
palette in the component CSS.

Design register: restrained enterprise premium (indigo→violet brand, slate
surfaces, hairline borders, tasteful depth, fast/subtle motion) — deliberately
NOT the neon-glow "gaming" look of v4.

Back-compat: all ``.nh-*`` class names and the ``ICONS`` dict are preserved so
every existing page keeps rendering. ``PREMIUM_CSS`` and ``inject_css()`` still
exist (defaulting to the dark theme).
"""
from __future__ import annotations

# ─── SVG Icon Library (Lucide-style, stroke-based, currentColor) ─────────────
ICONS = {
    # Navigation
    "home":         '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="m3 9 9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>',
    "target":       '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>',
    "users":        '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    "bar-chart":    '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>',
    "folder":       '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>',
    "trending-up":  '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>',
    "settings":     '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg>',
    # Actions
    "upload":       '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>',
    "download":     '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
    "play":         '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg>',
    "search":       '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>',
    "zap":          '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>',
    "check":        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>',
    "x":            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>',
    "alert":        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
    "info":         '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
    # Data
    "brain":        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2Z"/></svg>',
    "activity":     '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>',
    "layers":       '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></svg>',
    "cpu":          '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M9 2v2M15 20v2M9 20v2M2 15h2M2 9h2M20 15h2M20 9h2"/></svg>',
    "award":        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/></svg>',
    "file-text":    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>',
    "shield":       '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>',
    "grid":         '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>',
    "star":         '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    "arrow-right":  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>',
    "clock":        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    "user":         '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
    "briefcase":    '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>',
    "radar":        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M19.07 4.93A10 10 0 0 0 6.99 3.34"/><path d="M4 6h.01"/><path d="M2.29 9.62A10 10 0 1 0 21.31 8.35"/><path d="M16.24 7.76A6 6 0 1 0 8.23 16.67"/><path d="M12 18h.01"/><path d="M17.99 11.66A6 6 0 0 1 15.77 16.67"/><circle cx="12" cy="12" r="2"/><path d="m13.41 10.59 5.66-5.66"/></svg>',
    "chevron-right":'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6"/></svg>',
    "sliders":      '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/></svg>',
    "bell":         '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    "sparkles":     '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.9 4.6L18.5 9.5 13.9 11.4 12 16l-1.9-4.6L5.5 9.5l4.6-1.9z"/><path d="M19 14l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z"/></svg>',
    "sun":          '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>',
    "moon":         '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>',
}


# ═══════════════════════════════════════════════════════════════════════════
# TOKEN PALETTES  (the two first-class themes)
# ═══════════════════════════════════════════════════════════════════════════

_DARK = {
    # App surfaces
    "bg-app":        "#0A0E17",
    "bg-app-2":      "#0D1220",
    "surface":       "#111726",
    "surface-2":     "#161D2E",
    "surface-3":     "#1C2438",
    "sidebar-bg":    "#0C111C",
    "topbar-bg":     "rgba(17,23,38,0.72)",
    "input-bg":      "#0E1420",
    # Borders
    "border":        "rgba(148,163,184,0.12)",
    "border-strong": "rgba(148,163,184,0.22)",
    "border-focus":  "rgba(99,102,241,0.55)",
    "hover":         "rgba(148,163,184,0.06)",
    "track":         "rgba(148,163,184,0.12)",
    # Text
    "text-primary":  "#F1F5F9",
    "text-secondary":"#94A3B8",
    "text-muted":    "#64748B",
    "text-faint":    "#475569",
    "text-accent":   "#A5B4FC",
    "text-code":     "#7DD3FC",
    # Brand + accent
    "brand":         "#6366F1",
    "brand-2":       "#8B5CF6",
    "accent":        "#06B6D4",
    "brand-ink":     "#A5B4FC",
    "brand-bg":      "rgba(99,102,241,0.12)",
    "brand-bd":      "rgba(99,102,241,0.30)",
    "accent-bg":     "rgba(6,182,212,0.12)",
    # Semantics
    "success":       "#10B981",
    "warn":          "#F59E0B",
    "danger":        "#F43F5E",
    "info":          "#3B82F6",
    "success-ink":   "#34D399",
    "warn-ink":      "#FBBF24",
    "danger-ink":    "#FB7185",
    "info-ink":      "#60A5FA",
    "success-bg":    "rgba(16,185,129,0.12)",
    "warn-bg":       "rgba(245,158,11,0.12)",
    "danger-bg":     "rgba(244,63,94,0.12)",
    "info-bg":       "rgba(59,130,246,0.12)",
    "success-bd":    "rgba(16,185,129,0.28)",
    "warn-bd":       "rgba(245,158,11,0.28)",
    "danger-bd":     "rgba(244,63,94,0.28)",
    "info-bd":       "rgba(59,130,246,0.28)",
    # Depth
    "shadow-sm":     "0 1px 2px rgba(0,0,0,0.4)",
    "shadow-md":     "0 6px 22px rgba(0,0,0,0.42)",
    "shadow-lg":     "0 18px 48px rgba(0,0,0,0.55)",
    "ring-accent":   "0 0 0 1px rgba(99,102,241,0.10)",
    # App backdrop wash (subtle, static — no animated grid)
    "app-wash": ("radial-gradient(1100px 460px at 82% -8%, rgba(99,102,241,0.10), transparent 60%),"
                 "radial-gradient(900px 420px at 8% 4%, rgba(6,182,212,0.06), transparent 55%)"),
    "scrollbar":     "rgba(148,163,184,0.28)",
    "scrollbar-hover":"rgba(148,163,184,0.45)",
    "code-bg":       "rgba(99,102,241,0.10)",
}

_LIGHT = {
    "bg-app":        "#F4F6FB",
    "bg-app-2":      "#EEF1F8",
    "surface":       "#FFFFFF",
    "surface-2":     "#F7F9FC",
    "surface-3":     "#EEF2F8",
    "sidebar-bg":    "#FFFFFF",
    "topbar-bg":     "rgba(255,255,255,0.82)",
    "input-bg":      "#FFFFFF",
    "border":        "rgba(15,23,42,0.09)",
    "border-strong": "rgba(15,23,42,0.16)",
    "border-focus":  "rgba(99,102,241,0.55)",
    "hover":         "rgba(15,23,42,0.035)",
    "track":         "rgba(15,23,42,0.08)",
    "text-primary":  "#0F172A",
    "text-secondary":"#475569",
    "text-muted":    "#64748B",
    "text-faint":    "#94A3B8",
    "text-accent":   "#4F46E5",
    "text-code":     "#0369A1",
    "brand":         "#6366F1",
    "brand-2":       "#7C3AED",
    "accent":        "#0891B2",
    "brand-ink":     "#4F46E5",
    "brand-bg":      "rgba(99,102,241,0.10)",
    "brand-bd":      "rgba(99,102,241,0.28)",
    "accent-bg":     "rgba(8,145,178,0.10)",
    "success":       "#059669",
    "warn":          "#D97706",
    "danger":        "#E11D48",
    "info":          "#2563EB",
    "success-ink":   "#047857",
    "warn-ink":      "#B45309",
    "danger-ink":    "#BE123C",
    "info-ink":      "#1D4ED8",
    "success-bg":    "rgba(5,150,105,0.10)",
    "warn-bg":       "rgba(217,119,6,0.10)",
    "danger-bg":     "rgba(225,29,72,0.09)",
    "info-bg":       "rgba(37,99,235,0.09)",
    "success-bd":    "rgba(5,150,105,0.26)",
    "warn-bd":       "rgba(217,119,6,0.26)",
    "danger-bd":     "rgba(225,29,72,0.24)",
    "info-bd":       "rgba(37,99,235,0.24)",
    "shadow-sm":     "0 1px 2px rgba(15,23,42,0.06)",
    "shadow-md":     "0 6px 20px rgba(15,23,42,0.08)",
    "shadow-lg":     "0 18px 44px rgba(15,23,42,0.12)",
    "ring-accent":   "0 0 0 1px rgba(99,102,241,0.06)",
    "app-wash": ("radial-gradient(1100px 460px at 82% -8%, rgba(99,102,241,0.07), transparent 60%),"
                 "radial-gradient(900px 420px at 8% 4%, rgba(8,145,178,0.05), transparent 55%)"),
    "scrollbar":     "rgba(15,23,42,0.20)",
    "scrollbar-hover":"rgba(15,23,42,0.34)",
    "code-bg":       "rgba(99,102,241,0.07)",
}


def _root_block(theme: str) -> str:
    tokens = _LIGHT if theme == "light" else _DARK
    lines = "\n".join(f"  --{k}: {v};" for k, v in tokens.items())
    scheme = "light" if theme == "light" else "dark"
    return f":root{{\n  color-scheme: {scheme};\n{lines}\n}}\n"


# Structural tokens shared by both themes (geometry + motion + gradients that
# reference the palette variables above).
_SHARED_ROOT = """
:root {
  --grad-brand:   linear-gradient(135deg, var(--brand) 0%, var(--brand-2) 100%);
  --grad-success: linear-gradient(135deg, var(--success) 0%, var(--accent) 100%);
  --grad-warn:    linear-gradient(135deg, var(--warn) 0%, #FB7185 100%);
  --grad-danger:  linear-gradient(135deg, var(--danger) 0%, var(--brand-2) 100%);

  --r-xs: 6px;  --r-sm: 9px;  --r-md: 12px;
  --r-lg: 16px; --r-xl: 20px; --r-2xl: 26px; --r-full: 9999px;

  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.4, 0.64, 1);
  --t-fast: 0.13s; --t-mid: 0.22s; --t-slow: 0.4s;

  /* legacy aliases kept so any stray old references still resolve */
  --nh-border: var(--border);
  --nh-text-secondary: var(--text-secondary);
  --neon-blue: var(--brand);
  --neon-purple: var(--brand-2);
  --neon-cyan: var(--accent);
  --neon-amber: var(--warn);
  --neon-red: var(--danger);
  --border-dim: var(--border);
  --border-soft: var(--border-strong);
  --border-bright: var(--border-strong);
  --text-code: var(--text-code);
  --bg-elevated: var(--surface-2);
  --grad-card: var(--surface);
  --shadow-card: var(--shadow-md);
  --shadow-blue: var(--shadow-md);
}
"""


# ═══════════════════════════════════════════════════════════════════════════
# STATIC COMPONENT CSS  (uses ONLY tokens → works in both themes)
# ═══════════════════════════════════════════════════════════════════════════

_BODY_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

/* ── Hide Streamlit auto multi-page nav / chrome noise ── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"],
#MainMenu, footer,
[data-testid="stDecoration"],
[data-testid="manage-app-button"] {
  display: none !important;
}

/* Keep the sidebar collapse/expand controls usable & on-brand */
header[data-testid="stHeader"],
[data-testid="stToolbar"] {
  background: transparent !important;
  box-shadow: none !important;
  pointer-events: none !important;
}
header[data-testid="stHeader"] *,
[data-testid="stToolbar"] * { pointer-events: auto !important; }

[data-testid="collapsedControl"],
[data-testid="stSidebarExpandButton"] button,
[data-testid="stSidebarCollapseButton"] {
  color: var(--brand) !important;
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-sm) !important;
  box-shadow: var(--shadow-sm) !important;
  transition: all var(--t-fast) var(--ease) !important;
}
[data-testid="collapsedControl"]:hover,
[data-testid="stSidebarCollapseButton"]:hover {
  border-color: var(--brand-bd) !important;
  background: var(--surface-2) !important;
}
[data-testid="collapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg { color: var(--brand) !important; }

*, *::before, *::after { box-sizing: border-box; }

html, body, .stApp,
[data-testid="stAppViewContainer"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.stApp {
  background: var(--bg-app) !important;
  min-height: 100vh;
}
.stApp::before {
  content: '';
  position: fixed; inset: 0;
  background: var(--app-wash);
  pointer-events: none;
  z-index: 0;
}

.main .block-container {
  padding: 1.6rem 2.4rem 4rem 2.4rem !important;
  max-width: 1400px !important;
  position: relative;
  z-index: 1;
}

/* ═══ SIDEBAR ═══ */
section[data-testid="stSidebar"] {
  background: var(--sidebar-bg) !important;
  border-right: 1px solid var(--border) !important;
  box-shadow: var(--shadow-md) !important;
}
section[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"],
section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { display: none !important; }

section[data-testid="stSidebar"] .stButton { margin-bottom: 3px !important; }
section[data-testid="stSidebar"] .stButton > button {
  display: flex !important; align-items: center !important; justify-content: flex-start !important;
  gap: 11px !important; text-align: left !important; width: 100% !important;
  padding: 9px 13px !important; font-size: 0.86rem !important; font-weight: 500 !important;
  border-radius: var(--r-sm) !important; box-shadow: none !important;
  transition: all var(--t-fast) var(--ease) !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] {
  background: transparent !important; border: 1px solid transparent !important;
  color: var(--text-secondary) !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {
  background: var(--hover) !important; color: var(--text-primary) !important;
  transform: none !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="secondary"] svg { color: var(--text-muted) !important; }
section[data-testid="stSidebar"] .stButton > button[kind="primary"] {
  background: var(--brand-bg) !important;
  border: 1px solid var(--brand-bd) !important;
  color: var(--text-primary) !important; font-weight: 650 !important;
  box-shadow: inset 3px 0 0 var(--brand) !important;
}
section[data-testid="stSidebar"] .stButton > button[kind="primary"] svg { color: var(--brand) !important; }
section[data-testid="stSidebar"] .stButton > button[kind="primary"]:hover { transform: none !important; opacity: 1 !important; }
section[data-testid="stSidebar"] .stRadio { display: none !important; }

.nh-brand { padding: 24px 18px 18px; border-bottom: 1px solid var(--border); margin-bottom: 8px; }
.nh-brand-row { display: flex; align-items: center; gap: 11px; }
.nh-brand-icon {
  width: 38px; height: 38px; border-radius: 10px; background: var(--grad-brand);
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  box-shadow: var(--shadow-sm); color: white;
}
.nh-brand-text-name { font-family: 'Space Grotesk', sans-serif; font-size: 1.2rem; font-weight: 700; letter-spacing: -0.03em; color: var(--text-primary) !important; }
.nh-brand-text-name .accent { background: var(--grad-brand); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.nh-brand-text-sub { font-size: 0.6rem; color: var(--text-muted) !important; letter-spacing: 0.14em; text-transform: uppercase; font-weight: 600; margin-top: 2px; }
.nh-nav-section-label { padding: 16px 20px 6px; font-size: 0.6rem; font-weight: 700; color: var(--text-faint) !important; letter-spacing: 0.16em; text-transform: uppercase; }

.nh-sidebar-footer { padding: 14px 18px; border-top: 1px solid var(--border); margin-top: 10px; }
.nh-sidebar-status-badge { display: flex; align-items: center; gap: 8px; padding: 9px 12px; background: var(--success-bg); border: 1px solid var(--success-bd); border-radius: var(--r-sm); margin-bottom: 10px; }
.nh-status-dot { width: 7px; height: 7px; border-radius: 50%; background: var(--success); flex-shrink: 0; animation: statusPulse 2.4s ease-in-out infinite; }
@keyframes statusPulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
.nh-status-label { font-size: 0.72rem; font-weight: 600; color: var(--success-ink) !important; }
.nh-sidebar-version { font-family: 'JetBrains Mono', monospace; font-size: 0.6rem; color: var(--text-faint) !important; letter-spacing: 0.04em; text-align: center; }

/* ═══ TYPOGRAPHY ═══ */
h1, h2, h3, h4, h5, h6 { font-family: 'Space Grotesk', sans-serif !important; color: var(--text-primary) !important; letter-spacing: -0.02em; line-height: 1.25; }
p, span, div, li, label { color: var(--text-secondary); }
strong, b { color: var(--text-primary); }
.nh-text { color: var(--text-secondary) !important; font-size: 0.9rem; line-height: 1.7; }
.nh-text strong { color: var(--text-primary) !important; }
a, a:visited { color: var(--brand-ink); text-decoration: none; }
a:hover { text-decoration: underline; }

/* ═══ PAGE HEADER ═══ */
.nh-page-header { margin-bottom: 2rem; padding-bottom: 1.4rem; border-bottom: 1px solid var(--border); }
.nh-page-badge {
  display: inline-flex; align-items: center; gap: 7px; padding: 4px 12px; border-radius: var(--r-full);
  background: var(--brand-bg); border: 1px solid var(--brand-bd);
  font-size: 0.62rem; font-weight: 700; color: var(--brand-ink) !important;
  letter-spacing: 0.14em; text-transform: uppercase; margin-bottom: 14px;
}
.nh-page-badge-dot { width: 5px; height: 5px; border-radius: 50%; background: var(--brand); }
.nh-page-title {
  font-family: 'Space Grotesk', sans-serif !important; font-size: 2.35rem !important; font-weight: 700 !important;
  color: var(--text-primary) !important; letter-spacing: -0.03em; line-height: 1.08; margin-bottom: 10px;
  animation: fadeUp 0.4s var(--ease) both;
}
.nh-page-title .grad { background: var(--grad-brand); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.nh-page-subtitle { font-size: 0.94rem; color: var(--text-secondary) !important; line-height: 1.7; max-width: 640px; animation: fadeUp 0.45s 0.05s var(--ease) both; }
@keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeDown { from { opacity: 0; transform: translateY(-6px); } to { opacity: 1; transform: translateY(0); } }

/* ═══ TOP BAR ═══ */
.nh-topbar {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 11px 18px; background: var(--topbar-bg); border: 1px solid var(--border);
  border-radius: var(--r-lg); margin-bottom: 24px; backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px); box-shadow: var(--shadow-sm);
}
.nh-topbar-left { display: flex; align-items: center; gap: 12px; }
.nh-topbar-breadcrumb { display: flex; align-items: center; gap: 8px; font-size: 0.82rem; font-weight: 500; color: var(--text-muted); }
.nh-topbar-breadcrumb .root { color: var(--text-secondary); font-weight: 600; }
.nh-topbar-breadcrumb .sep { opacity: 0.5; }
.nh-topbar-breadcrumb .current { color: var(--text-primary); font-weight: 700; font-family: 'Space Grotesk', sans-serif; }
.nh-topbar-center { flex: 1; max-width: 420px; margin: 0 16px; }
.nh-topbar-search { display: flex; align-items: center; gap: 10px; background: var(--input-bg); border: 1px solid var(--border); border-radius: var(--r-full); padding: 6px 15px; color: var(--text-muted); }
.nh-topbar-search input { background: transparent !important; border: none !important; color: var(--text-secondary) !important; font-size: 0.8rem !important; width: 100%; outline: none !important; box-shadow: none !important; }
.nh-topbar-right { display: flex; align-items: center; gap: 12px; }
.nh-topbar-status { display: inline-flex; align-items: center; gap: 8px; padding: 5px 12px; background: var(--success-bg); border: 1px solid var(--success-bd); border-radius: var(--r-full); font-size: 0.72rem; font-weight: 600; color: var(--success-ink); }
.nh-topbar-avatar { width: 32px; height: 32px; border-radius: 50%; background: var(--grad-brand); display: flex; align-items: center; justify-content: center; font-size: 0.75rem; font-weight: 700; color: white; box-shadow: var(--shadow-sm); }

.nh-breadcrumb { display: flex; align-items: center; gap: 8px; padding: 11px 16px; background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-md); margin-bottom: 22px; font-size: 0.8rem; color: var(--text-muted); width: fit-content; }

/* ═══ CARDS ═══ */
.nh-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg);
  padding: 22px; box-shadow: var(--shadow-sm);
  transition: border-color var(--t-mid) var(--ease), box-shadow var(--t-mid) var(--ease), transform var(--t-mid) var(--ease);
  position: relative;
}
.nh-card:hover { border-color: var(--border-strong); box-shadow: var(--shadow-md); transform: translateY(-1px); }
.nh-card-sm { padding: 15px; border-radius: var(--r-md); }

/* ═══ STAT CARDS ═══ */
.nh-stat {
  background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg);
  padding: 18px 20px; position: relative; overflow: hidden; box-shadow: var(--shadow-sm);
  transition: all var(--t-mid) var(--ease);
}
.nh-stat::after { content: ''; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; background: var(--brand); opacity: 0.9; border-radius: var(--r-lg) 0 0 var(--r-lg); }
.nh-stat.success::after { background: var(--success); }
.nh-stat.warn::after    { background: var(--warn); }
.nh-stat.danger::after  { background: var(--danger); }
.nh-stat.purple::after  { background: var(--brand-2); }
.nh-stat.cyan::after    { background: var(--accent); }
.nh-stat:hover { border-color: var(--border-strong); box-shadow: var(--shadow-md); transform: translateY(-2px); }
.nh-stat-icon { width: 34px; height: 34px; border-radius: var(--r-sm); display: flex; align-items: center; justify-content: center; margin-bottom: 13px; color: var(--brand); background: var(--brand-bg); }
.nh-stat-icon.success { color: var(--success); background: var(--success-bg); }
.nh-stat-icon.warn    { color: var(--warn); background: var(--warn-bg); }
.nh-stat-icon.danger  { color: var(--danger); background: var(--danger-bg); }
.nh-stat-icon.brand   { color: var(--brand); background: var(--brand-bg); }
.nh-stat-icon.purple  { color: var(--brand-2); background: var(--brand-bg); }
.nh-stat-icon.cyan    { color: var(--accent); background: var(--accent-bg); }
.nh-stat-value { font-family: 'Space Grotesk', sans-serif; font-size: 1.9rem; font-weight: 700; color: var(--text-primary) !important; letter-spacing: -0.03em; line-height: 1; font-variant-numeric: tabular-nums; }
.nh-stat-value.grad, .nh-stat-value.success, .nh-stat-value.warn, .nh-stat-value.danger { -webkit-text-fill-color: initial; background: none; }
.nh-stat-label { font-size: 0.68rem; font-weight: 700; color: var(--text-muted) !important; letter-spacing: 0.1em; text-transform: uppercase; margin-top: 6px; }

/* ═══ SECTION LABEL ═══ */
.nh-section-label { display: flex; align-items: center; gap: 8px; font-size: 0.68rem; font-weight: 700; color: var(--text-muted) !important; letter-spacing: 0.13em; text-transform: uppercase; margin-bottom: 12px; }
.nh-section-label .icon { color: var(--brand); display: inline-flex; }
.nh-section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }

/* ═══ SCORE RING ═══ */
.nh-score-ring-wrap { display: flex; flex-direction: column; align-items: center; padding: 16px 12px; }
.nh-score-ring { position: relative; width: 154px; height: 154px; margin-bottom: 14px; }
.nh-score-ring svg { width: 154px; height: 154px; transform: rotate(-90deg); }
.nh-score-ring .track { fill: none; stroke: var(--track); stroke-width: 10; }
.nh-score-ring .arc { fill: none; stroke-width: 10; stroke-linecap: round; transition: stroke-dashoffset 1.2s var(--ease); }
.nh-score-center { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.nh-score-num { font-family: 'Space Grotesk', sans-serif; font-size: 2.5rem; font-weight: 700; letter-spacing: -0.04em; line-height: 1; font-variant-numeric: tabular-nums; }
.nh-score-num.hire     { color: var(--success); }
.nh-score-num.consider { color: var(--warn); }
.nh-score-num.reject   { color: var(--danger); }
.nh-score-unit { font-size: 1rem; font-weight: 600; opacity: 0.6; color: var(--text-secondary) !important; }
.nh-score-ring-label { font-size: 0.58rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: var(--text-muted) !important; margin-bottom: 10px; }

/* ═══ BADGES ═══ */
.nh-badge { display: inline-flex; align-items: center; gap: 6px; padding: 5px 14px; border-radius: var(--r-full); font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; border: 1px solid; }
.nh-badge svg { width: 13px; height: 13px; }
.nh-badge-hire     { background: var(--success-bg); border-color: var(--success-bd); color: var(--success-ink) !important; }
.nh-badge-consider { background: var(--warn-bg); border-color: var(--warn-bd); color: var(--warn-ink) !important; }
.nh-badge-reject   { background: var(--danger-bg); border-color: var(--danger-bd); color: var(--danger-ink) !important; }

/* ═══ SKILL CHIPS ═══ */
.nh-chip { display: inline-flex; align-items: center; gap: 4px; padding: 4px 11px; border-radius: var(--r-full); font-size: 0.73rem; font-weight: 600; border: 1px solid; margin: 2px; transition: transform var(--t-fast); }
.nh-chip:hover { transform: translateY(-1px); }
.nh-chip-match    { background: var(--success-bg); border-color: var(--success-bd); color: var(--success-ink) !important; }
.nh-chip-missing  { background: var(--danger-bg); border-color: var(--danger-bd); color: var(--danger-ink) !important; }
.nh-chip-extra    { background: var(--brand-bg); border-color: var(--brand-bd); color: var(--brand-ink) !important; }
.nh-chip-critical { background: var(--warn-bg); border-color: var(--warn-bd); color: var(--warn-ink) !important; font-weight: 700; }

/* ═══ ALERTS ═══ */
.nh-alert { display: flex; align-items: flex-start; gap: 10px; padding: 11px 14px; border-radius: var(--r-md); border: 1px solid; font-size: 0.85rem; line-height: 1.6; margin: 6px 0; }
.nh-alert-icon { flex-shrink: 0; margin-top: 2px; display: inline-flex; }
.nh-alert-success { background: var(--success-bg); border-color: var(--success-bd); color: var(--success-ink) !important; }
.nh-alert-warning { background: var(--warn-bg); border-color: var(--warn-bd); color: var(--warn-ink) !important; }
.nh-alert-error   { background: var(--danger-bg); border-color: var(--danger-bd); color: var(--danger-ink) !important; }
.nh-alert-info    { background: var(--info-bg); border-color: var(--info-bd); color: var(--info-ink) !important; }
.nh-alert span:not(.nh-alert-icon) { color: inherit !important; }

/* ═══ AI INSIGHT PANEL ═══ */
.nh-insight { padding: 20px 22px; border-radius: var(--r-lg); border: 1px solid; position: relative; margin: 8px 0; }
.nh-insight-hire     { background: var(--success-bg); border-color: var(--success-bd); }
.nh-insight-consider { background: var(--warn-bg); border-color: var(--warn-bd); }
.nh-insight-reject   { background: var(--danger-bg); border-color: var(--danger-bd); }
.nh-insight-eyebrow { display: flex; align-items: center; font-size: 0.6rem; font-weight: 700; letter-spacing: 0.16em; text-transform: uppercase; margin-bottom: 8px; }
.nh-insight-hire .nh-insight-eyebrow { color: var(--success-ink) !important; }
.nh-insight-consider .nh-insight-eyebrow { color: var(--warn-ink) !important; }
.nh-insight-reject .nh-insight-eyebrow { color: var(--danger-ink) !important; }
.nh-insight-body { font-size: 0.92rem; line-height: 1.7; color: var(--text-primary) !important; }

/* ═══ FEATURE CARDS ═══ */
.nh-feature { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 22px; height: 100%; box-shadow: var(--shadow-sm); transition: all var(--t-mid) var(--ease); }
.nh-feature:hover { border-color: var(--border-strong); transform: translateY(-3px); box-shadow: var(--shadow-md); }
.nh-feature-icon { width: 42px; height: 42px; border-radius: var(--r-md); display: flex; align-items: center; justify-content: center; margin-bottom: 14px; }
.nh-feature-icon.blue   { color: var(--brand); background: var(--brand-bg); }
.nh-feature-icon.purple { color: var(--brand-2); background: var(--brand-bg); }
.nh-feature-icon.cyan   { color: var(--accent); background: var(--accent-bg); }
.nh-feature-icon.amber  { color: var(--warn); background: var(--warn-bg); }
.nh-feature-icon.violet { color: var(--brand-2); background: var(--brand-bg); }
.nh-feature-icon.rose   { color: var(--danger); background: var(--danger-bg); }
.nh-feature-title { font-family: 'Space Grotesk', sans-serif; font-size: 1rem; font-weight: 700; color: var(--text-primary) !important; margin-bottom: 8px; letter-spacing: -0.01em; }
.nh-feature-desc { font-size: 0.82rem; color: var(--text-secondary) !important; line-height: 1.65; }

/* ═══ PIPELINE ═══ */
.nh-pipeline { display: flex; align-items: flex-start; gap: 0; overflow-x: auto; padding: 20px 4px; }
.nh-pipeline-step { flex: 1; min-width: 110px; display: flex; flex-direction: column; align-items: center; text-align: center; position: relative; padding: 0 10px; }
.nh-pipeline-step::after { content: ''; position: absolute; right: -1px; top: 24px; width: 20px; height: 2px; background: var(--border); }
.nh-pipeline-step:last-child::after { display: none; }
.nh-pipeline-icon { width: 50px; height: 50px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 1px solid var(--border); background: var(--surface-2); margin-bottom: 10px; color: var(--brand); transition: all var(--t-mid); }
.nh-pipeline-step:hover .nh-pipeline-icon { border-color: var(--brand-bd); transform: translateY(-2px); box-shadow: var(--shadow-sm); }
.nh-pipeline-label { font-size: 0.7rem; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-primary) !important; margin-bottom: 3px; }
.nh-pipeline-desc { font-size: 0.66rem; color: var(--text-muted) !important; line-height: 1.5; }

/* ═══ ARCHITECTURE ROW ═══ */
.nh-arch-row { display: flex; align-items: center; gap: 14px; padding: 11px 14px; border-radius: var(--r-md); margin-bottom: 5px; background: var(--surface); border: 1px solid var(--border); transition: all var(--t-fast); }
.nh-arch-row:hover { border-color: var(--border-strong); background: var(--surface-2); }
.nh-arch-layer { font-size: 0.64rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: var(--brand-ink) !important; min-width: 88px; }
.nh-arch-tech  { font-family: 'JetBrains Mono', monospace; font-size: 0.77rem; color: var(--text-code) !important; }
.nh-arch-desc  { font-size: 0.75rem; color: var(--text-muted) !important; margin-left: auto; }

/* ═══ RANKING CARDS ═══ */
.nh-rank-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 18px 20px; margin-bottom: 10px; box-shadow: var(--shadow-sm); transition: all var(--t-mid) var(--ease); position: relative; }
.nh-rank-card:hover { border-color: var(--border-strong); transform: translateY(-1px); box-shadow: var(--shadow-md); }
.nh-rank-card.rank-1 { border-color: var(--warn-bd); box-shadow: inset 3px 0 0 var(--warn), var(--shadow-sm); }
.nh-rank-card.rank-2 { box-shadow: inset 3px 0 0 #94A3B8, var(--shadow-sm); }
.nh-rank-card.rank-3 { box-shadow: inset 3px 0 0 #B45309, var(--shadow-sm); }
.nh-rank-num { font-family: 'Space Grotesk', sans-serif; font-size: 1.9rem; font-weight: 700; color: var(--text-faint) !important; letter-spacing: -0.04em; line-height: 1; min-width: 46px; font-variant-numeric: tabular-nums; }
.nh-rank-card.rank-1 .nh-rank-num { color: var(--warn) !important; }
.nh-rank-card.rank-2 .nh-rank-num { color: #94A3B8 !important; }
.nh-rank-card.rank-3 .nh-rank-num { color: #B45309 !important; }
.nh-rank-name { font-family: 'Space Grotesk', sans-serif; font-size: 1.05rem; font-weight: 700; color: var(--text-primary) !important; letter-spacing: -0.02em; }
.nh-rank-bar { height: 6px; border-radius: var(--r-full); background: var(--track); overflow: hidden; margin: 7px 0; }
.nh-rank-fill { height: 100%; border-radius: var(--r-full); transition: width 0.9s var(--ease); }
.nh-rank-fill-hire     { background: var(--success); }
.nh-rank-fill-consider { background: var(--warn); }
.nh-rank-fill-reject   { background: var(--danger); }

/* ═══ HERO ═══ */
.nh-hero { padding: 46px 40px; text-align: center; border-radius: var(--r-2xl); background: var(--surface); border: 1px solid var(--border); position: relative; overflow: hidden; margin-bottom: 2.2rem; box-shadow: var(--shadow-sm); }
.nh-hero::before { content: ''; position: absolute; inset: 0; background: var(--app-wash); pointer-events: none; }
.nh-hero-eyebrow { display: inline-flex; align-items: center; gap: 8px; background: var(--brand-bg); border: 1px solid var(--brand-bd); border-radius: var(--r-full); padding: 5px 14px; font-size: 0.64rem; font-weight: 700; color: var(--brand-ink) !important; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 20px; position: relative; }
.nh-hero-title { font-family: 'Space Grotesk', sans-serif !important; font-size: 3.2rem !important; font-weight: 700 !important; line-height: 1.05 !important; color: var(--text-primary) !important; letter-spacing: -0.04em; margin-bottom: 16px; position: relative; }
.nh-hero-title .glow { background: var(--grad-brand); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.nh-hero-sub { font-size: 1.02rem; color: var(--text-secondary) !important; line-height: 1.75; max-width: 560px; margin: 0 auto; position: relative; }

/* ═══ SUMMARY ROW ═══ */
.nh-summary-row { display: flex; gap: 0; background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-md); overflow: hidden; margin: 14px 0; }
.nh-summary-item { flex: 1; text-align: center; padding: 14px 10px; border-right: 1px solid var(--border); }
.nh-summary-item:last-child { border-right: none; }
.nh-summary-val { font-family: 'Space Grotesk', sans-serif; font-size: 1.5rem; font-weight: 700; color: var(--text-primary) !important; letter-spacing: -0.03em; font-variant-numeric: tabular-nums; }
.nh-summary-label { font-size: 0.6rem; font-weight: 700; color: var(--text-muted) !important; text-transform: uppercase; letter-spacing: 0.1em; margin-top: 4px; }

/* ═══ MODEL CARDS ═══ */
.nh-model-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--r-lg); padding: 20px 16px; text-align: center; box-shadow: var(--shadow-sm); transition: all var(--t-mid) var(--ease); }
.nh-model-card:hover { border-color: var(--border-strong); transform: translateY(-2px); box-shadow: var(--shadow-md); }

/* ═══ RESULT REVEAL ═══ */
.nh-result { animation: fadeUp 0.4s var(--ease) both; }

/* ═══ EMPTY STATE ═══ */
.nh-empty { text-align: center; padding: 48px 32px; border: 1px dashed var(--border-strong); border-radius: var(--r-xl); background: var(--surface); }
.nh-empty-icon { color: var(--text-faint); margin-bottom: 14px; display: flex; justify-content: center; }
.nh-empty-title { font-family: 'Space Grotesk', sans-serif; font-size: 1.1rem; font-weight: 600; color: var(--text-primary) !important; margin-bottom: 8px; }
.nh-empty-desc { font-size: 0.84rem; color: var(--text-muted) !important; line-height: 1.65; max-width: 420px; margin: 0 auto; }

/* ═══ FOOTER ═══ */
.nh-footer { text-align: center; padding: 22px; color: var(--text-faint) !important; font-size: 0.68rem; letter-spacing: 0.04em; border-top: 1px solid var(--border); margin-top: 48px; }

/* ═══════════ STREAMLIT WIDGET OVERRIDES ═══════════ */
.stTextArea textarea, .stTextInput input, .stNumberInput input,
.stDateInput input {
  background: var(--input-bg) !important; border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important; color: var(--text-primary) !important;
  font-family: 'Inter', sans-serif !important; font-size: 0.875rem !important;
  transition: border-color var(--t-fast), box-shadow var(--t-fast) !important;
}
.stTextArea textarea { line-height: 1.7 !important; padding: 12px 14px !important; }
.stTextInput input, .stNumberInput input { padding: 10px 14px !important; }
.stTextArea textarea:focus, .stTextInput input:focus, .stNumberInput input:focus {
  border-color: var(--border-focus) !important;
  box-shadow: 0 0 0 3px var(--brand-bg) !important; outline: none !important;
}
.stTextArea textarea::placeholder, .stTextInput input::placeholder { color: var(--text-faint) !important; }

.stSelectbox > div > div, .stMultiSelect > div > div, [data-baseweb="select"] > div {
  background: var(--input-bg) !important; border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important; color: var(--text-primary) !important;
}
.stSelectbox > div > div:focus-within, .stMultiSelect > div > div:focus-within { border-color: var(--border-focus) !important; box-shadow: 0 0 0 3px var(--brand-bg) !important; }
[data-baseweb="select"] * { color: var(--text-primary) !important; }
[data-baseweb="popover"] [data-baseweb="menu"], [data-baseweb="popover"] ul { background: var(--surface-2) !important; border: 1px solid var(--border-strong) !important; border-radius: var(--r-md) !important; box-shadow: var(--shadow-lg) !important; }
[data-baseweb="option"] { color: var(--text-secondary) !important; }
[data-baseweb="option"]:hover { background: var(--hover) !important; color: var(--text-primary) !important; }
[data-baseweb="option"][aria-selected="true"] { background: var(--brand-bg) !important; color: var(--text-primary) !important; }

label[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] p {
  color: var(--text-secondary) !important; font-size: 0.78rem !important; font-weight: 600 !important; letter-spacing: 0.01em !important;
}

/* Buttons — primary brand */
.stButton > button {
  background: var(--grad-brand) !important; color: #fff !important; border: none !important;
  border-radius: var(--r-md) !important; font-weight: 650 !important; font-size: 0.88rem !important;
  padding: 10px 24px !important; box-shadow: var(--shadow-sm) !important;
  transition: transform var(--t-fast) var(--ease), box-shadow var(--t-fast) var(--ease), filter var(--t-fast) !important;
}
.stButton > button:hover { transform: translateY(-1px) !important; box-shadow: var(--shadow-md) !important; filter: brightness(1.05) !important; }
.stButton > button:active { transform: translateY(0) !important; }
.stButton > button:focus-visible { outline: 2px solid var(--brand) !important; outline-offset: 2px !important; }

.stDownloadButton > button { background: var(--surface) !important; color: var(--brand-ink) !important; border: 1px solid var(--brand-bd) !important; border-radius: var(--r-md) !important; font-weight: 650 !important; font-size: 0.86rem !important; box-shadow: var(--shadow-sm) !important; }
.stDownloadButton > button:hover { background: var(--brand-bg) !important; transform: translateY(-1px) !important; }
.stDownloadButton > button svg { color: var(--brand) !important; }

.stFormSubmitButton > button { background: var(--grad-brand) !important; color: #fff !important; border: none !important; border-radius: var(--r-md) !important; font-weight: 650 !important; }

[data-testid="stMetric"], [data-testid="metric-container"] { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; padding: 16px 18px !important; box-shadow: var(--shadow-sm) !important; }
[data-testid="stMetricLabel"], [data-testid="stMetricLabel"] p { color: var(--text-muted) !important; font-size: 0.66rem !important; font-weight: 700 !important; text-transform: uppercase !important; letter-spacing: 0.1em !important; }
[data-testid="stMetricValue"] { color: var(--text-primary) !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 700 !important; letter-spacing: -0.02em !important; font-variant-numeric: tabular-nums; }
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }

.stProgress > div > div > div { background: var(--grad-brand) !important; border-radius: var(--r-full) !important; }
.stProgress > div > div { background: var(--track) !important; border-radius: var(--r-full) !important; height: 6px !important; }

.stTabs [data-baseweb="tab-list"] { background: var(--surface-2) !important; border-radius: var(--r-md) !important; padding: 4px !important; gap: 2px !important; border: 1px solid var(--border) !important; }
.stTabs [data-baseweb="tab"] { border-radius: var(--r-sm) !important; color: var(--text-secondary) !important; font-weight: 600 !important; font-size: 0.83rem !important; padding: 7px 16px !important; transition: all var(--t-fast) !important; }
.stTabs [data-baseweb="tab"]:hover { color: var(--text-primary) !important; background: var(--hover) !important; }
.stTabs [aria-selected="true"] { background: var(--surface) !important; color: var(--brand-ink) !important; box-shadow: var(--shadow-sm) !important; }
.stTabs [data-baseweb="tab-highlight"], .stTabs [data-baseweb="tab-border"] { display: none !important; }

[data-testid="stExpander"] details { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; overflow: hidden; }
[data-testid="stExpander"] summary { color: var(--text-primary) !important; font-weight: 600 !important; font-size: 0.875rem !important; padding: 12px 14px !important; }
[data-testid="stExpander"] summary:hover { background: var(--hover) !important; }
.streamlit-expanderHeader { background: var(--surface) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; color: var(--text-primary) !important; font-weight: 600 !important; }
.streamlit-expanderContent { border: 1px solid var(--border) !important; border-top: none !important; background: var(--surface) !important; }

[data-testid="stFileUploadDropzone"], .stFileUploader > div, .stFileUploader section {
  background: var(--surface-2) !important; border: 2px dashed var(--border-strong) !important;
  border-radius: var(--r-lg) !important; transition: all var(--t-mid) !important;
}
[data-testid="stFileUploadDropzone"]:hover, .stFileUploader section:hover { border-color: var(--brand) !important; background: var(--brand-bg) !important; }
[data-testid="stFileUploadDropzone"] *, .stFileUploader section * { color: var(--text-secondary) !important; }
.stFileUploader button { background: var(--surface) !important; color: var(--brand-ink) !important; border: 1px solid var(--brand-bd) !important; }

.stRadio div[role="radiogroup"] { gap: 6px !important; }
.stRadio div[role="radiogroup"] > label {
  display: flex !important; align-items: center !important; gap: 8px !important; padding: 8px 13px !important;
  border: 1px solid var(--border) !important; border-radius: var(--r-md) !important;
  color: var(--text-secondary) !important; font-size: 0.85rem !important; cursor: pointer !important;
  transition: all var(--t-fast) !important; background: var(--surface) !important;
}
.stRadio div[role="radiogroup"] > label:hover { border-color: var(--border-strong) !important; background: var(--surface-2) !important; }

.stCheckbox label { color: var(--text-secondary) !important; font-size: 0.875rem !important; cursor: pointer !important; }
.stCheckbox label:hover { color: var(--text-primary) !important; }

.stSlider [data-baseweb="slider"] div[role="slider"] { background: var(--brand) !important; box-shadow: var(--shadow-sm) !important; }
.stSlider [data-baseweb="slider"] > div > div { background: var(--brand) !important; }
.stSlider [data-testid="stTickBar"], .stSlider [data-testid="stThumbValue"] { color: var(--text-muted) !important; }

/* Native dataframe */
.stDataFrame, [data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; overflow: hidden !important; }

/* Custom premium table */
.nh-premium-table-container { width: 100%; overflow-x: auto; margin: 10px 0 20px; border-radius: var(--r-md); border: 1px solid var(--border); background: var(--surface); box-shadow: var(--shadow-sm); }
.nh-premium-table { width: 100%; border-collapse: collapse; text-align: left; font-family: 'Inter', sans-serif; }
.nh-premium-table th { padding: 13px 16px; background: var(--surface-2); color: var(--text-muted); font-size: 0.68rem; font-weight: 700; letter-spacing: 0.07em; text-transform: uppercase; border-bottom: 1px solid var(--border); white-space: nowrap; }
.nh-premium-table td { padding: 14px 16px; color: var(--text-secondary); font-size: 0.85rem; border-bottom: 1px solid var(--border); vertical-align: middle; }
.nh-premium-table tr:last-child td { border-bottom: none; }
.nh-premium-table tbody tr { transition: background-color var(--t-fast); }
.nh-premium-table tbody tr:hover { background: var(--hover); }
.nh-premium-table .avatar-cell { display: flex; align-items: center; gap: 12px; }
.nh-premium-table .avatar { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.75rem; flex-shrink: 0; }
.nh-premium-table .primary-text { font-weight: 600; color: var(--text-primary); }
.nh-premium-table .secondary-text { font-size: 0.78rem; color: var(--text-muted); }

.nh-badge-inline { display: inline-flex; align-items: center; gap: 5px; padding: 4px 10px; border-radius: var(--r-full); font-size: 0.68rem; font-weight: 700; letter-spacing: 0.04em; border: 1px solid; }
.nh-badge-inline svg { width: 11px; height: 11px; }
.nh-badge-inline.hire     { background: var(--success-bg); color: var(--success-ink); border-color: var(--success-bd); }
.nh-badge-inline.consider { background: var(--warn-bg); color: var(--warn-ink); border-color: var(--warn-bd); }
.nh-badge-inline.reject   { background: var(--danger-bg); color: var(--danger-ink); border-color: var(--danger-bd); }
.nh-badge-inline.active   { background: var(--success-bg); color: var(--success-ink); border-color: var(--success-bd); }
.nh-badge-inline.closed   { background: var(--danger-bg); color: var(--danger-ink); border-color: var(--danger-bd); }
.nh-badge-inline.draft    { background: var(--surface-3); color: var(--text-muted); border-color: var(--border-strong); }

.nh-progress-container { display: flex; align-items: center; gap: 10px; }
.nh-progress-mini { width: 100%; max-width: 120px; height: 7px; background: var(--track); border-radius: var(--r-full); overflow: hidden; }
.nh-progress-mini-bar { height: 100%; border-radius: var(--r-full); }
.nh-progress-mini-text { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-primary); font-weight: 600; min-width: 40px; font-variant-numeric: tabular-nums; }

.stAlert { border-radius: var(--r-md) !important; border: 1px solid var(--border) !important; border-left-width: 3px !important; }
.stSpinner > div { border-top-color: var(--brand) !important; }

code { font-family: 'JetBrains Mono', monospace !important; background: var(--code-bg) !important; border: 1px solid var(--border) !important; border-radius: var(--r-xs) !important; padding: 1px 6px !important; font-size: 0.82em !important; color: var(--text-code) !important; }
pre { background: var(--surface-2) !important; border: 1px solid var(--border) !important; border-radius: var(--r-md) !important; padding: 14px !important; }
pre code { background: transparent !important; border: none !important; padding: 0 !important; }

hr { border: none !important; height: 1px !important; background: var(--border) !important; margin: 20px 0 !important; }

::-webkit-scrollbar { width: 10px; height: 10px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--scrollbar); border-radius: var(--r-full); border: 2px solid transparent; background-clip: padding-box; }
::-webkit-scrollbar-thumb:hover { background: var(--scrollbar-hover); border: 2px solid transparent; background-clip: padding-box; }

.stToast, [data-testid="stToast"] { background: var(--surface-2) !important; border: 1px solid var(--border-strong) !important; border-radius: var(--r-md) !important; color: var(--text-primary) !important; box-shadow: var(--shadow-lg) !important; }

@media (max-width: 900px) {
  .main .block-container { padding: 1rem 1rem 3rem !important; }
  .nh-page-title { font-size: 1.8rem !important; }
  .nh-hero-title { font-size: 2.2rem !important; }
  .nh-topbar-center { display: none; }
}
@media (min-width: 1800px) { .main .block-container { max-width: 1560px !important; } }
"""


def build_css(theme: str = "dark") -> str:
    """Return the full <style> block for the requested theme ('dark' | 'light')."""
    theme = "light" if theme == "light" else "dark"
    return f"<style>\n{_root_block(theme)}{_SHARED_ROOT}{_BODY_CSS}\n</style>"


def chart_palette(theme: str = "dark") -> dict:
    """Colours for matplotlib charts so they read correctly in both themes."""
    if theme == "light":
        return {
            "bg": "#FFFFFF", "grid": "#E2E8F0", "axis": "#CBD5E1",
            "text": "#0F172A", "muted": "#64748B", "label": "#475569",
            "brand": "#6366F1", "brand2": "#7C3AED", "accent": "#0891B2",
            "success": "#059669", "warn": "#D97706", "danger": "#E11D48",
        }
    return {
        "bg": "#111726", "grid": "#232B3D", "axis": "#334155",
        "text": "#F1F5F9", "muted": "#64748B", "label": "#94A3B8",
        "brand": "#6366F1", "brand2": "#8B5CF6", "accent": "#06B6D4",
        "success": "#10B981", "warn": "#F59E0B", "danger": "#F43F5E",
    }


# Back-compat exports (default dark theme).
PREMIUM_CSS = build_css("dark")


def inject_css(theme: str = "dark"):
    """Inject the design-system CSS into the Streamlit app."""
    import streamlit as st
    st.markdown(build_css(theme), unsafe_allow_html=True)
