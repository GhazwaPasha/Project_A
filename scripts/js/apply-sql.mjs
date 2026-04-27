/**
 * Apply a .sql file using DATABASE_URL (repo root .env).
 * Usage (from repo root): node scripts/js/apply-sql.mjs database/migrations_v2/003_core_multitenant_user_org.sql
 */
import { config } from 'dotenv'
import path from 'path'
import { fileURLToPath } from 'url'
import fs from 'fs'
import postgres from 'postgres'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.join(__dirname, '..', '..')
config({ path: path.join(repoRoot, '.env') })
config({ path: path.join(repoRoot, '.env.local') })

const fileArg = process.argv[2]
if (!fileArg) {
  console.error('Usage: node scripts/apply-sql.mjs <path-to.sql>')
  process.exit(1)
}
const sqlPath = path.isAbsolute(fileArg) ? fileArg : path.join(repoRoot, fileArg)
const u = process.env.DATABASE_URL
if (!u) {
  console.error('DATABASE_URL missing')
  process.exit(1)
}
const file = fs.readFileSync(sqlPath, 'utf8')
const client = postgres(u, { max: 1, ssl: 'require', connect_timeout: 30, prepare: false })
try {
  await client.unsafe(file)
  console.log('applied', sqlPath)
} finally {
  await client.end()
}
