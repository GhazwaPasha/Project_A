import { NextResponse } from 'next/server'
import { auth } from '@/auth'

async function proxyToCommandApi(req: Request, segments: string[]) {
  const base = process.env.COMMAND_API_URL?.replace(/\/$/, '')
  const secret = process.env.COMMAND_API_SECRET
  if (!base || !secret) {
    return NextResponse.json(
      { error: 'Commands API not configured. Set COMMAND_API_URL and COMMAND_API_SECRET in web-app env.' },
      { status: 503 }
    )
  }

  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  const path = segments.length ? segments.join('/') : ''
  const incoming = new URL(req.url)
  const target = path ? `${base}/${path}${incoming.search}` : `${base}/${incoming.search}`

  const headers = new Headers()
  headers.set('X-User-Id', session.user.id)
  headers.set('X-Command-Secret', secret)
  const idem = req.headers.get('Idempotency-Key')
  if (idem) {
    headers.set('Idempotency-Key', idem)
  }
  const ct = req.headers.get('Content-Type')
  if (ct) {
    headers.set('Content-Type', ct)
  }

  const hasBody = req.method !== 'GET' && req.method !== 'HEAD'
  const res = await fetch(target, {
    method: req.method,
    headers,
    body: hasBody ? await req.arrayBuffer() : undefined,
    cache: 'no-store',
  })

  const outHeaders = new Headers()
  const resCt = res.headers.get('content-type')
  if (resCt) {
    outHeaders.set('content-type', resCt)
  }

  return new NextResponse(res.body, { status: res.status, headers: outHeaders })
}

export async function GET(req: Request, ctx: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await ctx.params
  return proxyToCommandApi(req, path)
}

export async function POST(req: Request, ctx: { params: Promise<{ path?: string[] }> }) {
  const { path = [] } = await ctx.params
  return proxyToCommandApi(req, path)
}
