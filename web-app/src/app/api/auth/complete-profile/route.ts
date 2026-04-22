import { NextResponse } from 'next/server'
import { randomUUID } from 'crypto'
import { neonAuth } from '@/auth'
import { getSql } from '@/server/pg'
import { z } from 'zod'

const bodySchema = z.object({
  fullName: z.string().min(1),
  organizationName: z.string().min(1),
  organizationType: z.string().optional().default('business'),
})

export async function POST(req: Request) {
  try {
    const { data } = await neonAuth.getSession()
    if (!data?.user?.id || !data.user.email) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }

    const json = await req.json()
    const parsed = bodySchema.safeParse(json)
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })
    }

    const userId = data.user.id
    const normalizedEmail = data.user.email.trim().toLowerCase()
    const { fullName, organizationName, organizationType } = parsed.data

    const sql = getSql()
    const existingProfile = await sql<{ id: string }[]>`
      SELECT id FROM public.user_profiles WHERE id = ${userId} LIMIT 1
    `
    if (existingProfile.length > 0) {
      return NextResponse.json({ ok: true, alreadyComplete: true })
    }

    const emailRow = await sql<{ id: string }[]>`
      SELECT id FROM public.user_profiles WHERE lower(email) = ${normalizedEmail} LIMIT 1
    `
    if (emailRow.length > 0) {
      return NextResponse.json(
        { error: 'This email is already linked to another account in the app database' },
        { status: 409 }
      )
    }

    const orgId = randomUUID()
    const memberId = randomUUID()

    await sql.begin(async (tx) => {
      await tx`
        INSERT INTO public.user_profiles (
          id, email, full_name, is_super_admin, preferences, password_hash
        ) VALUES (
          ${userId},
          ${normalizedEmail},
          ${fullName},
          false,
          ${JSON.stringify({})}::jsonb,
          NULL
        )
      `
      await tx`
        INSERT INTO public.organizations (
          id, name, description, settings, is_active
        ) VALUES (
          ${orgId},
          ${organizationName},
          ${organizationType + ' organization'},
          ${JSON.stringify({ organization_type: organizationType, created_by: userId })}::jsonb,
          true
        )
      `
      await tx`
        INSERT INTO public.organization_members (
          id, organization_id, user_id, role, is_active, joined_at
        ) VALUES (
          ${memberId},
          ${orgId},
          ${userId},
          'organization_owner',
          true,
          NOW()
        )
      `
    })

    return NextResponse.json({ ok: true })
  } catch (e) {
    console.error('complete-profile error', e)
    return NextResponse.json({ error: 'Profile setup failed' }, { status: 500 })
  }
}
