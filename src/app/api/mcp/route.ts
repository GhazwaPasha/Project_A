import { WebStandardStreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js'
import { createMcpServer } from '@/server/mcp/server'
import { principalFromRequest } from '@/server/mcp/tokens'

export const runtime = 'nodejs'
export const maxDuration = 60

const unauthorized = () => new Response(JSON.stringify({ error: 'A valid Accountuitive connection token is required.' }), {
  status: 401,
  headers: { 'Content-Type': 'application/json', 'WWW-Authenticate': 'Bearer' },
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
  if (!principal) return unauthorized()

  const server = createMcpServer({ userId: principal.userId, org: principal.org, source: 'mcp', sourceName: principal.name, canRecord: principal.canRecord })
  const transport = new WebStandardStreamableHTTPServerTransport({ sessionIdGenerator: undefined, enableJsonResponse: true })
  await server.connect(transport)
  return transport.handleRequest(req)
}

export const POST = handle
export const GET = handle
export const DELETE = handle
