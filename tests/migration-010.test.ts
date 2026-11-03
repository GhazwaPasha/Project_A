import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import path from 'node:path'
import { PGlite } from '@electric-sql/pglite'

const BEFORE = ['003_core_multitenant_user_org', '004_ledger_core', '005_account_report_category', '005_inventory_vouchers', '006_supplier_tables', '002_voucher_attachments_file_data', '007_accounts_report_category', '008_agent_proposals_mcp_tokens', '009_accounting_modules']
const file = (name: string) => readFileSync(path.join(process.cwd(), 'database/migrations_v2', `${name}.sql`), 'utf8')
const ORG = '00000000-0000-4000-8000-0000000000aa'
const EMPTY_ORG = '00000000-0000-4000-8000-0000000000bb'

test('migrations 010 and 011 move existing stock into Main, change no totals, keep moving average, and can run twice', async () => {
  const db = new PGlite()
  await db.exec('CREATE ROLE authenticated NOLOGIN; CREATE ROLE anon NOLOGIN; CREATE ROLE service_role NOLOGIN;').catch(() => {})
  for (const name of BEFORE) await db.exec(file(name))
  await db.exec(`
    INSERT INTO public.organizations (id, name) VALUES ('${ORG}', 'Has stock'), ('${EMPTY_ORG}', 'No stock');
    INSERT INTO public.accounts (id, organization_id, code, name, account_type, is_postable, is_active) OVERRIDING SYSTEM VALUE VALUES (1, '${ORG}', '1300', 'Inventory', 'asset', true, true), (2, '${ORG}', '5000', 'Cost', 'expense', true, true);
    INSERT INTO public.inventory_categories (id, organization_id, name, inventory_account_id, expense_account_id) OVERRIDING SYSTEM VALUE VALUES (1, '${ORG}', 'Goods', 1, 2);
    INSERT INTO public.inventory_items (id, organization_id, category_id, sku, name, quantity_available, average_unit_cost, total_value) OVERRIDING SYSTEM VALUE VALUES (1, '${ORG}', 1, 'A', 'Has stock', 7, 3, 21), (2, '${ORG}', 1, 'B', 'None left', 0, 3, 0);
    INSERT INTO public.inventory_transactions (organization_id, item_id, transaction_type, quantity, transaction_date) VALUES ('${ORG}', 1, 'in', 7, '2026-01-01');
  `)
  const totals = async () => (await db.query('SELECT id, quantity_available::float AS q, total_value::float AS v, average_unit_cost::float AS a FROM public.inventory_items ORDER BY id')).rows
  const before = await totals()
  await db.exec(file('010_advanced_inventory'))
  await db.exec(file('010_advanced_inventory'))
  await db.exec(file('011_inventory_depth'))
  await db.exec(file('011_inventory_depth'))
  assert.deepEqual(await totals(), before, 'item totals untouched')
  const warehouses = (await db.query<{ organization_id: string; name: string; is_default: boolean }>('SELECT organization_id, name, is_default FROM public.warehouses')).rows
  assert.deepEqual(warehouses, [{ organization_id: ORG, name: 'Main', is_default: true }], 'one Main, and none for an organization with no items')
  const levels = (await db.query<{ item_id: string; quantity: number }>('SELECT item_id, quantity::float AS quantity FROM public.stock_levels ORDER BY item_id')).rows
  assert.deepEqual(levels.map((l) => [Number(l.item_id), l.quantity]), [[1, 7], [2, 0]])
  const [t] = (await db.query<{ warehouse_id: string | null }>('SELECT warehouse_id FROM public.inventory_transactions')).rows
  assert.ok(t.warehouse_id, 'old movements know their warehouse')
  await db.exec(`INSERT INTO public.inventory_transactions (organization_id, item_id, transaction_type, quantity, transaction_date) VALUES ('${ORG}', 1, 'transfer_in', 1, '2026-01-02')`)
  const methods = (await db.query<{ costing_method: string; track_serials: boolean }>('SELECT DISTINCT costing_method, track_serials FROM public.inventory_items')).rows
  assert.deepEqual(methods, [{ costing_method: 'average', track_serials: false }])
  await db.close()
})
