/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    '../templates/**/*.html',
    '../../sondaje/templates/**/*.html',
    '../../YENO/templates/**/*.html',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Roboto', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#faf5ff',
          100: '#f3e8ff',
          200: '#e9d5ff',
          300: '#d8b4fe',
          400: '#c084fc',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          800: '#6b21a8',
          900: '#581c87',
        }
      },
      borderRadius: {
        'bubbly': '2rem',
        'bubbly-lg': '3rem',
      },
      boxShadow: {
        'bubbly': '0 8px 32px rgba(0, 0, 0, 0.1)',
        'bubbly-lg': '0 16px 48px rgba(0, 0, 0, 0.15)',
      }
    },
  },
  plugins: [],
}

