import postgres from 'postgres'
import { logger } from './logger.js'

let _sql: ReturnType<typeof postgres> | null = null

export function getSql() {
  const url = process.env.DATABASE_URL
  if (!url) {
    throw new Error('DATABASE_URL is required for command-api')
  }
  if (!_sql) {
    _sql = postgres(url, { max: 5, ssl: 'require' })
    logger.info('Postgres pool initialized')
  }
  return _sql
}
