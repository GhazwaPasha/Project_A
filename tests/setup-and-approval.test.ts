import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { ORG, OTHER_ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { BooksServiceAdmin as B } from '../src/server/books/service'
import { STARTER_CHART } from '../src/server/books/starter-chart'
import { approveProposal, createProposal, recordDirectly } from '../src/server/agent/proposals'

let db: Awaited<ReturnType<typeof startDatabase>>
const SECOND = '00000000-0000-4000-8000-000000000002'
const as = <T>(fn: () => Promise<T>, user = USER) => actingUserStore.run(user, fn)
const id = async (code: string) => Number((await db.sql`SELECT id FROM public.accounts WHERE organization_id = ${ORG}::uuid AND code = ${code}`)[0].id)
const why = { explanation: 'Test', confidence: 'high' as const }

before(async () => {
  db = await startDatabase()
  await db.sql`INSERT INTO public.user_profiles (id, email, full_name) VALUES (${SECOND}::uuid, 's@example.com', 'Second')`
  for (const u of [USER, SECOND]) await db.sql`INSERT INTO public.organization_members (id, organization_id, user_id, role, is_active) VALUES (gen_random_uuid(), ${ORG}::uuid, ${u}::uuid, 'organization_owner', true)`
})
after(async () => { await db.stop() })

test('the starter chart is added once, fully classified, and works with the reports', async () => {
  const r = await as(() => B.applyStarterChart(ORG))
  assert.equal(r.added, STARTER_CHART.length)
  await assert.rejects(as(() => B.applyStarterChart(ORG)), /already has accounts/)
  const [ar] = await db.sql`SELECT system_role, is_control FROM public.accounts WHERE organization_id = ${ORG}::uuid AND code = '1200'`
  assert.deepEqual({ ...ar }, { system_role: 'receivable', is_control: true })
  const [s] = await db.sql`SELECT a.code FROM public.inventory_settings s JOIN public.accounts a ON a.id = s.grni_account_id WHERE s.organization_id = ${ORG}::uuid`
  assert.equal(s.code, '2050')
  const cash = await as(() => B.cashAccounts(ORG))
  assert.deepEqual(cash.accounts.map((c) => c.code), ['1000', '1010'])
  assert.equal(cash.guessed, false)
  // Another organization's chart is untouched.
  const [{ n }] = await db.sql`SELECT COUNT(*)::int AS n FROM public.accounts WHERE organization_id = ${OTHER_ORG}::uuid`
  assert.equal(n, 0)
})

test('with a second approver required, the person who asked cannot approve, and AI apps cannot record directly', async () => {
  const lines = [{ account_id: await id('6100'), debit: 700, credit: 0 }, { account_id: await id('1010'), debit: 0, credit: 700 }]
  await db.sql`UPDATE public.organizations SET settings = ${db.sql.json({ accountingSettings: { requireSecondApprover: true } })} WHERE id = ${ORG}::uuid`
  const p = await createProposal(USER, ORG, 'app', null, { date: '2026-06-02', description: 'Rent', lines, ...why })
  await assert.rejects(approveProposal(USER, ORG, p.id), /second person/)
  const entry = await approveProposal(SECOND, ORG, p.id)
  assert.match(entry.entry_number, /^JNL-/)
  await assert.rejects(recordDirectly(USER, ORG, { date: '2026-06-03', description: 'Rent', lines, not_a_duplicate: true, ...why }), /recording directly is off/)
})
