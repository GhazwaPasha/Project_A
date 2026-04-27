import postgres from 'postgres'

let _sql: ReturnType<typeof postgres> | null = null

function assertPostgresUrl(url: string) {
  try {
    const u = new URL(url)
    if (u.hostname.includes('apirest')) {
      throw new Error(
        'DATABASE_URL host looks like a Data API / wrong endpoint. In Neon: Project → Connect → use the Postgres connection string (host should look like ep-…-pooler.….neon.tech, not "apirest").'
      )
    }
  } catch (e) {
    if (e instanceof TypeError) return
    throw e
  }
}

/**
 * Server-only Postgres (Neon) client. Singleton for Route Handlers / server code.
 * `prepare: false` is required for Neon's connection pooler (transaction mode / PgBouncer).
 */
export function getSql() {
  const url = process.env.DATABASE_URL
  if (!url) {
    throw new Error('DATABASE_URL is not set')
  }
  assertPostgresUrl(url)
  if (!_sql) {
    _sql = postgres(url, {
      max: 5,
      ssl: 'require',
      connect_timeout: 30,
      prepare: false,
    })
  }
  return _sql
}
