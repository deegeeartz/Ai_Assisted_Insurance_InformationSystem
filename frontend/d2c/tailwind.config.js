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
          DEFAULT: 'hsl(220 90% 40%)',
          light: 'hsl(220 90% 60%)',
        }
      }
    },
  },
  plugins: [],
}
