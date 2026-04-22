const path = require('path')
const fs = require('fs')
const { loadEnvConfig } = require('@next/env')
const { config: loadDotenv } = require('dotenv')

const webApp = __dirname
const repoRoot = path.join(__dirname, '..')
const isDev = process.env.NODE_ENV !== 'production'

// 1) Next: .env* under `web-app/` (optional; for keys only used by the UI)
loadEnvConfig(webApp, isDev)

// 2) Monorepo root: canonical `Project_A/.env` — same keys override web-app
const rootEnvFiles = isDev
  ? ['.env', '.env.local', '.env.development', '.env.development.local']
  : ['.env', '.env.local', '.env.production', '.env.production.local']
for (const name of rootEnvFiles) {
  const file = path.join(repoRoot, name)
  if (fs.existsSync(file)) {
    loadDotenv({ path: file, override: true })
  }
}

// 3) Client: inline every `NEXT_PUBLIC_*` after env resolution (so root can define them)
const nextPublic = {}
for (const [key, value] of Object.entries(process.env)) {
  if (key.startsWith('NEXT_PUBLIC_') && value !== undefined) {
    nextPublic[key] = value
  }
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  env: nextPublic,
}

module.exports = nextConfig
