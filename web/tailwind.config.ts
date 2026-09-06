import type { Config } from "tailwindcss";

/**
 * NeuralHire — "Precision Intelligence" design tokens.
 *
 * Theme-varying tokens (surfaces, borders, text, status-soft backgrounds) are
 * driven by CSS variables defined in app/globals.css, so light/dark are two
 * first-class themes rather than an inverted palette. Brand hues (accent violet,
 * cyan, magenta) stay vivid and constant across both themes.
 *
 * Variables hold space-separated RGB channels so Tailwind's `/<alpha-value>`
 * opacity modifiers keep working, e.g. `bg-surface/60`, `border-subtle`.
 */
const v = (name: string) => `rgb(var(${name}) / <alpha-value>)`;

const config: Config = {
  darkMode: ["class", '[data-theme="dark"]'],
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Theme-varying surfaces ──────────────────────────────────
        canvas: v("--bg-canvas"),
        surface: v("--bg-surface"),
        "surface-raised": v("--bg-surface-raised"),
        "surface-overlay": v("--bg-surface-overlay"),

        // ── Borders ────────────────────────────────────────────────
        subtle: v("--border-subtle"),
        line: v("--border-default"),
        strong: v("--border-strong"),

        // ── Text ───────────────────────────────────────────────────
        ink: {
          DEFAULT: v("--text-primary"),
          secondary: v("--text-secondary"),
          muted: v("--text-muted"),
          inverse: v("--text-inverse"),
        },

        // ── Accent (violet/indigo) — constant across themes ─────────
        accent: {
          50: "#f3f1ff",
          100: "#e7e2ff",
          200: "#cec4ff",
          300: "#ac9cff",
          400: "#8f78ff",
          500: "#7c5cff",
          600: "#6a3ff2",
          700: "#5a2fd6",
          800: "#4826a8",
          900: "#382083",
          DEFAULT: "#7c5cff",
        },
        // ── Secondary hue (cyan) — for gradients / score reveal ─────
        cyan: {
          400: "#3ee6ff",
          500: "#22cfee",
          600: "#12a7c9",
        },
        // ── Tertiary hue (magenta) — hero CTA + reveal gradient ─────
        magenta: {
          400: "#ff7ad6",
          500: "#f65cc6",
          600: "#d63fa8",
        },

        // ── Status — saturated badge + theme-aware soft bg ──────────
        success: {
          DEFAULT: "#2fd39a",
          fg: v("--success-fg"),
          soft: v("--success-soft"),
          glow: "#2fd39a",
        },
        warning: {
          DEFAULT: "#f5b445",
          fg: v("--warning-fg"),
          soft: v("--warning-soft"),
          glow: "#f5b445",
        },
        danger: {
          // warmed / slightly desaturated — not stock bootstrap red
          DEFAULT: "#ec6a63",
          fg: v("--danger-fg"),
          soft: v("--danger-soft"),
          glow: "#ec6a63",
        },
      },

      borderRadius: {
        sm: "8px",
        DEFAULT: "12px",
        md: "12px",
        lg: "16px",
        xl: "24px",
        "2xl": "32px",
      },

      spacing: {
        // 18px step for 4.5-sized icons; the rest of the 8px rhythm uses
        // Tailwind's default scale (2=8px, 4=16px, 6=24px, 8=32px…).
        4.5: "18px",
      },

      fontFamily: {
        display: ["var(--font-display)", "system-ui", "sans-serif"],
        sans: ["var(--font-body)", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "monospace"],
      },

      fontSize: {
        display: ["clamp(2.75rem, 5vw, 4.5rem)", { lineHeight: "1.02", letterSpacing: "-0.03em" }],
        h1: ["2.25rem", { lineHeight: "1.1", letterSpacing: "-0.02em" }],
        h2: ["1.75rem", { lineHeight: "1.15", letterSpacing: "-0.02em" }],
        h3: ["1.375rem", { lineHeight: "1.25", letterSpacing: "-0.01em" }],
        h4: ["1.125rem", { lineHeight: "1.3", letterSpacing: "-0.01em" }],
        "body-lg": ["1.0625rem", { lineHeight: "1.6" }],
        body: ["0.9375rem", { lineHeight: "1.6" }],
        caption: ["0.8125rem", { lineHeight: "1.45", letterSpacing: "0.01em" }],
        micro: ["0.6875rem", { lineHeight: "1.4", letterSpacing: "0.06em" }],
      },

      boxShadow: {
        // layered elevation recipes (ambient + direct), never a flat drop
        e1: "var(--shadow-e1)",
        e2: "var(--shadow-e2)",
        e3: "var(--shadow-e3)",
        e4: "var(--shadow-e4)",
        e5: "var(--shadow-e5)",
        "glow-accent": "0 0 0 1px rgb(124 92 255 / 0.35), 0 8px 40px -8px rgb(124 92 255 / 0.55)",
        "glow-success": "0 0 48px -8px rgb(47 211 154 / 0.55)",
        "glow-warning": "0 0 48px -8px rgb(245 180 69 / 0.55)",
        "glow-danger": "0 0 48px -8px rgb(236 106 99 / 0.55)",
      },

      backdropBlur: {
        xs: "2px",
        glass: "18px",
      },

      transitionTimingFunction: {
        "out-expo": "cubic-bezier(0.16, 1, 0.3, 1)",
        "out-back": "cubic-bezier(0.34, 1.56, 0.64, 1)",
        spring: "cubic-bezier(0.22, 1, 0.36, 1)",
      },

      transitionDuration: {
        fast: "150ms",
        DEFAULT: "250ms",
        slow: "400ms",
      },

      keyframes: {
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
        "pulse-glow": {
          "0%, 100%": { opacity: "0.6" },
          "50%": { opacity: "1" },
        },
        "border-pulse": {
          "0%, 100%": { borderColor: "rgb(124 92 255 / 0.3)" },
          "50%": { borderColor: "rgb(124 92 255 / 0.9)" },
        },
        drift: {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%": { transform: "translateY(-6px)" },
        },
      },
      animation: {
        shimmer: "shimmer 1.6s infinite",
        "pulse-glow": "pulse-glow 2.4s ease-in-out infinite",
        "border-pulse": "border-pulse 1.4s ease-in-out infinite",
        drift: "drift 6s ease-in-out infinite",
      },

      maxWidth: {
        container: "1360px",
      },
    },
  },
  plugins: [],
};

export default config;
