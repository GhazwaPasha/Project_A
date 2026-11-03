import { getSql } from '@/server/pg'

/**
 * Counts requests per key per minute in Postgres, so the limit holds across serverless instances.
 * A limiter failure lets the request through: it protects the app, it shouldn't take it down.
 */
export async function allowRequest(key: string, maxPerMinute: number): Promise<boolean> {
  try {
    const sql = getSql()
    const [row] = await sql<{ count: number }[]>`
      INSERT INTO public.rate_limits (key, window_start, count)
      VALUES (${key}, date_trunc('minute', now()), 1)
      ON CONFLICT (key, window_start) DO UPDATE SET count = public.rate_limits.count + 1
      RETURNING count
    `
    // Now and then, clear out old windows.
    if (Math.random() < 0.01) void sql`DELETE FROM public.rate_limits WHERE window_start < now() - interval '1 hour'`.then(() => undefined, () => undefined)
    return Number(row.count) <= maxPerMinute
  } catch {
    return true
  }
}

export const tooMany = () => new Response(JSON.stringify({ error: "Too many requests. Please wait a minute and try again." }), {
  status: 429,
  headers: { 'Content-Type': 'application/json', 'Retry-After': '60' },
})

export const clientIp = (req: Request) => req.headers.get('x-real-ip') ?? req.headers.get('x-forwarded-for')?.split(',')[0]?.trim() ?? 'unknown'
