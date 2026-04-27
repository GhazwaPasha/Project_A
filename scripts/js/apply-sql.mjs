/**
 * Apply a .sql file using DATABASE_URL (root .env).
 * Usage: node scripts/apply-sql.mjs ../database/migrations_v2/003_core_multitenant_user_org.sql
 */
import { config } from 'dotenv'
import path from 'path'
import { fileURLToPath } from 'url'
import fs from 'fs'
import postgres from 'postgres'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
config({ path: path.join(__dirname, '..', '..', '.env') })
config({ path: path.join(__dirname, '..', '.env') })

const fileArg = process.argv[2]
if (!fileArg) {
  console.error('Usage: node scripts/apply-sql.mjs <path-to.sql>')
  process.exit(1)
}
const sqlPath = path.isAbsolute(fileArg)
  ? fileArg
  : path.join(__dirname, '..', '..', fileArg)
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
