import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  base: '/app/',
  plugins: [react(), tailwindcss()],
  // Keeps the old app's PostCSS and Tailwind 3 config in the repo root from applying here.
  css: { postcss: { plugins: [] } },
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  build: { outDir: '../public/app', emptyOutDir: true },
  server: { port: 5180, proxy: { '/api': 'http://localhost:3000' } },
})
