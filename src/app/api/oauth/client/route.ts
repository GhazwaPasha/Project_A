import { NextResponse } from 'next/server'
import { authInApiRoute } from '@/auth'
import { findClient } from '@/server/mcp/oauth'

/** Tells the approval screen which app is asking. It reports an unknown app rather than redirecting anywhere. */
export async function GET(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const q = new URL(req.url).searchParams
  const client = await findClient(q.get('client_id') ?? '', q.get('redirect_uri') ?? '')
  return client ? NextResponse.json(client) : NextResponse.json({ error: 'This app is not recognized.' }, { status: 404 })
}
