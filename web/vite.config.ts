import path from 'node:path'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig(({ command }) => ({
  // Next serves the build's files from public/app, while the app's own URLs start at the root.
  base: command === 'build' ? '/app/' : '/',
  plugins: [react(), tailwindcss()],
  resolve: { alias: { '@': path.resolve(__dirname, './src') } },
  build: { outDir: '../public/app', emptyOutDir: true },
  server: { port: 5180, proxy: { '/api': 'http://localhost:3000' } },
}))
