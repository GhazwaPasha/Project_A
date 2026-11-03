import postgres from 'postgres'

// One connection and no TLS. A query that escapes a transaction would hang here rather than pass quietly.
export function getSql() {
  const g = globalThis as unknown as { __sql?: ReturnType<typeof postgres> }
  if (!g.__sql) g.__sql = postgres(process.env.DATABASE_URL as string, { max: 1, ssl: false, prepare: false, connect_timeout: 5, onnotice: () => {} })
  return g.__sql
}
