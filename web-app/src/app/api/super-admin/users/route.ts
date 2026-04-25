import { NextResponse } from 'next/server'
import { z } from 'zod'
import { getSql } from '@/server/pg'
import { requirePlatformSuperAdmin, SuperAdminHttpError } from '@/server/super-admin'

const patchSchema = z.object({
  userId: z.string().uuid(),
  isSuperAdmin: z.boolean(),
})

export async function PATCH(req: Request) {
  try {
    const actor = await requirePlatformSuperAdmin()
    const json = await req.json()
    const parsed = patchSchema.safeParse(json)
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })
    }

    const { userId, isSuperAdmin } = parsed.data
    if (actor.userId === userId && !isSuperAdmin) {
      return NextResponse.json({ error: 'You cannot remove your own super admin access' }, { status: 400 })
    }

    const sql = getSql()
    const rows = await sql<
      {
        id: string
        email: string
        full_name: string | null
        is_super_admin: boolean
      }[]
    >`
      UPDATE public.user_profiles
      SET is_super_admin = ${isSuperAdmin}, updated_at = NOW()
      WHERE id = ${userId}::uuid
      RETURNING id::text, email, full_name, is_super_admin
    `

    const user = rows[0]
    if (!user) {
      return NextResponse.json({ error: 'User not found' }, { status: 404 })
    }

    return NextResponse.json({ ok: true, user })
  } catch (e) {
    if (e instanceof SuperAdminHttpError) {
      return NextResponse.json({ error: e.message }, { status: e.status })
    }
    console.error('super admin users PATCH', e)
    return NextResponse.json({ error: 'Failed to update user' }, { status: 500 })
  }
}
