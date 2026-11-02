import { NextResponse } from 'next/server'
import { z } from 'zod/v4'
import { authInApiRoute } from '@/auth'
import { llmConfig, runAgent } from '@/server/agent/llm'
import { AGENT_INSTRUCTIONS, toolsFor, type ToolContext } from '@/server/agent/tools'
import { authorizeAppDataCall } from '@/server/app-data-authorize'

export const runtime = 'nodejs'
export const maxDuration = 60

const Body = z.object({
  org: z.string().uuid(),
  screen: z.string().max(60),
  mode: z.enum(['simple', 'accountant']),
  currency: z.string().max(8),
  today: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  messages: z.array(z.object({ role: z.enum(['user', 'assistant']), text: z.string().min(1).max(8000) })).min(1).max(30),
})

export async function POST(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })

  const parsed = Body.safeParse(await req.json().catch(() => null))
  if (!parsed.success || parsed.data.messages.at(-1)?.role !== 'user') {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 })
  }
  const { org, screen, mode, currency, today, messages } = parsed.data
  const userId = session.user.id

  try {
    await authorizeAppDataCall('DataService', 'getAccounts', [org, false], userId)
  } catch {
    return NextResponse.json({ error: 'Your role does not include the agent for this organization.' }, { status: 403 })
  }
  const config = llmConfig()
  if (!config) {
    return NextResponse.json({ error: 'The agent is not set up yet. Choose an AI provider in the server settings.', code: 'AGENT_NOT_CONFIGURED' }, { status: 503 })
  }

  const encoder = new TextEncoder()
  const stream = new ReadableStream({
    async start(controller) {
      const send = (event: object) => controller.enqueue(encoder.encode(`${JSON.stringify(event)}\n`))
      const ctx: ToolContext = {
        userId,
        org,
        source: 'app',
        sourceName: null,
        canRecord: false,
        onStatus: (text) => send({ type: 'status', text }),
        onProposal: (proposal) => send({ type: 'proposal', proposal }),
      }
      try {
        await runAgent({
          config,
          system: `${AGENT_INSTRUCTIONS}\n\nContext: today is ${today}; currency ${currency}; the person is on the ${screen} screen; mode is ${mode}.`,
          messages: messages.map((m) => ({ role: m.role, content: m.text })),
          tools: toolsFor(ctx),
          ctx,
          onText: (text) => send({ type: 'text', text }),
          signal: req.signal,
        })
        send({ type: 'done' })
      } catch (e) {
        console.error('agent error', e instanceof Error ? e.message : e)
        send({ type: 'error', message: "Something went wrong and I couldn't finish. Nothing was recorded." })
      } finally {
        controller.close()
      }
    },
  })
  return new Response(stream, { headers: { 'Content-Type': 'application/x-ndjson', 'Cache-Control': 'no-store' } })
}
