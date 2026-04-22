import './load-root-env.js'
import { serve } from '@hono/node-server'
import { Hono } from 'hono'
import { logger } from './logger.js'
import { commandAuthMiddleware } from './security.js'
import { journal } from './journal/honoRoutes.js'

type Env = { Variables: { userId: string } }

const app = new Hono<Env>()

app.get('/health', (c) => c.json({ ok: true, service: 'command-api' }))

app.use('/journal/*', commandAuthMiddleware)
app.route('/journal', journal)

const port = Number(process.env.PORT ?? 8787)

serve({ fetch: app.fetch, port })
logger.info({ port }, 'command-api listening')
