import { readFileSync } from 'node:fs'
import path from 'node:path'
import { PGlite } from '@electric-sql/pglite'
import { PGLiteSocketServer } from '@electric-sql/pglite-socket'
import { getSql } from './pg'

const MIGRATIONS = ['003_core_multitenant_user_org', '004_ledger_core', '005_account_report_category', '005_inventory_vouchers', '006_supplier_tables', '002_voucher_attachments_file_data', '007_accounts_report_category', '008_agent_proposals_mcp_tokens', '009_accounting_modules', '010_advanced_inventory', '011_inventory_depth']

export const USER = '00000000-0000-4000-8000-000000000001'
export const ORG = '00000000-0000-4000-8000-0000000000aa'
export const OTHER_ORG = '00000000-0000-4000-8000-0000000000bb'

/** A real Postgres in memory with the app's own migrations. Nothing here touches any real database. */
export async function startDatabase() {
  const db = new PGlite()
  const port = 20000 + Math.floor(Math.random() * 20000)
  process.env.DATABASE_URL = `postgres://postgres:postgres@127.0.0.1:${port}/postgres?sslmode=disable`
  await db.exec('CREATE ROLE authenticated NOLOGIN; CREATE ROLE anon NOLOGIN; CREATE ROLE service_role NOLOGIN;').catch(() => {})
  for (const name of MIGRATIONS) await db.exec(readFileSync(path.join(process.cwd(), 'database/migrations_v2', `${name}.sql`), 'utf8'))
  await db.exec(`
    INSERT INTO public.user_profiles (id, email, full_name) VALUES ('${USER}', 't@example.com', 'Test');
    INSERT INTO public.organizations (id, name) VALUES ('${ORG}', 'Test Org'), ('${OTHER_ORG}', 'Other Org');
  `)
  const server = new PGLiteSocketServer({ db, port, host: '127.0.0.1' })
  await server.start()
  const sql = getSql()
  return { sql, stop: async () => { await sql.end({ timeout: 1 }).catch(() => {}); await server.stop(); await db.close().catch(() => {}) } }
}

export async function account(code: string, name: string, type: string, options: { postable?: boolean; org?: string } = {}) {
  const [row] = await getSql()`INSERT INTO public.accounts (organization_id, code, name, account_type, is_postable, is_active) VALUES (${options.org ?? ORG}::uuid, ${code}, ${name}, ${type}::public.account_type, ${options.postable ?? true}, true) RETURNING id`
  return Number(row.id)
}
