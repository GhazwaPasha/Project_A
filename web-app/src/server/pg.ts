import postgres from 'postgres'

let _sql: ReturnType<typeof postgres> | null = null

/**
 * Server-only Postgres (Neon) client. Singleton for Route Handlers / server code.
 */
export function getSql() {
  const url = process.env.DATABASE_URL
  if (!url) {
    throw new Error('DATABASE_URL is not set')
  }
  if (!_sql) {
    _sql = postgres(url, { max: 1, ssl: 'require' })
  }
  return _sql
}
