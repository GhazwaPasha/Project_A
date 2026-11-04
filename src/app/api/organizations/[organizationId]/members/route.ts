import { NextResponse } from 'next/server'
import { recordAudit } from '@/server/audit'
import { createInvite } from '@/server/invites'
import { randomUUID } from 'crypto'
import { neonAuth } from '@/auth'
import { getSql } from '@/server/pg'
import { getOrganizationMemberRole, isUserProfileSuperAdmin } from '@/server/organization-access'
import { z } from 'zod'

const postSchema = z.object({
  email: z.string().email(),
  role: z.enum(['accountant', 'member', 'observer']),
})

const patchSchema = z.object({
  memberId: z.string().uuid(),
  role: z.enum(['accountant', 'member', 'observer']),
})

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ organizationId: string }> }
) {
  try {
    const { data } = await neonAuth.getSession()
    if (!data?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const { organizationId } = await ctx.params
    const me = data.user.id

    const myRole = await getOrganizationMemberRole(organizationId, me)
    if (!myRole) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }

    const sql = getSql()
    const members = await sql<
      {
        id: string
        user_id: string
        email: string
        full_name: string | null
        role: string
        joined_at: string | null
      }[]
    >`
      SELECT
        m.id::text,
        m.user_id::text,
        p.email,
        p.full_name,
        m.role,
        m.joined_at::text
      FROM public.organization_members m
      INNER JOIN public.user_profiles p ON p.id = m.user_id
      WHERE m.organization_id = ${organizationId}::uuid
        AND m.is_active = true
      ORDER BY
        (m.role = 'organization_owner') DESC,
        p.email
    `

    return NextResponse.json({ members })
  } catch (e) {
    console.error('org members GET', e)
    return NextResponse.json({ error: 'Failed to list members' }, { status: 500 })
  }
}

export async function POST(
  req: Request,
  ctx: { params: Promise<{ organizationId: string }> }
) {
  try {
    const { data } = await neonAuth.getSession()
    if (!data?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const { organizationId } = await ctx.params
    const actorId = data.user.id

    const myRole = await getOrganizationMemberRole(organizationId, actorId)
    const canManage =
      myRole === 'organization_owner' || (await isUserProfileSuperAdmin(actorId))
    if (!canManage) {
      return NextResponse.json(
        { error: 'Only an organization owner can add members' },
        { status: 403 }
      )
    }

    const json = await req.json()
    const parsed = postSchema.safeParse(json)
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })
    }
    const email = parsed.data.email.trim().toLowerCase()
    const { role } = parsed.data

    const sql = getSql()
    const userRows = await sql<{ id: string }[]>`
      SELECT id::text FROM public.user_profiles WHERE lower(email) = ${email} LIMIT 1
    `
    if (userRows.length === 0) {
      // No account yet, so they get a link to join with instead.
      const invite = await createInvite(organizationId, email, role, actorId)
      await recordAudit({ org: organizationId, userId: actorId, action: 'Invite team member', targetType: 'invite', targetId: invite.id, details: { email, role } })
      return NextResponse.json({ ok: true, invite: { id: invite.id, token: invite.token, expires_at: invite.expires_at, email } })
    }
    const targetId = userRows[0]!.id

    const existing = await sql<{ id: string }[]>`
      SELECT id::text FROM public.organization_members
      WHERE organization_id = ${organizationId}::uuid AND user_id = ${targetId}::uuid
      LIMIT 1
    `
    if (existing.length > 0) {
      return NextResponse.json(
        { error: 'This user is already a member of this organization' },
        { status: 409 }
      )
    }

    const newId = randomUUID()
    await sql`
      INSERT INTO public.organization_members (
        id, organization_id, user_id, role, is_active, joined_at
      ) VALUES (
        ${newId}::uuid,
        ${organizationId}::uuid,
        ${targetId}::uuid,
        ${role},
        true,
        NOW()
      )
    `

    await recordAudit({ org: organizationId, userId: actorId, action: 'Add team member', targetType: 'member', targetId: targetId, details: { email, role } })
    return NextResponse.json({ ok: true, member: { id: newId, user_id: targetId, role } })
  } catch (e) {
    console.error('org members POST', e)
    if (e && typeof e === 'object' && 'code' in e && (e as { code: string }).code === '23505') {
      return NextResponse.json(
        { error: 'This user is already a member of this organization' },
        { status: 409 }
      )
    }
    return NextResponse.json({ error: 'Failed to add member' }, { status: 500 })
  }
}

export async function PATCH(
  req: Request,
  ctx: { params: Promise<{ organizationId: string }> }
) {
  try {
    const { data } = await neonAuth.getSession()
    if (!data?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const { organizationId } = await ctx.params
    const actorId = data.user.id
    const myRole = await getOrganizationMemberRole(organizationId, actorId)
    const canManage =
      myRole === 'organization_owner' || (await isUserProfileSuperAdmin(actorId))
    if (!canManage) {
      return NextResponse.json(
        { error: 'Only an organization owner can change member roles' },
        { status: 403 }
      )
    }

    const json = await req.json()
    const parsed = patchSchema.safeParse(json)
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })
    }

    const { memberId, role } = parsed.data
    const sql = getSql()
    const targetRows = await sql<{ user_id: string; role: string }[]>`
      SELECT user_id::text, role
      FROM public.organization_members
      WHERE id = ${memberId}::uuid
        AND organization_id = ${organizationId}::uuid
        AND is_active = true
      LIMIT 1
    `

    const target = targetRows[0]
    if (!target) {
      return NextResponse.json({ error: 'Member not found' }, { status: 404 })
    }
    if (target.user_id === actorId) {
      return NextResponse.json({ error: 'You cannot change your own role' }, { status: 400 })
    }
    if (target.role === 'organization_owner') {
      return NextResponse.json({ error: 'Owner roles cannot be changed here' }, { status: 400 })
    }

    await sql`
      UPDATE public.organization_members
      SET role = ${role}
      WHERE id = ${memberId}::uuid
        AND organization_id = ${organizationId}::uuid
        AND is_active = true
    `

    await recordAudit({ org: organizationId, userId: actorId, action: 'Change team member role', targetType: 'member', targetId: target.user_id, details: { from: target.role, to: role } })
    return NextResponse.json({ ok: true, member: { id: memberId, role } })
  } catch (e) {
    console.error('org members PATCH', e)
    return NextResponse.json({ error: 'Failed to change member role' }, { status: 500 })
  }
}
