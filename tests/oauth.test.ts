import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { createHash, randomBytes } from 'node:crypto'
import { ORG, startDatabase, USER } from './helpers/db'
import { createCode, exchangeCode, findClient, registerClient, validRedirect } from '../src/server/mcp/oauth'
import { principalFromRequest } from '../src/server/mcp/tokens'
import { allowRequest } from '../src/server/rate-limit'
import { toolsFor } from '../src/server/agent/tools'

let db: Awaited<ReturnType<typeof startDatabase>>
before(async () => { db = await startDatabase() })
after(async () => { await db.stop() })

const REDIRECT = 'https://app.example.com/callback'
const issue = async () => {
  const { clientId } = await registerClient('Test App', [REDIRECT])
  const verifier = randomBytes(32).toString('base64url')
  const challenge = createHash('sha256').update(verifier).digest('base64url')
  const code = await createCode({ clientId, userId: USER, org: ORG, redirectUri: REDIRECT, challenge, canRecord: false })
  return { clientId, code, verifier }
}

test('dangerous redirects are refused at registration', async () => {
  for (const bad of ['javascript:alert(1)', 'data:text/html,x', 'http://evil.example.com/cb', 'file:///etc/passwd', 'https://x.example.com/#frag', 'not a url']) {
    assert.equal(validRedirect(bad), false, bad)
    await assert.rejects(() => registerClient('x', [bad]))
  }
  for (const ok of ['https://a.example.com/cb', 'http://localhost:3334/cb', 'http://127.0.0.1:1/cb', 'cursor://anysphere/cb']) assert.equal(validRedirect(ok), true, ok)
})
test('the redirect must match exactly what was registered', async () => {
  const { clientId } = await registerClient('App', [REDIRECT])
  assert.ok(await findClient(clientId, REDIRECT))
  assert.equal(await findClient(clientId, `${REDIRECT}/extra`), null)
  assert.equal(await findClient('nope', REDIRECT), null)
})
test('the full flow gives a working token, limited to propose-only by default', async () => {
  const { clientId, code, verifier } = await issue()
  const token = await exchangeCode({ code, clientId, redirectUri: REDIRECT, verifier })
  assert.match(String(token), /^acct_/)
  const who = await principalFromRequest(new Request('http://x/api/mcp', { headers: { authorization: `Bearer ${token}` } }))
  assert.deepEqual([who?.userId, who?.org, who?.canRecord, who?.name], [USER, ORG, false, 'Test App'])
})
test('a code works only once', async () => {
  const { clientId, code, verifier } = await issue()
  assert.ok(await exchangeCode({ code, clientId, redirectUri: REDIRECT, verifier }))
  assert.equal(await exchangeCode({ code, clientId, redirectUri: REDIRECT, verifier }), null)
})
test('a wrong verifier, client or redirect gets nothing, and burns the code', async () => {
  const a = await issue()
  assert.equal(await exchangeCode({ code: a.code, clientId: a.clientId, redirectUri: REDIRECT, verifier: 'wrong'.repeat(10) }), null)
  assert.equal(await exchangeCode({ code: a.code, clientId: a.clientId, redirectUri: REDIRECT, verifier: a.verifier }), null, 'burned')
  const b = await issue()
  assert.equal(await exchangeCode({ code: b.code, clientId: 'other', redirectUri: REDIRECT, verifier: b.verifier }), null)
  const c = await issue()
  assert.equal(await exchangeCode({ code: c.code, clientId: c.clientId, redirectUri: 'https://evil.example.com/cb', verifier: c.verifier }), null)
})
test('an expired code gets nothing', async () => {
  const { clientId, code, verifier } = await issue()
  await db.sql`UPDATE public.oauth_codes SET expires_at = now() - interval '1 minute'`
  assert.equal(await exchangeCode({ code, clientId, redirectUri: REDIRECT, verifier }), null)
})
test('codes are stored only as hashes', async () => {
  const { code } = await issue()
  const rows = await db.sql`SELECT code_hash FROM public.oauth_codes`
  assert.ok(rows.every((r) => r.code_hash !== code))
})
test('rate limits count per key and stop at the limit', async () => {
  const results: boolean[] = []
  for (let i = 0; i < 4; i++) results.push(await allowRequest('test-key', 3))
  assert.deepEqual(results, [true, true, true, false])
  assert.equal(await allowRequest('other-key', 3), true)
})
test('tools: recording stays hidden unless allowed, and people keep the final say', () => {
  const names = toolsFor({ canRecord: false }).map((t) => t.name)
  assert.ok(!names.includes('record_journal_entry'))
  assert.ok(toolsFor({ canRecord: true }).some((t) => t.name === 'record_journal_entry'))
  for (const n of ['draft_document', 'get_aged_report', 'get_tax_summary', 'get_bank_reconciliation', 'get_budget_report', 'get_forecast', 'get_period_status']) assert.ok(names.includes(n), n)
  for (const forbidden of ['post_document', 'record_payment', 'close_books', 'reverse_entry']) assert.ok(!names.includes(forbidden), forbidden)
})
