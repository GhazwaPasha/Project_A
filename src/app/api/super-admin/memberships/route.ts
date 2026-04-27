import { NextResponse } from 'next/server'
import { z } from 'zod'
import { getSql } from '@/server/pg'
import { requirePlatformSuperAdmin, SuperAdminHttpError } from '@/server/super-admin'

const patchSchema = z.object({
  membershipId: z.string().uuid(),
  role: z.enum(['accountant', 'member', 'observer']),
})

export async function PATCH(req: Request) {
  try {
    const actor = await requirePlatformSuperAdmin()
    const json = await req.json()
    const parsed = patchSchema.safeParse(json)
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })
    }

    const { membershipId, role } = parsed.data
    const sql = getSql()
    const targetRows = await sql<
      {
        user_id: string
        role: string
      }[]
    >`
      SELECT user_id::text, role
      FROM public.organization_members
      WHERE id = ${membershipId}::uuid
        AND is_active = true
      LIMIT 1
    `

    const target = targetRows[0]
    if (!target) {
      return NextResponse.json({ error: 'Membership not found' }, { status: 404 })
    }
    if (target.user_id === actor.userId) {
      return NextResponse.json({ error: 'You cannot change your own organization role here' }, { status: 400 })
    }
    if (target.role === 'organization_owner') {
      return NextResponse.json({ error: 'Owner roles cannot be changed here' }, { status: 400 })
    }

    const rows = await sql<
      {
        id: string
        organization_id: string
        user_id: string
        role: string
      }[]
    >`
      UPDATE public.organization_members
      SET role = ${role}
      WHERE id = ${membershipId}::uuid
        AND is_active = true
      RETURNING id::text, organization_id::text, user_id::text, role
    `

    return NextResponse.json({ ok: true, membership: rows[0] })
  } catch (e) {
    if (e instanceof SuperAdminHttpError) {
      return NextResponse.json({ error: e.message }, { status: e.status })
    }
    console.error('super admin memberships PATCH', e)
    return NextResponse.json({ error: 'Failed to update membership' }, { status: 500 })
  }
}
