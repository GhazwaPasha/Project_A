import { NextResponse } from 'next/server'
import { authInApiRoute } from '@/auth'
import { recordAudit } from '@/server/audit'
import { listInvites, revokeInvite } from '@/server/invites'
import { getOrganizationMemberRole, isUserProfileSuperAdmin } from '@/server/organization-access'

type Ctx = { params: Promise<{ organizationId: string }> }

/** Invites are open to owners only, like adding a member. */
async function owner(ctx: Ctx) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return { error: NextResponse.json({ error: 'Unauthorized' }, { status: 401 }) }
  const { organizationId } = await ctx.params
  const role = await getOrganizationMemberRole(organizationId, session.user.id)
  if (role !== 'organization_owner' && !(await isUserProfileSuperAdmin(session.user.id))) {
    return { error: NextResponse.json({ error: 'Only an organization owner can manage invites' }, { status: 403 }) }
  }
  return { organizationId, userId: session.user.id }
}

export async function GET(_req: Request, ctx: Ctx) {
  const who = await owner(ctx)
  if (who.error) return who.error
  return NextResponse.json({ invites: await listInvites(who.organizationId) })
}

export async function DELETE(req: Request, ctx: Ctx) {
  const who = await owner(ctx)
  if (who.error) return who.error
  const id = Number(new URL(req.url).searchParams.get('id'))
  if (!Number.isInteger(id) || id <= 0) return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  try {
    await revokeInvite(who.organizationId, id)
    await recordAudit({ org: who.organizationId, userId: who.userId, action: 'Revoke invite', targetType: 'invite', targetId: id })
    return NextResponse.json({ ok: true })
  } catch (e) {
    return NextResponse.json({ error: e instanceof Error ? e.message : 'Could not revoke the invite.' }, { status: 400 })
  }
}
