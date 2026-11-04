import { afterEach, test } from 'node:test'
import assert from 'node:assert/strict'
import { z } from 'zod/v4'
import { llmConfig, ProviderBusyError, runAgent } from '../src/server/agent/llm'

const realFetch = globalThis.fetch
afterEach(() => { globalThis.fetch = realFetch })

/** Answers each request with the next canned reply, and keeps what was sent. */
function fakeProvider(replies: { status?: number; headers?: Record<string, string>; chunks?: unknown[] }[]) {
  const sent: { url: string; body: Record<string, any> }[] = [] // eslint-disable-line @typescript-eslint/no-explicit-any
  globalThis.fetch = (async (url: string, init: RequestInit) => {
    sent.push({ url, body: JSON.parse(String(init.body)) })
    const r = replies[sent.length - 1]
    const body = (r.chunks ?? []).map((c) => `data: ${JSON.stringify(c)}\n\n`).join('') + 'data: [DONE]\n\n'
    return new Response(body, { status: r.status ?? 200, headers: r.headers })
  }) as typeof fetch
  return sent
}
const tool = { name: 'get_stock', title: 'Stock', description: 'Stock', schema: z.object({}), readOnly: true, run: async () => ({ on_hand: 3 }) }
const run = (config: NonNullable<ReturnType<typeof llmConfig>>, out: string[] = []) => runAgent({ config, system: 'sys', messages: [{ role: 'user', content: 'hi' }], tools: [tool as never], ctx: { userId: 'u', org: 'o', source: 'app', sourceName: null, canRecord: false }, onText: (t) => out.push(t) })
const gemini = { baseUrl: 'https://example.test', apiKey: 'k', model: 'm' }

test('Google is used with its free model and server-only key', () => {
  const c = llmConfig({ GOOGLE_AI_KEY: 'g' })!
  assert.equal(c.baseUrl, 'https://generativelanguage.googleapis.com/v1beta/openai')
  assert.equal(c.model, 'gemini-3.6-flash')
  assert.deepEqual(c.fallbackModels, ['gemini-3.5-flash-lite', 'gemini-3.8-flash'])
  assert.equal(c.apiKey, 'g')
  assert.equal(llmConfig({ NEXT_PUBLIC_GOOGLE_AI_KEY: 'public' }), null, 'a key exposed to browsers is never used')
})

test('AnyRouter is chosen by name, asks for no data collection, and the model can be overridden', () => {
  const c = llmConfig({ AGENT_PROVIDER: 'anyrouter', GOOGLE_AI_KEY: 'g', ANYROUTER_API_KEY: 'a' })!
  assert.equal(c.baseUrl, 'https://anyrouter.dev/api/v1')
  assert.equal(c.model, 'anyrouter/free')
  assert.equal(c.apiKey, 'a')
  assert.deepEqual(c.extra, { provider: { data_collection: 'deny' } })
  assert.equal(llmConfig({ ANYROUTER_API_KEY: 'a', AGENT_MODEL: 'x/y' })!.model, 'x/y')
})

test('Mistral is gone, and nothing is set up without a key', () => {
  assert.equal(llmConfig({ MISTRAL_API_KEY: 'm' }), null)
  assert.equal(llmConfig({ AGENT_PROVIDER: 'mistral', AGENT_API_KEY: 'm' }), null)
  assert.equal(llmConfig({}), null)
})

test('Gemini 3 thought signatures go back with the tool call', async () => {
  const extra = { google: { thought_signature: 'SIG' } }
  const sent = fakeProvider([
    { chunks: [{ choices: [{ delta: { tool_calls: [{ index: 0, id: 'c1', type: 'function', extra_content: extra, function: { name: 'get_stock', arguments: '{}' } }] } }] }] },
    { chunks: [{ choices: [{ delta: { content: 'You have 3.' } }] }] },
  ])
  const out: string[] = []
  await run(gemini, out)
  const back = sent[1].body.messages.find((m: { role: string }) => m.role === 'assistant')
  assert.deepEqual(back.tool_calls[0].extra_content, extra)
  assert.equal(back.tool_calls[0].id, 'c1')
  assert.equal(out.join(''), 'You have 3.')
})

test('settings like data_collection are sent with the request', async () => {
  const sent = fakeProvider([{ chunks: [{ choices: [{ delta: { content: 'ok' } }] }] }])
  await run({ ...gemini, extra: { provider: { data_collection: 'deny' } } })
  assert.deepEqual(sent[0].body.provider, { data_collection: 'deny' })
})

test('a free-tier limit waits and retries once, then says it is busy', async () => {
  const ok = { chunks: [{ choices: [{ delta: { content: 'ok' } }] }] }
  const limited = { status: 429, headers: { 'Retry-After': '0' } }
  const sent = fakeProvider([limited, ok])
  await run(gemini)
  assert.equal(sent.length, 2)
  fakeProvider([limited, limited])
  await assert.rejects(() => run(gemini), ProviderBusyError)
})

const answer = { chunks: [{ choices: [{ delta: { content: 'ok' } }] }] }
const withBackups = { ...gemini, fallbackModels: ['b', 'c'] }

test('an overloaded model moves on to the next, and a retired one too', async () => {
  const sent = fakeProvider([{ status: 503 }, { status: 404 }, answer])
  const out: string[] = []
  await run(withBackups, out)
  assert.deepEqual(sent.map((s) => s.body.model), ['m', 'b', 'c'])
  assert.equal(out.join(''), 'ok')
})

test('the model that answered stays for the rest of the question', async () => {
  const sent = fakeProvider([
    { status: 503 },
    { chunks: [{ choices: [{ delta: { tool_calls: [{ index: 0, id: 'c1', type: 'function', function: { name: 'get_stock', arguments: '{}' } }] } }] }] },
    answer,
  ])
  await run(withBackups)
  assert.deepEqual(sent.map((s) => s.body.model), ['m', 'b', 'b'])
})

test('when every model is busy it says so instead of failing oddly', async () => {
  fakeProvider([{ status: 503 }, { status: 429 }, { status: 503 }])
  await assert.rejects(() => run(withBackups), ProviderBusyError)
})

test('a model that says nothing is given up on, and the next one answers', async () => {
  const seen: string[] = []
  globalThis.fetch = (async (_url: string, init: RequestInit) => {
    const model = JSON.parse(String(init.body)).model
    seen.push(model)
    if (model === 'm') return new Promise((_ok, fail) => init.signal?.addEventListener('abort', () => fail(new DOMException('aborted', 'AbortError'))))
    return new Response(`data: ${JSON.stringify(answer.chunks[0])}\n\ndata: [DONE]\n\n`)
  }) as typeof fetch
  const out: string[] = []
  await run({ ...withBackups, timeoutMs: 20 }, out)
  assert.deepEqual(seen, ['m', 'b'])
  assert.equal(out.join(''), 'ok')
})

test('a person cancelling is not treated as a busy model', async () => {
  const seen: string[] = []
  globalThis.fetch = (async (_url: string, init: RequestInit) => {
    seen.push(JSON.parse(String(init.body)).model)
    return new Promise((_ok, fail) => init.signal?.addEventListener('abort', () => fail(new DOMException('aborted', 'AbortError'))))
  }) as typeof fetch
  const stop = new AbortController()
  const running = runAgent({ config: { ...withBackups, timeoutMs: 5000 }, system: 's', messages: [{ role: 'user', content: 'hi' }], tools: [tool as never], ctx: { userId: 'u', org: 'o', source: 'app', sourceName: null, canRecord: false }, onText: () => {}, signal: stop.signal })
  setTimeout(() => stop.abort(), 10)
  await assert.rejects(running, (e: Error) => !(e instanceof ProviderBusyError))
  assert.deepEqual(seen, ['m'])
})

test('a question that runs too long stops in time to say so', async () => {
  globalThis.fetch = (async (_url: string, init: RequestInit) => new Promise((_ok, fail) => init.signal?.addEventListener('abort', () => fail(new DOMException('aborted', 'AbortError'))))) as typeof fetch
  await assert.rejects(() => runAgent({ config: { ...gemini, timeoutMs: 5000 }, system: 's', messages: [{ role: 'user', content: 'hi' }], tools: [tool as never], ctx: { userId: 'u', org: 'o', source: 'app', sourceName: null, canRecord: false }, onText: () => {}, deadlineMs: 20 }), ProviderBusyError)
})

test('other provider errors fail straight away', async () => {
  const sent = fakeProvider([{ status: 400 }])
  await assert.rejects(() => run(gemini), /Provider returned 400/)
  assert.equal(sent.length, 1)
})
