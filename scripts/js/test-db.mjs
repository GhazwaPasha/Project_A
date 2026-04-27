import { config } from 'dotenv'
import path from 'path'
import { fileURLToPath } from 'url'
import postgres from 'postgres'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const repoRoot = path.join(__dirname, '..', '..')
config({ path: path.join(repoRoot, '.env') })
config({ path: path.join(repoRoot, '.env.local') })

const u = process.env.DATABASE_URL
if (!u) {
  console.error('DATABASE_URL missing')
  process.exit(1)
}
try {
  const { hostname } = new URL(u)
  if (hostname.includes('apirest')) {
    console.error(
      'Wrong host: "apirest" is not the Postgres endpoint. Neon → Connect → use the normal pooled connection string.'
    )
    process.exit(3)
  }
} catch {
  /* non-URL form */
}

const sql = postgres(u, { max: 1, ssl: 'require', connect_timeout: 20 })
try {
  const r = await sql`SELECT 1 AS ok`
  console.log('db_ok', r)
  await sql.end()
  process.exit(0)
} catch (e) {
  console.error('db_fail', e.code, e.message)
  process.exit(2)
}
