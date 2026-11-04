import { runTool, toolParameters, type AgentTool, type ToolContext } from '@/server/agent/tools'

/** Providers that speak the widely used OpenAI-compatible chat API. Any other can use AGENT_BASE_URL. */
const PRESETS: Record<string, { baseUrl: string; model?: string; fallbackModels?: string[]; keyEnv?: string; extra?: Record<string, unknown> }> = {
  openai: { baseUrl: 'https://api.openai.com/v1' },
  anthropic: { baseUrl: 'https://api.anthropic.com/v1' },
  google: { baseUrl: 'https://generativelanguage.googleapis.com/v1beta/openai', model: 'gemini-3.6-flash', fallbackModels: ['gemini-3.5-flash-lite', 'gemini-3.8-flash'], keyEnv: 'GOOGLE_AI_KEY' },
  // Accounting data shouldn't reach a provider that collects it, so AnyRouter is told to route around those.
  anyrouter: { baseUrl: 'https://anyrouter.dev/api/v1', model: 'anyrouter/free', keyEnv: 'ANYROUTER_API_KEY', extra: { provider: { data_collection: 'deny' } } },
  groq: { baseUrl: 'https://api.groq.com/openai/v1' },
  openrouter: { baseUrl: 'https://openrouter.ai/api/v1' },
  ollama: { baseUrl: 'http://localhost:11434/v1' },
}

export type LlmConfig = { baseUrl: string; apiKey: string; model: string; fallbackModels?: string[]; extra?: Record<string, unknown>; timeoutMs?: number }

/** Every model was over its limit, overloaded or too slow, as free tiers often are. */
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
  const fallbackModels = (preset?.fallbackModels ?? []).filter((m) => m !== model)
  return { baseUrl: baseUrl.replace(/\/$/, ''), apiKey, model, ...(fallbackModels.length ? { fallbackModels } : {}), ...(preset?.extra ? { extra: preset.extra } : {}) }
}

// extra_content carries Gemini 3's thought signature, which has to go back with the call or the next turn is refused.
type ToolCall = { id: string; type: 'function'; function: { name: string; arguments: string }; extra_content?: unknown }
export type ChatMessage =
  | { role: 'system' | 'user'; content: string }
  | { role: 'assistant'; content: string | null; tool_calls?: ToolCall[] }
  | { role: 'tool'; tool_call_id: string; content: string }

const MAX_WAIT_MS = 20_000
// A model that says nothing for this long is treated as overloaded, so there's time to try the others.
const STALL_MS = 15_000
const TRY_NEXT = [404, 429, 500, 502, 503, 504]

/** Stops a request when the caller gives up, or when nothing has arrived for a while. */
function watchdog(ms: number, outer?: AbortSignal) {
  const controller = new AbortController()
  let stalled = false
  let timer: ReturnType<typeof setTimeout>
  const touch = () => {
    clearTimeout(timer)
    timer = setTimeout(() => { stalled = true; controller.abort() }, ms)
  }
  const onOuter = () => controller.abort()
  outer?.addEventListener('abort', onOuter)
  touch()
  return { signal: controller.signal, touch, stalled: () => stalled, stop: () => { clearTimeout(timer); outer?.removeEventListener('abort', onOuter) } }
}

/**
 * Asks each model in turn until one answers, and stays with it for the rest of the question by dropping those that
 * failed. Only the last one left is waited for, since moving on is quicker than waiting out a limit.
 */
async function request(config: LlmConfig, models: string[], messages: ChatMessage[], tools: AgentTool[], signal?: AbortSignal) {
  const stallMs = config.timeoutMs ?? STALL_MS
  const send = async (model: string) => {
    const dog = watchdog(stallMs, signal)
    try {
      const res = await fetch(`${config.baseUrl}/chat/completions`, {
        method: 'POST',
        signal: dog.signal,
        headers: { 'Content-Type': 'application/json', ...(config.apiKey ? { Authorization: `Bearer ${config.apiKey}` } : {}) },
        body: JSON.stringify({
          ...config.extra,
          model,
          stream: true,
          messages,
          tools: tools.map((t) => ({ type: 'function', function: { name: t.name, description: t.description, parameters: toolParameters(t) } })),
        }),
      })
      return { res, dog }
    } catch (e) {
      dog.stop()
      if (dog.stalled()) return { res: null, dog }
      throw e
    }
  }
  for (;;) {
    const model = models[0]
    const last = models.length === 1
    let { res, dog } = await send(model)
    if (last && res?.status === 429) {
      dog.stop()
      const header = res.headers.get('Retry-After')
      const waitMs = (header === null || Number.isNaN(Number(header)) ? 5 : Number(header)) * 1000
      if (waitMs > MAX_WAIT_MS) throw new ProviderBusyError('Provider limit reached.')
      await new Promise((r) => setTimeout(r, waitMs))
      ;({ res, dog } = await send(model))
    }
    if (res && !TRY_NEXT.includes(res.status)) return { res, dog }
    dog.stop()
    console.warn('agent model unavailable', model, res?.status ?? 'no response')
    // A model that's gone (404) with nothing left to try is a setup problem, not a busy one, so it falls through as an error.
    if (last && res?.status !== 404) throw new ProviderBusyError('No model available.')
    if (last && res) return { res, dog }
    models.shift()
  }
}

/** One streamed model turn: passes text along as it arrives and assembles any tool calls. */
async function modelTurn(config: LlmConfig, models: string[], messages: ChatMessage[], tools: AgentTool[], onText: (t: string) => void, signal?: AbortSignal) {
  const { res, dog } = await request(config, models, messages, tools, signal)
  if (!res.ok || !res.body) {
    dog.stop()
    const detail = (await res.text().catch(() => '')).slice(0, 300)
    throw new Error(`Provider returned ${res.status}: ${detail}`)
  }

  let text = ''
  const calls: ToolCall[] = []
  const reader = res.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ''
  for (;;) {
    const { value, done } = await reader.read().catch((e) => {
      if (dog.stalled()) throw new ProviderBusyError('The model stopped responding.')
      throw e
    })
    if (done) break
    dog.touch()
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
  dog.stop()
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
  /** Stop in time to tell the person, before the server is cut off without a word. */
  deadlineMs?: number
}) {
  const stop = new AbortController()
  let late = false
  const timer = args.deadlineMs ? setTimeout(() => { late = true; stop.abort() }, args.deadlineMs) : null
  const onCancel = () => stop.abort()
  args.signal?.addEventListener('abort', onCancel)
  try {
    await agentLoop(args, stop.signal, () => late)
  } catch (e) {
    if (late) throw new ProviderBusyError('Took too long.')
    throw e
  } finally {
    if (timer) clearTimeout(timer)
    args.signal?.removeEventListener('abort', onCancel)
  }
}

async function agentLoop(args: Parameters<typeof runAgent>[0], signal: AbortSignal, late: () => boolean) {
  const history: ChatMessage[] = [{ role: 'system', content: args.system }, ...args.messages]
  const models = [args.config.model, ...(args.config.fallbackModels ?? [])]
  for (let turn = 0; turn < MAX_TURNS; turn++) {
    if (late()) throw new ProviderBusyError('Took too long.')
    const { text, calls } = await modelTurn(args.config, models, history, args.tools, args.onText, signal)
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
