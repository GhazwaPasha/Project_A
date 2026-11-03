import { NextResponse } from 'next/server'
import { z } from 'zod/v4'
import { registerClient } from '@/server/mcp/oauth'
import { allowRequest, clientIp, tooMany } from '@/server/rate-limit'

const Body = z.object({ client_name: z.string().max(200).optional(), redirect_uris: z.array(z.string().max(500)).min(1).max(10) })

/** Lets an AI app register itself. Registering grants nothing: a person still has to approve it. */
export async function POST(req: Request) {
  if (!(await allowRequest(`oauth-register:${clientIp(req)}`, 10))) return tooMany()
  const parsed = Body.safeParse(await req.json().catch(() => null))
  if (!parsed.success) return NextResponse.json({ error: 'invalid_client_metadata' }, { status: 400 })
  try {
    const { clientId, name } = await registerClient(parsed.data.client_name ?? 'An AI app', parsed.data.redirect_uris)
    return NextResponse.json({ client_id: clientId, client_name: name, redirect_uris: parsed.data.redirect_uris, grant_types: ['authorization_code'], response_types: ['code'], token_endpoint_auth_method: 'none' }, { status: 201 })
  } catch (e) {
    if (e instanceof Error && e.message === 'invalid_redirect_uri') return NextResponse.json({ error: 'invalid_redirect_uri' }, { status: 400 })
    throw e
  }
}
