module.exports = {
  purge: {
    enabled: false,
    mode: 'all',
    content: [
      './templates/**/*.html',
    ],
  },
  theme: {
    extend: {},
  },
  variants: {},
  plugins: [
    // ...
    require('tailwindcss'),
    require('autoprefixer'),
    // ...
  ],
}
