import { NextResponse } from 'next/server'
import { z } from 'zod/v4'
import { authInApiRoute } from '@/auth'
import { approveProposal, discardProposal, listProposals } from '@/server/agent/proposals'
import { authorizeAppDataCall } from '@/server/app-data-authorize'

const NOT_MIGRATED = '42P01'
const failure = (e: unknown) => {
  if ((e as { code?: string })?.code === NOT_MIGRATED) return NextResponse.json({ error: 'Proposals are not set up on this database yet.', code: 'SCHEMA_NOT_READY' }, { status: 503 })
  const message = e instanceof Error ? e.message : 'Something went wrong'
  return NextResponse.json({ error: message }, { status: message === 'Forbidden' ? 403 : 400 })
}

export async function GET(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const org = new URL(req.url).searchParams.get('org')
  try {
    await authorizeAppDataCall('DataService', 'getAccounts', [org, false], session.user.id)
    return NextResponse.json(await listProposals(org as string))
  } catch (e) {
    return failure(e)
  }
}

const Decision = z.object({ org: z.string().uuid(), id: z.string().uuid(), action: z.enum(['approve', 'discard']) })

/** A person's decision. Only this route turns a proposal into a recorded entry. */
export async function POST(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  const parsed = Decision.safeParse(await req.json().catch(() => null))
  if (!parsed.success) return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  const { org, id, action } = parsed.data
  try {
    if (action === 'discard') {
      await discardProposal(session.user.id, org, id)
      return NextResponse.json({ status: 'discarded' })
    }
    const entry = await approveProposal(session.user.id, org, id)
    return NextResponse.json({ status: 'recorded', entry_number: entry.entry_number })
  } catch (e) {
    return failure(e)
  }
}
