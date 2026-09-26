/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "rgb(var(--color-bg) / <alpha-value>)",
        surface: "rgb(var(--color-surface) / <alpha-value>)",
        border: "rgb(var(--color-border) / <alpha-value>)",
        ink: "rgb(var(--color-ink) / <alpha-value>)",
        muted: "rgb(var(--color-muted) / <alpha-value>)",
        accent: "rgb(var(--color-accent) / <alpha-value>)",
        accentSoft: "rgb(var(--color-accent-soft) / <alpha-value>)",
        secondary: "rgb(var(--color-secondary) / <alpha-value>)",
        added: "rgb(var(--color-added) / <alpha-value>)",
        removed: "rgb(var(--color-removed) / <alpha-value>)",
        warning: "rgb(var(--color-warning) / <alpha-value>)",
        info: "rgb(var(--color-info) / <alpha-value>)",
      },
      fontFamily: {
        sans: ["Manrope", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        soft: "0 18px 45px -28px rgb(18 48 73 / 0.42)",
        lift: "0 14px 30px -20px rgb(18 48 73 / 0.38)",
      },
      borderRadius: {
        DEFAULT: "0.65rem",
        md: "0.8rem",
      },
    },
  },
  plugins: [],
}

