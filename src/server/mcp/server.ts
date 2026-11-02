import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js'
import { AGENT_INSTRUCTIONS, runTool, toolParameters, toolsFor, type ToolContext } from '@/server/agent/tools'

/** Exposes the agent's own tools over MCP, so any connected AI app works the same way it does. */
export function createMcpServer(ctx: ToolContext) {
  const tools = toolsFor(ctx)
  const server = new Server(
    { name: 'accountuitive', version: '1.0.0' },
    { capabilities: { tools: {} }, instructions: AGENT_INSTRUCTIONS },
  )
  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: tools.map((t) => ({
      name: t.name,
      title: t.title,
      description: t.description,
      inputSchema: toolParameters(t) as { type: 'object' },
      annotations: { title: t.title, readOnlyHint: t.readOnly, destructiveHint: false, idempotentHint: t.readOnly, openWorldHint: false },
    })),
  }))
  server.setRequestHandler(CallToolRequestSchema, async ({ params }) => {
    const tool = tools.find((t) => t.name === params.name)
    if (!tool) return { content: [{ type: 'text', text: `Unknown tool ${params.name}.` }], isError: true }
    const { text, isError } = await runTool(tool, params.arguments ?? {}, ctx)
    return { content: [{ type: 'text', text }], isError }
  })
  return server
}
