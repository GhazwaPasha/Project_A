const { loadEnvConfig } = require('@next/env')

const repoRoot = __dirname
const isDev = process.env.NODE_ENV !== 'production'

loadEnvConfig(repoRoot, isDev)

// Client: inline every `NEXT_PUBLIC_*` after env resolution
const nextPublic = {}
for (const [key, value] of Object.entries(process.env)) {
  if (key.startsWith('NEXT_PUBLIC_') && value !== undefined) {
    nextPublic[key] = value
  }
}

/** @type {import('next').NextConfig} */
const nextConfig = {
  env: nextPublic,
  async redirects() {
    return [
      { source: '/dashboard', destination: '/home', permanent: true },
      { source: '/dashboard/:path*', destination: '/:path*', permanent: true },
    ]
  },
}

module.exports = nextConfig
