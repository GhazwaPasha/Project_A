import { NextResponse } from 'next/server'
import { randomUUID } from 'crypto'
import { neonAuth } from '@/auth'
import { getSql } from '@/server/pg'
import { z } from 'zod'

const postSchema = z.object({
  name: z.string().min(1).max(200),
  description: z.string().max(2000).optional().nullable(),
})

export async function POST(req: Request) {
  try {
    const { data } = await neonAuth.getSession()
    if (!data?.user?.id) {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
    }
    const userId = data.user.id

    const json = await req.json()
    const parsed = postSchema.safeParse(json)
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })
    }

    const { name, description } = parsed.data
    const sql = getSql()

    const profile = await sql<{ id: string }[]>`
      SELECT id FROM public.user_profiles WHERE id = ${userId}::uuid LIMIT 1
    `
    if (profile.length === 0) {
      return NextResponse.json(
        { error: 'Complete your profile before creating an organization.' },
        { status: 400 }
      )
    }

    const orgId = randomUUID()
    const memberId = randomUUID()
    const desc = description?.trim() || 'Created by user'

    const rows = await sql.begin(async (tx) => {
      const inserted = await tx<
        { id: string; name: string; description: string | null; settings: unknown; is_active: boolean; created_at: string; updated_at: string }[]
      >`
        INSERT INTO public.organizations (
          id, name, description, settings, is_active
        ) VALUES (
          ${orgId}::uuid,
          ${name.trim()},
          ${desc},
          ${JSON.stringify({ created_by: userId })}::jsonb,
          true
        )
        RETURNING *
      `
      await tx`
        INSERT INTO public.organization_members (
          id, organization_id, user_id, role, is_active, joined_at
        ) VALUES (
          ${memberId}::uuid,
          ${orgId}::uuid,
          ${userId}::uuid,
          'organization_owner',
          true,
          NOW()
        )
      `
      return inserted
    })

    const org = rows[0]
    if (!org) {
      return NextResponse.json({ error: 'Failed to create organization' }, { status: 500 })
    }

    return NextResponse.json({ organization: org })
  } catch (e) {
    console.error('create organization error', e)
    const code =
      e && typeof e === 'object' && 'code' in e
        ? String((e as { code: unknown }).code)
        : ''
    const isDb =
      code === 'ETIMEDOUT' ||
      code === 'CONNECT_TIMEOUT' ||
      code === 'ECONNREFUSED' ||
      code === 'ENOTFOUND' ||
      (e instanceof Error && /connect|timeout|database/i.test(e.message))
    if (isDb) {
      return NextResponse.json(
        {
          error:
            'Cannot reach the database. Check DATABASE_URL and restart the dev server.',
        },
        { status: 503 }
      )
    }
    if (e instanceof Error && e.message.startsWith('DATABASE_URL host looks like')) {
      return NextResponse.json({ error: e.message }, { status: 400 })
    }
    return NextResponse.json({ error: 'Failed to create organization' }, { status: 500 })
  }
}
