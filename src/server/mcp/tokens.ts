import { createHash, randomBytes } from 'node:crypto'
import { getSql } from '@/server/pg'

const hash = (token: string) => createHash('sha256').update(token).digest('hex')

export type McpTokenRow = { id: string; name: string; token_hint: string; can_record: boolean; created_at: string; last_used_at: string | null }
export type McpPrincipal = { userId: string; org: string; canRecord: boolean; name: string }

/** Returns the token once. Only its hash is stored, so it can't be shown again or leak from the database. */
export async function createToken(userId: string, org: string, name: string, canRecord: boolean) {
  const token = `acct_${randomBytes(32).toString('base64url')}`
  const sql = getSql()
  const rows = await sql<McpTokenRow[]>`
    INSERT INTO public.mcp_tokens (user_id, organization_id, name, token_hash, token_hint, can_record)
    VALUES (${userId}::uuid, ${org}::uuid, ${name}, ${hash(token)}, ${token.slice(-4)}, ${canRecord})
    RETURNING id::text, name, token_hint, can_record, created_at::text, last_used_at::text
  `
  return { token, row: rows[0] }
}

export async function listTokens(userId: string, org: string) {
  const sql = getSql()
  return (await sql<McpTokenRow[]>`
    SELECT id::text, name, token_hint, can_record, created_at::text, last_used_at::text
    FROM public.mcp_tokens
    WHERE user_id = ${userId}::uuid AND organization_id = ${org}::uuid AND revoked_at IS NULL
    ORDER BY created_at DESC
  `) as McpTokenRow[]
}

export async function revokeToken(userId: string, id: string) {
  const sql = getSql()
  const rows = await sql`
    UPDATE public.mcp_tokens SET revoked_at = now()
    WHERE id = ${id}::uuid AND user_id = ${userId}::uuid AND revoked_at IS NULL
    RETURNING id
  `
  return rows.length > 0
}

export async function principalFromRequest(req: Request): Promise<McpPrincipal | null> {
  const match = req.headers.get('authorization')?.match(/^Bearer\s+(acct_[\w-]+)$/)
  if (!match) return null
  const sql = getSql()
  const rows = await sql<{ id: string; user_id: string; organization_id: string; can_record: boolean; name: string }[]>`
    SELECT id::text, user_id::text, organization_id::text, can_record, name
    FROM public.mcp_tokens
    WHERE token_hash = ${hash(match[1])} AND revoked_at IS NULL
    LIMIT 1
  `
  const row = rows[0]
  if (!row) return null
  void sql`UPDATE public.mcp_tokens SET last_used_at = now() WHERE id = ${row.id}::uuid`.then(() => undefined, () => undefined)
  return { userId: row.user_id, org: row.organization_id, canRecord: row.can_record, name: row.name }
}
