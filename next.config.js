const { loadEnvConfig } = require('@next/env')

const repoRoot = __dirname
const isDev = process.env.NODE_ENV !== 'production'

loadEnvConfig(repoRoot, isDev)

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Next only hosts the API. The web app is a static build in public/app, and every other path loads its index.
  async rewrites() {
    return {
      fallback: [
        { source: '/', destination: '/app/index.html' },
        { source: '/:path((?!api/).*)', destination: '/app/index.html' },
      ],
    }
  },
  async redirects() {
    return [
      { source: '/dashboard', destination: '/home', permanent: true },
      { source: '/dashboard/:path*', destination: '/:path*', permanent: true },
      { source: '/reports/trial-balance', destination: '/trial-balance', permanent: true },
      { source: '/users', destination: '/team', permanent: true },
      { source: '/organization/new', destination: '/settings', permanent: true },
    ]
  },
}

module.exports = nextConfig
