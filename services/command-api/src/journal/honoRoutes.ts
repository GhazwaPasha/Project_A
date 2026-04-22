import { Hono } from 'hono'
import { z } from 'zod'
import { getSql } from '../db.js'
import { logger } from '../logger.js'
import {
  approveBodySchema,
  handleApprove,
  handlePost,
  handlePropose,
  handleReverse,
  listProposals,
  postBodySchema,
  projectionTrialBalance,
  proposeBodySchema,
  reverseBodySchema,
} from './handlers.js'

function jsonResponse(body: unknown, status: number) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8' },
  })
}

const journal = new Hono<{ Variables: { userId: string } }>()

journal.post('/propose', async (c) => {
  const userId = c.get('userId')
  const idem = c.req.header('idempotency-key') ?? undefined
  let json: unknown
  try {
    json = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }
  const parsed = proposeBodySchema.safeParse(json)
  if (!parsed.success) {
    return c.json({ error: parsed.error.flatten() }, 400)
  }
  try {
    const sql = getSql()
    const out = await handlePropose(sql, userId, parsed.data, idem)
    return c.json(out)
  } catch (e) {
    const err = e as Error & { status?: number; code?: string }
    if (err.code === '23505') {
      return c.json({ error: 'Idempotency conflict — use same key for retry' }, 409)
    }
    const code = err.status ?? 500
    logger.error({ err }, 'propose failed')
    return jsonResponse({ error: err.message }, code)
  }
})

journal.post('/approve', async (c) => {
  const userId = c.get('userId')
  let json: unknown
  try {
    json = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }
  const parsed = approveBodySchema.safeParse(json)
  if (!parsed.success) return c.json({ error: parsed.error.flatten() }, 400)
  try {
    const sql = getSql()
    const out = await handleApprove(sql, userId, parsed.data)
    return c.json(out)
  } catch (e) {
    const err = e as Error & { status?: number }
    const code = err.status ?? 500
    logger.error({ err }, 'approve failed')
    return jsonResponse({ error: err.message }, code)
  }
})

journal.post('/post', async (c) => {
  const userId = c.get('userId')
  let json: unknown
  try {
    json = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }
  const parsed = postBodySchema.safeParse(json)
  if (!parsed.success) return c.json({ error: parsed.error.flatten() }, 400)
  try {
    const sql = getSql()
    const out = await handlePost(sql, userId, parsed.data)
    return c.json(out)
  } catch (e) {
    const err = e as Error & { status?: number }
    const code = err.status ?? 500
    logger.error({ err }, 'post failed')
    return jsonResponse({ error: err.message }, code)
  }
})

journal.post('/reverse', async (c) => {
  const userId = c.get('userId')
  let json: unknown
  try {
    json = await c.req.json()
  } catch {
    return c.json({ error: 'Invalid JSON' }, 400)
  }
  const parsed = reverseBodySchema.safeParse(json)
  if (!parsed.success) return c.json({ error: parsed.error.flatten() }, 400)
  try {
    const sql = getSql()
    const out = await handleReverse(sql, userId, parsed.data)
    return c.json(out)
  } catch (e) {
    const err = e as Error & { status?: number }
    const code = err.status ?? 500
    logger.error({ err }, 'reverse failed')
    return jsonResponse({ error: err.message }, code)
  }
})

const listQuery = z.object({
  organization_id: z.string().uuid(),
  status: z.enum(['pending', 'approved', 'rejected', 'posted', 'superseded']).optional(),
})

journal.get('/proposals', async (c) => {
  const userId = c.get('userId')
  const q = listQuery.safeParse({
    organization_id: c.req.query('organization_id'),
    status: c.req.query('status') || undefined,
  })
  if (!q.success) return c.json({ error: q.error.flatten() }, 400)
  try {
    const sql = getSql()
    const rows = await listProposals(sql, userId, q.data.organization_id, q.data.status)
    return c.json({ proposals: rows })
  } catch (e) {
    const err = e as Error & { status?: number }
    const code = err.status ?? 500
    return jsonResponse({ error: err.message }, code)
  }
})

const tbQuery = z.object({
  organization_id: z.string().uuid(),
})

journal.get('/projection/trial-balance', async (c) => {
  const userId = c.get('userId')
  const q = tbQuery.safeParse({ organization_id: c.req.query('organization_id') })
  if (!q.success) return c.json({ error: q.error.flatten() }, 400)
  try {
    const sql = getSql()
    const rows = await projectionTrialBalance(sql, userId, q.data.organization_id)
    return c.json({ rows })
  } catch (e) {
    const err = e as Error & { status?: number }
    const code = err.status ?? 500
    return jsonResponse({ error: err.message }, code)
  }
})

export { journal }
