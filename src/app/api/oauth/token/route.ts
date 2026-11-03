import { NextResponse } from 'next/server'
import { exchangeCode } from '@/server/mcp/oauth'
import { allowRequest, clientIp, tooMany } from '@/server/rate-limit'

const failure = (error: string, status = 400) => NextResponse.json({ error }, { status, headers: { 'Cache-Control': 'no-store' } })

/** Swaps a one-time code and its PKCE verifier for a connection token, listed and revocable under Connections. */
export async function POST(req: Request) {
  if (!(await allowRequest(`oauth-token:${clientIp(req)}`, 30))) return tooMany()
  const type = req.headers.get('content-type') ?? ''
  const raw = type.includes('json') ? await req.json().catch(() => ({})) : Object.fromEntries(new URLSearchParams(await req.text()))
  const { grant_type, code, client_id, redirect_uri, code_verifier } = raw as Record<string, string>
  if (grant_type !== 'authorization_code') return failure('unsupported_grant_type')
  if (!code || !client_id || !redirect_uri || !code_verifier) return failure('invalid_request')
  const token = await exchangeCode({ code, clientId: client_id, redirectUri: redirect_uri, verifier: code_verifier })
  if (!token) return failure('invalid_grant')
  return NextResponse.json({ access_token: token, token_type: 'Bearer' }, { headers: { 'Cache-Control': 'no-store' } })
}
