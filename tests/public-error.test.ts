import { after, before, test } from 'node:test'
import assert from 'node:assert/strict'
import { account, ORG, startDatabase, USER } from './helpers/db'
import { actingUserStore } from '../src/server/request-context'
import { DataServiceAdmin as D } from '../src/server/data-service-admin'
import { AccountServiceAdmin as A } from '../src/server/account-service-admin'
import { publicError } from '../src/server/public-error'
import { allowRequest } from '../src/server/rate-limit'

let db: Awaited<ReturnType<typeof startDatabase>>
const as = <T>(fn: () => Promise<T>) => actingUserStore.run(USER, fn)
const pg = (code: string, message = 'update or delete on table "accounts" violates foreign key at db.internal.example') => Object.assign(new Error(message), { code })

before(async () => { db = await startDatabase() })
after(async () => { await db.stop() })

test('messages the app wrote for people pass through', () => {
  assert.deepEqual(publicError(new Error('Choose a supplier.')), { status: 500, error: 'Choose a supplier.' })
})

test('database and connection errors never show tables or hosts', () => {
  for (const code of ['23503', '23001', '23505', '23502', '23514', '22P02', '42P01', '42703', '40001', 'ECONNREFUSED', 'CONNECT_TIMEOUT', 'UNDEFINED_VALUE']) {
    const shown = JSON.stringify(publicError(pg(code)))
    assert.ok(!/accounts|foreign key|db\.internal/.test(shown), `${code} leaked: ${shown}`)
  }
  assert.equal(publicError(pg('23503')).status, 409)
  assert.equal(publicError(pg('23001')).status, 409)
  assert.equal(publicError(pg('23505')).status, 409)
  assert.equal(publicError(pg('22P02')).status, 400)
  assert.equal(publicError(pg('42P01')).code, 'SCHEMA_NOT_READY')
  assert.equal(publicError(pg('ECONNREFUSED')).status, 500)
})

test('deleting something in use explains itself, and changes nothing', () => as(async () => {
  const inv = await account('1300', 'Inv', 'asset'), cogs = await account('5000', 'Cogs', 'expense')
  const [c] = await db.sql`INSERT INTO public.inventory_categories (organization_id, name, inventory_account_id, expense_account_id) VALUES (${ORG}::uuid, 'Used', ${inv}, ${cogs}) RETURNING id`
  await D.createInventoryItem({ organization_id: ORG, category_id: Number(c.id), sku: 'U', name: 'U', description: null, unit_of_measure: 'Each', quantity_in: 0, quantity_out: 0, average_unit_cost: 0, reorder_point: 0, reorder_quantity: 0, is_active: true, created_by: USER } as never)
  await assert.rejects(() => D.deleteInventoryCategory(Number(c.id)), /still has items/)
  await assert.rejects(() => D.deleteAccount(inv), /can't be deleted/)
  await assert.rejects(() => A.deleteAccount(inv), /can't be deleted/)
  assert.equal((await db.sql`SELECT COUNT(*)::int AS n FROM public.accounts WHERE id = ${inv}`)[0].n, 1)
}))

test('the rate limit counts per person and stops at the limit', async () => {
  for (let i = 0; i < 3; i++) assert.equal(await allowRequest('app-data:person-a', 3), true)
  assert.equal(await allowRequest('app-data:person-a', 3), false)
  assert.equal(await allowRequest('app-data:person-b', 3), true)
})
