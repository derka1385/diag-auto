import type { Config } from "tailwindcss";
export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#0b1017",   // fond application (ardoise très sombre)
        surface: "#131c28",  // cartes / panneaux
        panel: "#1b2735",    // encarts, remplissages secondaires
        line: "#2c3a4b",     // bordures marquées (feel outil)
        primary: "#f5a524",  // accent ambre (scanner atelier)
        warning: "#f59e0b",
        danger: "#ef4444",
        success: "#22c55e",
        info: "#38bdf8",
        muted: "#8a9bb0",
      },
      fontFamily: {
        mono: ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      boxShadow: {
        panel: "0 10px 30px rgba(0,0,0,.35)",
        inset: "inset 0 1px 0 rgba(255,255,255,.04)",
      },
    },
  },
  plugins: [],
} satisfies Config;
