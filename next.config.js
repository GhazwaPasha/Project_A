const { loadEnvConfig } = require('@next/env')

const repoRoot = __dirname
const isDev = process.env.NODE_ENV !== 'production'

loadEnvConfig(repoRoot, isDev)

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Next only hosts the API. The web app is a static build in public/app, and every other path loads its index.
  async rewrites() {
    return {
      // MCP sign-in discovery. Some apps also append the resource path, so both forms are served.
      beforeFiles: [
        { source: '/.well-known/oauth-authorization-server/:path*', destination: '/api/oauth/metadata/authorization-server' },
        { source: '/.well-known/oauth-protected-resource/:path*', destination: '/api/oauth/metadata/protected-resource' },
      ],
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
