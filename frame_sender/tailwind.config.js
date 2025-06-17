// tailwind.config.js
module.exports = {
  content: ["./src/**/*.{html,js,jsx,tsx}"],
  theme: {
    extend: {
      animation: {
        'gradient-x': 'gradientX 8s ease infinite',
      },
      keyframes: {
        gradientX: {
          '0%, 100%': { 'background-position': '0% 50%' },
          '50%': { 'background-position': '100% 50%' },
        },
      },
      backgroundImage: {
        'neon-gradient': 'linear-gradient(-45deg, #ff073a, #00f0ff, #ff073a, #00f0ff)',
      },
      backgroundSize: {
        '4x': '400% 400%',
      },
    },
  },
  plugins: [],
}
