/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Outfit', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        // Intermediate shades the components already reference. Without these
        // the classes (e.g. border-slate-850, text-slate-350) compile to nothing
        // and the intended borders/text simply never render.
        slate: {
          250: '#cdd5e0',
          350: '#aeb9ca',
          450: '#7c8aa1',
          850: '#172033',
        },
        amber: {
          450: '#f7a813',
        },
        emerald: {
          450: '#1fc28a',
        },
      },
      boxShadow: {
        glow: '0 0 24px rgba(99, 102, 241, 0.25)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 12s linear infinite',
        'fade-in': 'fadeIn 0.4s ease-out forwards',
        'glow-pulse': 'glow 2s ease-in-out infinite alternate',
        'shimmer': 'shimmer 2.2s linear infinite',
        'float': 'float 6s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        glow: {
          '0%': { boxShadow: '0 0 4px rgba(99, 102, 241, 0.15)' },
          '100%': { boxShadow: '0 0 16px rgba(99, 102, 241, 0.4), 0 0 24px rgba(6, 182, 212, 0.25)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-6px)' },
        },
      },
    },
  },
  plugins: [],
}
