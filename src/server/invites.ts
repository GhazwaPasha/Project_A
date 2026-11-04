import { createHash, randomBytes } from 'crypto'
import { getSql } from '@/server/pg'

const VALID_DAYS = 14
const hash = (token: string) => createHash('sha256').update(token).digest('hex')
type Row = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any

/**
 * Makes a link for someone who has no account yet. Only a hash is stored, so the link can only be seen once.
 * A new invite to the same email replaces the old one.
 */
export async function createInvite(org: string, email: string, role: string, invitedBy: string) {
  const address = email.trim().toLowerCase()
  const token = randomBytes(32).toString('base64url')
  const sql = getSql()
  await sql`UPDATE public.organization_invites SET revoked_at = now() WHERE organization_id = ${org}::uuid AND lower(email) = ${address} AND accepted_at IS NULL AND revoked_at IS NULL`
  const [row] = (await sql`
    INSERT INTO public.organization_invites (organization_id, email, role, token_hash, invited_by, expires_at)
    VALUES (${org}::uuid, ${address}, ${role}, ${hash(token)}, ${invitedBy}::uuid, now() + make_interval(days => ${VALID_DAYS}))
    RETURNING id, expires_at::text AS expires_at
  `) as Row[]
  return { id: Number(row.id), token, expires_at: row.expires_at as string }
}

export function listInvites(org: string) {
  return getSql()`
    SELECT id, email, role, expires_at::text AS expires_at, created_at::text AS created_at
    FROM public.organization_invites
    WHERE organization_id = ${org}::uuid AND accepted_at IS NULL AND revoked_at IS NULL AND expires_at > now()
    ORDER BY created_at DESC
  `
}

export async function revokeInvite(org: string, id: number) {
  const rows = await getSql()`UPDATE public.organization_invites SET revoked_at = now() WHERE id = ${id} AND organization_id = ${org}::uuid AND accepted_at IS NULL AND revoked_at IS NULL RETURNING id`
  if (!rows.length) throw new Error('This invite is no longer open.')
}

/** Joins the organization. The link has to match the person's own email, so a forwarded link is no use to anyone else. */
export async function acceptInvite(token: string, user: { id: string; email: string }) {
  return getSql().begin(async (tx) => {
    const [invite] = (await tx`SELECT * FROM public.organization_invites WHERE token_hash = ${hash(token)} FOR UPDATE`) as unknown as Row[]
    if (!invite || invite.revoked_at) throw new Error('This invite is no longer valid. Ask for a new one.')
    if (invite.accepted_at) throw new Error('This invite has already been used.')
    if (new Date(invite.expires_at).getTime() < Date.now()) throw new Error('This invite has expired. Ask for a new one.')
    if (String(invite.email).toLowerCase() !== user.email.trim().toLowerCase()) throw new Error(`This invite is for ${invite.email}. Sign in with that email to accept it.`)
    await tx`
      INSERT INTO public.organization_members (id, organization_id, user_id, role, is_active, joined_at, invited_by)
      VALUES (gen_random_uuid(), ${invite.organization_id}::uuid, ${user.id}::uuid, ${invite.role}, true, now(), ${invite.invited_by})
      ON CONFLICT (organization_id, user_id) DO UPDATE SET is_active = true
    `
    await tx`UPDATE public.organization_invites SET accepted_at = now(), accepted_by = ${user.id}::uuid WHERE id = ${invite.id}`
    return { organization_id: String(invite.organization_id), role: String(invite.role) }
  })
}
