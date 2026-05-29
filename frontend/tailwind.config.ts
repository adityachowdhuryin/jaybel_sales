import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{js,ts,jsx,tsx}", "./components/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        brand: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          200: "#bae6fd",
          300: "#7dd3fc",
          400: "#38bdf8",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
        },
        success: {
          100: "#dcfce7",
          700: "#15803d",
        },
        warning: {
          100: "#fef3c7",
          700: "#b45309",
        },
        danger: {
          100: "#fee2e2",
          700: "#b91c1c",
        },
        insight: {
          100: "#ede9fe",
          700: "#6d28d9",
        },
      },
      boxShadow: {
        panel: "0 10px 30px rgba(15, 23, 42, 0.08), 0 2px 10px rgba(15, 23, 42, 0.05)",
      },
    },
  },
  plugins: [],
};
export default config;
