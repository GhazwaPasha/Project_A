import { NextResponse } from 'next/server'
import { z } from 'zod/v4'
import { authInApiRoute } from '@/auth'
import { recordAudit } from '@/server/audit'
import { acceptInvite } from '@/server/invites'
import { allowRequest, tooMany } from '@/server/rate-limit'

const Body = z.object({ token: z.string().min(20).max(200) })

export async function POST(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  if (!(await allowRequest(`invite-accept:${session.user.id}`, 10))) return tooMany()
  const parsed = Body.safeParse(await req.json().catch(() => null))
  if (!parsed.success) return NextResponse.json({ error: 'This invite link is not valid.' }, { status: 400 })
  try {
    const joined = await acceptInvite(parsed.data.token, { id: session.user.id, email: session.user.email })
    await recordAudit({ org: joined.organization_id, userId: session.user.id, action: 'Accept invite', targetType: 'member', targetId: session.user.id, details: { role: joined.role } })
    return NextResponse.json(joined)
  } catch (e) {
    if (typeof (e as { code?: unknown })?.code === 'string') {
      console.error('invite accept', (e as { code?: unknown }).code)
      return NextResponse.json({ error: 'Could not accept this invite. Try again.' }, { status: 500 })
    }
    return NextResponse.json({ error: e instanceof Error ? e.message : 'Could not accept this invite.' }, { status: 400 })
  }
}
