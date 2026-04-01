/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#1677FF",
          dark: "#0958D9",
          light: "#4096FF",
        },
        surface: {
          DEFAULT: "#FFFFFF",
          secondary: "#FAFAFA",
          background: "#F5F7FA",
        },
        content: {
          primary: "#1A1A2E",
          secondary: "#595959",
          muted: "#8C8C8C",
        },
        stock: {
          up: "#CF1322",
          down: "#3F8600",
          warn: "#FAAD14",
          info: "#1677FF",
        },
      },
      fontFamily: {
        sans: ["PingFang SC", "Inter", "system-ui", "sans-serif"],
        mono: ["SF Mono", "Menlo", "Monaco", "monospace"],
      },
    },
  },
  plugins: [
    require("tailwindcss-animate"),
  ],
}
