import type { Config } from "tailwindcss";

// Brand-green light design system. Hex literals (not CSS vars) so opacity modifiers like
// `bg-status-ok/10` work. Keep the CSS variables in globals.css in sync for inline/recharts use.
const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: { DEFAULT: "#00915a", deep: "#00673e", accent: "#76b82a" },
        ink: { DEFAULT: "#1f2a24", secondary: "#5a6b62" },
        surface: { DEFAULT: "#ffffff", 2: "#f4f6f5", 3: "#ece9e0" },
        default: "#dfe4e1",
        hover: "#eef1ef",
        status: {
          ok: "#00915a",
          partial: "#e8a33d",
          blocked: "#c0392b",
          neutral: "#5a6b62",
          info: "#2f6f8f",
        },
      },
      borderColor: {
        DEFAULT: "#dfe4e1",
      },
    },
  },
  plugins: [],
};
export default config;
