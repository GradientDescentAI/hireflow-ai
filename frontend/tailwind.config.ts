import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ── Brand ──────────────────────────────────────
        primary: "#003fb1",
        "primary-container": "#1a56db",
        "inverse-primary": "#b5c4ff",
        "primary-fixed": "#dbe1ff",
        "primary-fixed-dim": "#b5c4ff",
        "on-primary": "#ffffff",
        "on-primary-fixed": "#00174d",
        "on-primary-fixed-variant": "#003dab",
        "on-primary-container": "#d4dcff",

        // ── Secondary / AI accent ───────────────────────
        secondary: "#6f30dc",
        "secondary-container": "#894ff7",
        "secondary-fixed": "#eaddff",
        "secondary-fixed-dim": "#d2bcff",
        "on-secondary": "#ffffff",
        "on-secondary-fixed": "#25005a",
        "on-secondary-fixed-variant": "#5900c7",
        "on-secondary-container": "#fffbff",
        "accent-ai": "#6c2bd9",

        // ── Tertiary ────────────────────────────────────
        tertiary: "#852b00",
        "tertiary-container": "#ad3b00",
        "tertiary-fixed": "#ffdbcf",
        "tertiary-fixed-dim": "#ffb59a",
        "on-tertiary": "#ffffff",
        "on-tertiary-fixed": "#380d00",
        "on-tertiary-fixed-variant": "#802a00",
        "on-tertiary-container": "#ffd4c5",

        // ── Semantic ─────────────────────────────────────
        success: "#057a55",
        warning: "#c27803",
        danger: "#c81e1e",
        error: "#ba1a1a",
        "error-container": "#ffdad6",
        "on-error": "#ffffff",
        "on-error-container": "#93000a",

        // ── Surface / Background ──────────────────────────
        background: "#faf8ff",
        "on-background": "#191b23",
        surface: "#faf8ff",
        "surface-dim": "#d9d9e4",
        "surface-bright": "#faf8ff",
        "surface-container-lowest": "#ffffff",
        "surface-container-low": "#f3f3fe",
        "surface-container": "#ededf8",
        "surface-container-high": "#e7e7f3",
        "surface-container-highest": "#e2e1ed",
        "surface-variant": "#e2e1ed",
        "surface-tint": "#1353d8",
        "on-surface": "#191b23",
        "on-surface-variant": "#434654",
        "inverse-surface": "#2e3039",
        "inverse-on-surface": "#f0f0fb",

        // ── Outline ───────────────────────────────────────
        outline: "#737686",
        "outline-variant": "#c3c5d7",

        // ── Neutral ───────────────────────────────────────
        "neutral-50": "#f9fafb",
        "neutral-200": "#e5e7eb",
        "neutral-700": "#374151",
        "neutral-900": "#111928",
      },
      borderRadius: {
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px",
      },
      spacing: {
        "sidebar-width": "240px",
        "sidebar-collapsed": "64px",
        "container-padding": "1.5rem",
        "card-padding": "1.5rem",
        "max-content-width": "80rem",
        gutter: "1rem",
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
      fontSize: {
        "headline-lg": ["1.5rem", { fontWeight: "600", lineHeight: "2rem" }],
        "headline-md": ["1.25rem", { fontWeight: "600", lineHeight: "1.75rem" }],
        "headline-sm": ["1rem", { fontWeight: "600", lineHeight: "1.5rem" }],
        "body-md": ["0.875rem", { fontWeight: "400", lineHeight: "1.25rem" }],
        "body-sm": ["0.875rem", { fontWeight: "400", lineHeight: "1.25rem" }],
        "label-md": ["0.875rem", { fontWeight: "500", lineHeight: "1.25rem" }],
        "label-xs": ["0.75rem", { fontWeight: "500", lineHeight: "1rem" }],
      },
    },
  },
  plugins: [],
};

export default config;
