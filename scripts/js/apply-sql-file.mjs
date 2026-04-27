/**
 * Apply a .sql file to Neon using DATABASE_URL (same as Next.js server).
 * Usage (from repo root): npm run db:apply-inventory
 * Or: node scripts/js/apply-sql-file.mjs path/to/file.sql
 *
 * Loads DATABASE_URL from the environment, or parses a simple KEY=value line
 * from `.env` / `.env.local` at the repository root when DATABASE_URL is unset.
 */
import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import postgres from 'postgres'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.join(__dirname, '..', '..')

function loadDatabaseUrlFromFile(filePath) {
  if (!fs.existsSync(filePath)) return false
  const raw = fs.readFileSync(filePath, 'utf8')
  for (const line of raw.split(/\r?\n/)) {
    const t = line.trim()
    if (!t || t.startsWith('#')) continue
    const m = t.match(/^DATABASE_URL=(.*)$/)
    if (!m) continue
    let v = m[1].trim()
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) {
      v = v.slice(1, -1)
    }
    process.env.DATABASE_URL = v
    return true
  }
  return false
}

if (!process.env.DATABASE_URL) {
  loadDatabaseUrlFromFile(path.join(repoRoot, '.env.local')) ||
    loadDatabaseUrlFromFile(path.join(repoRoot, '.env'))
}

const url = process.env.DATABASE_URL
if (!url) {
  console.error('DATABASE_URL is not set. Export it or add DATABASE_URL to .env / .env.local at the repo root.')
  process.exit(1)
}

const rel =
  process.argv[2] ||
  path.join('database', 'migrations_v2', '005_inventory_vouchers.sql')
const sqlFile = path.isAbsolute(rel) ? rel : path.resolve(repoRoot, rel)

if (!fs.existsSync(sqlFile)) {
  console.error('SQL file not found:', sqlFile)
  process.exit(1)
}

const body = fs.readFileSync(sqlFile, 'utf8')
const sql = postgres(url, { max: 1, ssl: 'require', prepare: false })

try {
  await sql.unsafe(body)
  console.log('OK — applied', sqlFile)
} catch (e) {
  console.error(e)
  process.exit(1)
} finally {
  await sql.end({ timeout: 5 })
}
