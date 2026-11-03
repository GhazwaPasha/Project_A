import { NextResponse } from 'next/server'

/** How AI apps discover sign-in. Served at /.well-known/* through a rewrite in next.config.js. */
export async function GET(req: Request, ctx: { params: Promise<{ kind: string }> }) {
  const { kind } = await ctx.params
  const origin = new URL(req.url).origin
  if (kind === 'protected-resource') {
    return NextResponse.json({ resource: `${origin}/api/mcp`, authorization_servers: [origin], bearer_methods_supported: ['header'] })
  }
  if (kind === 'authorization-server') {
    return NextResponse.json({
      issuer: origin,
      authorization_endpoint: `${origin}/oauth/authorize`,
      token_endpoint: `${origin}/api/oauth/token`,
      registration_endpoint: `${origin}/api/oauth/register`,
      response_types_supported: ['code'],
      grant_types_supported: ['authorization_code'],
      code_challenge_methods_supported: ['S256'],
      token_endpoint_auth_methods_supported: ['none'],
    })
  }
  return NextResponse.json({ error: 'Not found' }, { status: 404 })
}
