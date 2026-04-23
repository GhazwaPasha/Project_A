/**
 * Seeds two postable accounts and one balanced journal entry for E2E / local verification.
 * Usage (from web-app, with root .env loaded):
 *   node scripts/seed-ledger-e2e.mjs <organization_uuid> <user_uuid>
 *
 * Example (PowerShell):
 *   node scripts/seed-ledger-e2e.mjs "0946405f-3b8a-4fe5-8c29-125b39d9ca8e" "e1b68757-3e5c-4ca1-951c-f28c26893b96"
 */
import { config } from 'dotenv'
import path from 'path'
import { fileURLToPath } from 'url'
import postgres from 'postgres'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
config({ path: path.join(__dirname, '..', '..', '.env') })
config({ path: path.join(__dirname, '..', '.env') })

const orgId = process.argv[2]
const userId = process.argv[3]
if (!orgId || !userId) {
  console.error('Usage: node scripts/seed-ledger-e2e.mjs <organization_uuid> <user_uuid>')
  process.exit(1)
}

const url = process.env.DATABASE_URL
if (!url) {
  console.error('DATABASE_URL is not set')
  process.exit(1)
}

const sql = postgres(url, { max: 1, ssl: 'require', connect_timeout: 30, prepare: false })

try {
  await sql.begin(async (tx) => {
    const a1 = await tx`
      INSERT INTO public.accounts (
        organization_id, code, name, account_type, parent_id, description, is_active,
        "group", is_postable, created_by
      ) VALUES (
        ${orgId}::uuid, '1000', 'E2E Cash (Asset)', 'asset', null, 'seed', true, null, true, ${userId}::uuid
      )
      ON CONFLICT (organization_id, code) DO UPDATE SET name = EXCLUDED.name
      RETURNING id
    `
    const a2 = await tx`
      INSERT INTO public.accounts (
        organization_id, code, name, account_type, parent_id, description, is_active,
        "group", is_postable, created_by
      ) VALUES (
        ${orgId}::uuid, '4000', 'E2E Service Revenue', 'revenue', null, 'seed', true, null, true, ${userId}::uuid
      )
      ON CONFLICT (organization_id, code) DO UPDATE SET name = EXCLUDED.name
      RETURNING id
    `

    const id1 = a1[0].id
    const id2 = a2[0].id

    const je = await tx`
      INSERT INTO public.journal_entries (
        organization_id, entry_number, entry_date, description, reference, total_amount,
        is_posted, created_by, posted_by, posted_at
      ) VALUES (
        ${orgId}::uuid,
        ${'E2E-' + Date.now()},
        CURRENT_DATE,
        'E2E seed entry',
        'seed',
        100.0,
        true,
        ${userId}::uuid,
        ${userId}::uuid,
        NOW()
      )
      RETURNING id
    `
    const jid = je[0].id
    await tx`
      INSERT INTO public.journal_entry_lines (
        journal_entry_id, account_id, description, debit_amount, credit_amount, line_order
      ) VALUES
        (${jid}, ${id1}, 'E2E seed', 100, 0, 1),
        (${jid}, ${id2}, 'E2E seed', 0, 100, 2)
    `

    console.log('ok — accounts', id1, id2, 'journal_entry', jid)
  })
} finally {
  await sql.end()
}
