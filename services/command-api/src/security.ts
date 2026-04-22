import type { Context, Next } from 'hono'

/**
 * Trust boundary: Next.js BFF verifies Auth.js (`auth()`), then forwards
 * `X-User-Id` + `X-Command-Secret`. Run command-api on a private interface in production.
 */
export async function commandAuthMiddleware(c: Context, next: Next) {
  const expected = process.env.COMMAND_API_SECRET
  if (!expected) {
    return c.json({ error: 'COMMAND_API_SECRET is not configured on command-api' }, 503)
  }
  const secret = c.req.header('x-command-secret')
  if (secret !== expected) {
    return c.json({ error: 'Unauthorized' }, 401)
  }
  const userId = c.req.header('x-user-id')
  if (!userId) {
    return c.json({ error: 'Missing X-User-Id' }, 401)
  }
  c.set('userId', userId)
  await next()
}
