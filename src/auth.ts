import { createNeonAuth } from '@neondatabase/auth/next/server'
import { cookies } from 'next/headers'
import { jwtVerify } from 'jose'

/**
 * @see @neondatabase/auth Next server adapter (session cache + session token)
 */
const NEON_AUTH_SESSION_DATA_COOKIES = [
  '__Secure-neon-auth.session_data',
  '__Secure-neon-auth.local.session_data',
  'neon-auth.session_data',
  'neon-auth.local.session_data',
]
const NEON_AUTH_SESSION_TOKEN_COOKIES = [
  '__Secure-neon-auth.session_token',
  '__Secure-neon-auth.local.session_token',
  'neon-auth.session_token',
  'neon-auth.local.session_token',
]

function getFirstCookieValue(
  store: Awaited<ReturnType<typeof cookies>>,
  names: readonly string[]
): string | null {
  for (const name of names) {
    const value = store.get(name)?.value
    if (value) return value
  }
  return null
}

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
 * Server-side session in the shape the app used with NextAuth (`session.user.id`, etc.).
 *
 * Uses only the signed session-data cookie (read-only). Safe in React Server Components;
 * it does not call `neonAuth.getSession()`, which may refresh tokens via `cookies().set()`
 * and trigger: "Cookies can only be modified in a Server Action or Route Handler."
 *
 * For Route Handlers that must refresh the session, use `authInApiRoute()` instead.
 */
export async function auth(): Promise<AppSession | null> {
  const secret = process.env.NEON_AUTH_COOKIE_SECRET?.trim()
  if (!secret) return null

  const store = await cookies()
  if (!getFirstCookieValue(store, NEON_AUTH_SESSION_TOKEN_COOKIES)) return null
  const sessionDataValue = getFirstCookieValue(store, NEON_AUTH_SESSION_DATA_COOKIES)
  if (!sessionDataValue) return null

  try {
    const { payload } = await jwtVerify(sessionDataValue, new TextEncoder().encode(secret), {
      algorithms: ['HS256'],
    })
    const u = (payload as { user?: { id?: string; email?: string; name?: string | null } }).user
    if (!u?.id || !u?.email) return null
    return {
      user: { id: u.id, email: u.email, name: u.name ?? null },
    }
  } catch {
    return null
  }
}

/**
 * Full Neon session; may update cookies. Use in Route Handlers (or Server Actions) only.
 */
export async function authInApiRoute(): Promise<AppSession | null> {
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
