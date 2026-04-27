import { NextResponse } from 'next/server'
import { neonAuth } from '@/auth'
import { getSql } from '@/server/pg'
import { getOrgPermissionSnapshot } from '@/server/organization-access'
import { z } from 'zod'
import type { Organization } from '@/types'

const patchBody = z.object({
  name: z.string().min(1).max(200).optional(),
  description: z.string().max(2000).nullable().optional(),
  settings: z.record(z.unknown()).optional(),
})

function toSettingsObject(raw: unknown): Record<string, unknown> {
  if (raw == null) return {}
  if (typeof raw === 'string') {
    try {
      const p = JSON.parse(raw) as unknown
      if (p && typeof p === 'object' && !Array.isArray(p)) {
        return p as Record<string, unknown>
      }
    } catch {
      return {}
    }
    return {}
  }
  if (typeof raw === 'object' && !Array.isArray(raw)) {
    return raw as Record<string, unknown>
  }
  return {}
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
    const userId = data.user.id
    const { organizationId } = await ctx.params

    const snap = await getOrgPermissionSnapshot(userId, organizationId)
    if (!snap) {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    const { isSuperAdmin, memberRole } = snap
    if (!isSuperAdmin) {
      if (!memberRole) {
        return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
      }
      if (memberRole !== 'organization_owner' && memberRole !== 'accountant') {
        return NextResponse.json(
          { error: 'You do not have permission to change organization settings.' },
          { status: 403 }
        )
      }
    }

    const json = await req.json()
    const parsed = patchBody.safeParse(json)
    if (!parsed.success) {
      return NextResponse.json({ error: parsed.error.flatten() }, { status: 400 })
    }
    const { name, description, settings: settingsPatch } = parsed.data
    if (name === undefined && description === undefined && settingsPatch === undefined) {
      return NextResponse.json({ error: 'Nothing to update' }, { status: 400 })
    }

    const sql = getSql()
    const rows = await sql<Organization[]>`
      SELECT * FROM public.organizations
      WHERE id = ${organizationId}::uuid
      LIMIT 1
    `
    const org = rows[0]
    if (!org) {
      return NextResponse.json({ error: 'Organization not found' }, { status: 404 })
    }

    // Shallow merge: client sends top-level `accountingSettings` and other
    // sections as full objects so `reportingCurrency` replaces the previous value.
    const currentSettings = toSettingsObject(org.settings)
    const newSettings: Record<string, unknown> = settingsPatch
      ? { ...currentSettings, ...settingsPatch }
      : currentSettings

    const nextName = name !== undefined ? name : org.name
    const nextDescription = description !== undefined ? description : org.description

    const updated = await sql<Organization[]>`
      UPDATE public.organizations
      SET
        name = ${nextName.trim()},
        description = ${nextDescription},
        settings = ${JSON.stringify(newSettings)}::jsonb,
        updated_at = NOW()
      WHERE id = ${organizationId}::uuid
      RETURNING *
    `

    const out = updated[0]
    if (!out) {
      return NextResponse.json({ error: 'Update failed' }, { status: 500 })
    }
    return NextResponse.json({ organization: out })
  } catch (e) {
    console.error('org PATCH', e)
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
        { error: 'Cannot reach the database. Check DATABASE_URL and restart the dev server.' },
        { status: 503 }
      )
    }
    return NextResponse.json({ error: 'Failed to update organization' }, { status: 500 })
  }
}
