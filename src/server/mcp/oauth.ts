import { createHash, randomBytes, timingSafeEqual } from 'node:crypto'
import { getSql } from '@/server/pg'
import { createToken } from '@/server/mcp/tokens'

const sha256 = (s: string) => createHash('sha256').update(s).digest()
const hash = (s: string) => sha256(s).toString('hex')

/** Web redirects must be https, or plain http only to this machine. Desktop apps may use their own scheme. */
export function validRedirect(uri: string) {
  let u: URL
  try { u = new URL(uri) } catch { return false }
  if (u.hash) return false
  if (u.protocol === 'https:') return true
  if (u.protocol === 'http:') return u.hostname === 'localhost' || u.hostname === '127.0.0.1' || u.hostname === '[::1]'
  return !['javascript:', 'data:', 'file:', 'vbscript:', 'about:', 'blob:', 'ftp:'].includes(u.protocol)
}

export async function registerClient(name: string, redirectUris: string[]) {
  if (!redirectUris.length || redirectUris.length > 10 || !redirectUris.every(validRedirect)) throw new Error('invalid_redirect_uri')
  const clientId = `mcp_${randomBytes(18).toString('base64url')}`
  const safeName = name.replace(/[\u0000-\u001f]/g, '').trim().slice(0, 80) || 'An AI app'
  await getSql()`INSERT INTO public.oauth_clients (client_id, name, redirect_uris) VALUES (${clientId}, ${safeName}, ${redirectUris})`
  return { clientId, name: safeName }
}

export async function findClient(clientId: string, redirectUri: string) {
  const [c] = await getSql()<{ name: string; redirect_uris: string[] }[]>`SELECT name, redirect_uris FROM public.oauth_clients WHERE client_id = ${clientId} LIMIT 1`
  // The redirect must match exactly what was registered, or a code could be sent somewhere else.
  return c && c.redirect_uris.includes(redirectUri) ? { name: c.name } : null
}

export async function createCode(input: { clientId: string; userId: string; org: string; redirectUri: string; challenge: string; canRecord: boolean }) {
  const code = randomBytes(32).toString('base64url')
  await getSql()`
    INSERT INTO public.oauth_codes (code_hash, client_id, user_id, organization_id, redirect_uri, code_challenge, can_record, expires_at)
    VALUES (${hash(code)}, ${input.clientId}, ${input.userId}::uuid, ${input.org}::uuid, ${input.redirectUri}, ${input.challenge}, ${input.canRecord}, now() + interval '5 minutes')
  `
  return code
}

export function pkceMatches(verifier: string, challenge: string) {
  const computed = Buffer.from(sha256(verifier).toString('base64url'))
  const expected = Buffer.from(challenge)
  return computed.length === expected.length && timingSafeEqual(computed, expected)
}

/** Each code works once. It's claimed before the verifier is checked, so a wrong guess burns it too. */
export async function exchangeCode(input: { code: string; clientId: string; redirectUri: string; verifier: string }) {
  const sql = getSql()
  const [row] = await sql<{ user_id: string; organization_id: string; code_challenge: string; redirect_uri: string; client_id: string; can_record: boolean; name: string }[]>`
    UPDATE public.oauth_codes c SET used_at = now()
    FROM public.oauth_clients k
    WHERE c.code_hash = ${hash(input.code)} AND c.used_at IS NULL AND c.expires_at > now() AND k.client_id = c.client_id
    RETURNING c.user_id::text, c.organization_id::text, c.code_challenge, c.redirect_uri, c.client_id, c.can_record, k.name
  `
  if (!row || row.client_id !== input.clientId || row.redirect_uri !== input.redirectUri || !pkceMatches(input.verifier, row.code_challenge)) return null
  const { token } = await createToken(row.user_id, row.organization_id, row.name, row.can_record)
  return token
}
