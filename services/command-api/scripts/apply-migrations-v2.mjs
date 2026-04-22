#!/usr/bin/env node
/**
 * Apply numbered SQL files under database/migrations_v2/ in lexical order.
 * Run from repo root or from this package:
 *   cd services/command-api && npm run migrate:v2
 *
 * Loads repo root `.env` then requires DATABASE_URL.
 */
import { config } from 'dotenv'
import { readdir, readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'
import postgres from 'postgres'

const __dirname = dirname(fileURLToPath(import.meta.url))
config({ path: join(__dirname, '..', '..', '..', '.env') })
const packageRoot = join(__dirname, '..')
const repoRoot = join(packageRoot, '..', '..')
const migrationsDir = join(repoRoot, 'database', 'migrations_v2')

const url = process.env.DATABASE_URL
if (!url) {
  console.error('DATABASE_URL is required')
  process.exit(1)
}

const sql = postgres(url, { max: 1, ssl: 'require' })
try {
  const names = (await readdir(migrationsDir))
    .filter((n) => n.endsWith('.sql'))
    .sort()
  if (names.length === 0) {
    console.log('No .sql files in', migrationsDir)
    process.exit(0)
  }
  for (const name of names) {
    const path = join(migrationsDir, name)
    const body = await readFile(path, 'utf8')
    console.log('Applying', name)
    await sql.unsafe(body)
  }
  console.log('Done.')
} finally {
  await sql.end({ timeout: 5 })
}
