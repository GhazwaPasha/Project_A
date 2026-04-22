import { createNeonAuth } from '@neondatabase/auth/next/server'

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
 */
export async function auth(): Promise<AppSession | null> {
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
