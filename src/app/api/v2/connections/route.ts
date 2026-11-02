import { NextResponse } from 'next/server'
import { z } from 'zod/v4'
import { authInApiRoute } from '@/auth'
import { authorizeAppDataCall } from '@/server/app-data-authorize'
import { createToken, listTokens, revokeToken } from '@/server/mcp/tokens'

const failure = (e: unknown) => {
  if ((e as { code?: string })?.code === '42P01') return NextResponse.json({ error: 'Connections are not set up on this database yet.', code: 'SCHEMA_NOT_READY' }, { status: 503 })
  const message = e instanceof Error ? e.message : 'Something went wrong'
  return NextResponse.json({ error: message === 'Forbidden' ? 'Your role does not include connections.' : message }, { status: message === 'Forbidden' ? 403 : 400 })
}

export async function GET(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const org = new URL(req.url).searchParams.get('org')
  try {
    await authorizeAppDataCall('DataService', 'getAccounts', [org, false], session.user.id)
    return NextResponse.json(await listTokens(session.user.id, org as string))
  } catch (e) {
    return failure(e)
  }
}

const Create = z.object({ org: z.string().uuid(), name: z.string().trim().min(1).max(80), canRecord: z.boolean() })

export async function POST(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const parsed = Create.safeParse(await req.json().catch(() => null))
  if (!parsed.success) return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  const { org, name, canRecord } = parsed.data
  try {
    await authorizeAppDataCall('DataService', 'getAccounts', [org, false], session.user.id)
    // A connection can only be allowed to record if the person creating it can.
    if (canRecord) await authorizeAppDataCall('DataService', 'createJournalEntry', [{ organization_id: org }], session.user.id)
    return NextResponse.json(await createToken(session.user.id, org, name, canRecord))
  } catch (e) {
    return failure(e)
  }
}

export async function DELETE(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const id = z.string().uuid().safeParse(new URL(req.url).searchParams.get('id'))
  if (!id.success) return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  try {
    const ok = await revokeToken(session.user.id, id.data)
    return ok ? NextResponse.json({ status: 'revoked' }) : NextResponse.json({ error: 'Connection not found' }, { status: 404 })
  } catch (e) {
    return failure(e)
  }
}
