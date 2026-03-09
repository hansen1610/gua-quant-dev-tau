/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#040405",
        panel: "#0b0c10",
        primary: "#f8fafc",
        success: "#00ff9d",
        danger: "#ff3b57",
        warning: "#ffb800",
        border: "#1a1d23",
        textMain: "#f1f5f9",
        textMuted: "#64748b"
      },
      fontFamily: {
        sans: ['Geist', 'sans-serif'],
        mono: ['"Geist Mono"', 'monospace'],
      },
      boxShadow: {
        none: 'none',
      }
    },
  },
  plugins: [],
};

