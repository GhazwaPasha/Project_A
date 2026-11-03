import { WebStandardStreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js'
import { createMcpServer } from '@/server/mcp/server'
import { principalFromRequest } from '@/server/mcp/tokens'
import { allowRequest, clientIp, tooMany } from '@/server/rate-limit'

export const runtime = 'nodejs'
export const maxDuration = 60

// The header points AI apps to sign-in, so a person can approve them without copying a token.
const unauthorized = (req: Request) => new Response(JSON.stringify({ error: 'A valid Accountuitive connection token is required.' }), {
  status: 401,
  headers: { 'Content-Type': 'application/json', 'WWW-Authenticate': `Bearer resource_metadata="${new URL(req.url).origin}/.well-known/oauth-protected-resource"` },
})

/** Stateless Streamable HTTP: each request authenticates and gets its own server instance. */
async function handle(req: Request) {
  let principal
  try {
    principal = await principalFromRequest(req)
  } catch (e) {
    if ((e as { code?: string })?.code === '42P01') {
      return new Response(JSON.stringify({ error: 'Connections are not set up on this database yet.' }), { status: 503, headers: { 'Content-Type': 'application/json' } })
    }
    throw e
  }
  if (!principal) {
    if (!(await allowRequest(`mcp-anon:${clientIp(req)}`, 30))) return tooMany()
    return unauthorized(req)
  }
  if (!(await allowRequest(`mcp:${principal.userId}`, 120))) return tooMany()

  const server = createMcpServer({ userId: principal.userId, org: principal.org, source: 'mcp', sourceName: principal.name, canRecord: principal.canRecord })
  const transport = new WebStandardStreamableHTTPServerTransport({ sessionIdGenerator: undefined, enableJsonResponse: true })
  await server.connect(transport)
  return transport.handleRequest(req)
}

export const POST = handle
export const GET = handle
export const DELETE = handle
