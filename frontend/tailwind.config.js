/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F9F9F7",
        surface: "#FFFFFF",
        border: "#E4E4E1",
        ink: "#1A1D23",
        muted: "#6B7280",
        accent: "#0F6E64",
        accentSoft: "#E4F2F0",
        added: "#1E8E3E",
        removed: "#C5221F",
      },
      fontFamily: {
        sans: ["IBM Plex Sans", "system-ui", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
    },
  },
  plugins: [],
}

