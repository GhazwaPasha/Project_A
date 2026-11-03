import { NextResponse } from 'next/server'
import { z } from 'zod/v4'
import { authInApiRoute } from '@/auth'
import { authorizeAppDataCall } from '@/server/app-data-authorize'
import { createCode, findClient } from '@/server/mcp/oauth'

const Body = z.object({
  client_id: z.string().max(100),
  redirect_uri: z.string().max(500),
  code_challenge: z.string().min(43).max(128),
  code_challenge_method: z.literal('S256'),
  state: z.string().max(1000).optional(),
  org: z.string().uuid(),
  can_record: z.boolean(),
})

/** A signed-in person approves an app, here on this site only. */
export async function POST(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  // Only this site's own page may approve, so another site can't trick a signed-in person's browser into it.
  const origin = req.headers.get('origin')
  const host = req.headers.get('x-forwarded-host') ?? req.headers.get('host')
  if (!origin || new URL(origin).host !== host) return NextResponse.json({ error: 'Forbidden' }, { status: 403 })

  const parsed = Body.safeParse(await req.json().catch(() => null))
  if (!parsed.success) return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  const b = parsed.data
  if (!(await findClient(b.client_id, b.redirect_uri))) return NextResponse.json({ error: 'This app is not recognized.' }, { status: 400 })
  try {
    await authorizeAppDataCall('DataService', 'getAccounts', [b.org, false], session.user.id)
    if (b.can_record) await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: b.org }], session.user.id)
  } catch {
    return NextResponse.json({ error: 'Your role does not allow this for that organization.' }, { status: 403 })
  }
  const code = await createCode({ clientId: b.client_id, userId: session.user.id, org: b.org, redirectUri: b.redirect_uri, challenge: b.code_challenge, canRecord: b.can_record })
  const target = new URL(b.redirect_uri)
  target.searchParams.set('code', code)
  if (b.state) target.searchParams.set('state', b.state)
  return NextResponse.json({ redirect: target.toString() })
}
