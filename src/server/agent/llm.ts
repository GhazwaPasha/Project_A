import { runTool, toolParameters, type AgentTool, type ToolContext } from '@/server/agent/tools'

/** Providers that speak the widely used OpenAI-compatible chat API. Any other can use AGENT_BASE_URL. */
const PRESETS: Record<string, { baseUrl: string; model?: string; keyEnv?: string; extra?: Record<string, unknown> }> = {
  openai: { baseUrl: 'https://api.openai.com/v1' },
  anthropic: { baseUrl: 'https://api.anthropic.com/v1' },
  google: { baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai', model: 'gemini-3.8-flash', keyEnv: 'GOOGLE_AI_KEY' },
  // Accounting data shouldn't reach a provider that collects it, so AnyRouter is told to route around those.
  anyrouter: { baseUrl: 'https://anyrouter.dev/api/v1', model: 'anyrouter/free', keyEnv: 'ANYROUTER_API_KEY', extra: { provider: { data_collection: 'deny' } } },
  groq: { baseUrl: 'https://api.groq.com/openai/v1' },
  openrouter: { baseUrl: 'https://openrouter.ai/api/v1' },
  ollama: { baseUrl: 'http://localhost:11434/v1' },
}

export type LlmConfig = { baseUrl: string; apiKey: string; model: string; extra?: Record<string, unknown> }

/** The provider's limit was hit and waiting didn't help, as free tiers do. */
export class ProviderBusyError extends Error {}

/** Reads the provider from the environment. Returns null when nothing usable is set. */
export function llmConfig(env: Record<string, string | undefined> = process.env): LlmConfig | null {
  const provider = env.AGENT_PROVIDER?.trim().toLowerCase() || (env.GOOGLE_AI_KEY ? 'google' : env.ANYROUTER_API_KEY ? 'anyrouter' : '')
  const preset = PRESETS[provider]
  const baseUrl = env.AGENT_BASE_URL?.trim() || preset?.baseUrl
  const model = env.AGENT_MODEL?.trim() || preset?.model
  const apiKey = env.AGENT_API_KEY?.trim() || (preset?.keyEnv ? env[preset.keyEnv]?.trim() : '') || ''
  if (!baseUrl || !model) return null
  if (!apiKey && provider !== 'ollama') return null
  return { baseUrl: baseUrl.replace(/\/$/, ''), apiKey, model, ...(preset?.extra ? { extra: preset.extra } : {}) }
}

// extra_content carries Gemini 3's thought signature, which has to go back with the call or the next turn is refused.
type ToolCall = { id: string; type: 'function'; function: { name: string; arguments: string }; extra_content?: unknown }
export type ChatMessage =
  | { role: 'system' | 'user'; content: string }
  | { role: 'assistant'; content: string | null; tool_calls?: ToolCall[] }
  | { role: 'tool'; tool_call_id: string; content: string }

const MAX_WAIT_MS = 20_000

/** Asks the provider, waiting once if it says it's over its limit. A longer wait isn't worth holding someone's question for. */
async function request(config: LlmConfig, messages: ChatMessage[], tools: AgentTool[], signal?: AbortSignal) {
  const send = () => fetch(`${config.baseUrl}/chat/completions`, {
    method: 'POST',
    signal,
    headers: { 'Content-Type': 'application/json', ...(config.apiKey ? { Authorization: `Bearer ${config.apiKey}` } : {}) },
    body: JSON.stringify({
      ...config.extra,
      model: config.model,
      stream: true,
      messages,
      tools: tools.map((t) => ({ type: 'function', function: { name: t.name, description: t.description, parameters: toolParameters(t) } })),
    }),
  })
  const first = await send()
  if (first.status !== 429) return first
  const header = first.headers.get('Retry-After')
  const waitMs = (header === null || Number.isNaN(Number(header)) ? 5 : Number(header)) * 1000
  if (waitMs > MAX_WAIT_MS) throw new ProviderBusyError('Provider limit reached.')
  await new Promise((r) => setTimeout(r, waitMs))
  const second = await send()
  if (second.status === 429) throw new ProviderBusyError('Provider limit reached.')
  return second
}

/** One streamed model turn: passes text along as it arrives and assembles any tool calls. */
async function modelTurn(config: LlmConfig, messages: ChatMessage[], tools: AgentTool[], onText: (t: string) => void, signal?: AbortSignal) {
  const res = await request(config, messages, tools, signal)
  if (!res.ok || !res.body) {
    const detail = (await res.text().catch(() => '')).slice(0, 300)
    throw new Error(`Provider returned ${res.status}: ${detail}`)
  }

  let text = ''
  const calls: ToolCall[] = []
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += value
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      const data = line.startsWith('data:') ? line.slice(5).trim() : ''
      if (!data || data === '[DONE]') continue
      const delta = JSON.parse(data).choices?.[0]?.delta
      if (!delta) continue
      if (typeof delta.content === 'string' && delta.content) {
        text += delta.content
        onText(delta.content)
      }
      const deltas: { index?: number; id?: string; function?: { name?: string; arguments?: unknown }; extra_content?: unknown }[] = delta.tool_calls ?? []
      deltas.forEach((tc) => {
        // Some providers omit the index and send each call whole.
        const i = tc.index ?? calls.length
        calls[i] ??= { id: tc.id ?? `call_${i}`, type: 'function', function: { name: '', arguments: '' } }
        if (tc.id) calls[i].id = tc.id
        if (tc.extra_content) calls[i].extra_content = tc.extra_content
        if (tc.function?.name) calls[i].function.name = tc.function.name
        const args = tc.function?.arguments
        if (args != null) calls[i].function.arguments += typeof args === 'string' ? args : JSON.stringify(args)
      })
    }
  }
  return { text, calls: calls.filter(Boolean) }
}

const MAX_TURNS = 10

/** The agent loop: ask the model, run the tools it picks, repeat until it answers. */
export async function runAgent(args: {
  config: LlmConfig
  system: string
  messages: ChatMessage[]
  tools: AgentTool[]
  ctx: ToolContext
  onText: (t: string) => void
  signal?: AbortSignal
}) {
  const history: ChatMessage[] = [{ role: 'system', content: args.system }, ...args.messages]
  for (let turn = 0; turn < MAX_TURNS; turn++) {
    const { text, calls } = await modelTurn(args.config, history, args.tools, args.onText, args.signal)
    if (calls.length === 0) return
    history.push({ role: 'assistant', content: text || null, tool_calls: calls })
    const results = await Promise.all(calls.map(async (call) => {
      const tool = args.tools.find((t) => t.name === call.function.name)
      if (!tool) return { text: `Unknown tool ${call.function.name}.`, isError: true }
      let input: unknown
      try {
        input = JSON.parse(call.function.arguments || '{}')
      } catch {
        return { text: 'The tool input was not valid JSON. Try again.', isError: true }
      }
      return runTool(tool, input, args.ctx)
    }))
    calls.forEach((call, i) => history.push({ role: 'tool', tool_call_id: call.id, content: results[i].text }))
  }
  throw new Error('The agent took too many steps.')
}
