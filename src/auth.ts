import { createNeonAuth } from '@neon/auth/next/server'

function neonAuthConfig() {
  const baseUrl = process.env.NEON_AUTH_BASE_URL?.trim()
  const secret = process.env.NEON_AUTH_COOKIE_SECRET?.trim()
  if (!baseUrl) {
    throw new Error(
      'NEON_AUTH_BASE_URL is not set. Add it from the Neon console (Neon Auth / project settings).'
    )
  }
  if (!secret || secret.length < 32) {
    throw new Error(
      'NEON_AUTH_COOKIE_SECRET must be at least 32 characters. Generate one with: openssl rand -base64 32'
    )
  }
  return {
    baseUrl,
    cookies: { secret },
  }
}

export const neonAuth = createNeonAuth(neonAuthConfig())

export type AppSessionUser = {
  id: string
  email: string
  name?: string | null
}

export type AppSession = {
  user: AppSessionUser
}

/**
 * Resolves the current user via `neonAuth.getSession()` (see Neon Next.js server SDK). That call
 * refreshes session cookies when the signed session-data cache is stale or expiring—unlike a
 * read-only `jwtVerify` of `session_data`, which fails after the cache TTL and makes full page
 * reloads look “logged out” even though the browser still holds a valid session token.
 */
async function getAppSessionFromNeon(): Promise<AppSession | null> {
  const { data } = await neonAuth.getSession()
  if (!data?.user) return null
  return {
    user: {
      id: data.user.id,
      email: data.user.email,
      name: data.user.name ?? null,
    },
  }
}

/**
 * App Router server usage (RSC layouts, `page.tsx`): same session as API routes, including refresh.
 * Layouts using this must use `export const dynamic = 'force-dynamic'` (already the case) because
 * the session depends on request cookies.
 */
export async function auth(): Promise<AppSession | null> {
  return getAppSessionFromNeon()
}

/**
 * Route Handlers / `auth()` for API routes. Same implementation as `auth()`.
 */
export async function authInApiRoute(): Promise<AppSession | null> {
  return getAppSessionFromNeon()
}
