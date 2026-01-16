
module.exports = {
  content: {
    relative: true, 
    files: [
      "../../../custom_index.html", // Reaches root HTML
      "../../../**/*.{js,ts,jsx,tsx}", // Scans all JS files for dynamic classes
    ],
  },
  theme: {
    extend: {},
  },
  plugins: [],
}
