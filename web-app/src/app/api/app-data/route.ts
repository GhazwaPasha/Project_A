import { NextResponse } from 'next/server'
import { auth } from '@/auth'
import { actingUserStore } from '@/server/request-context'
import { authorizeAppDataCall } from '@/server/app-data-authorize'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { AccountServiceAdmin } from '@/server/account-service-admin'
import { VoucherServiceAdmin } from '@/server/voucher-service-admin'
import { SupplierServiceAdmin } from '@/server/supplier-service-admin'

const services = {
  DataService: DataServiceAdmin,
  AccountService: AccountServiceAdmin,
  VoucherService: VoucherServiceAdmin,
  SupplierService: SupplierServiceAdmin,
} as const

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let body: { service: keyof typeof services; method: string; args: unknown[] }
  try {
    body = await req.json()
  } catch {
    return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 })
  }

  const { service, method, args } = body
  if (!service || !method || !Array.isArray(args)) {
    return NextResponse.json({ error: 'Invalid body' }, { status: 400 })
  }

  const Svc = services[service]
  if (!Svc) {
    return NextResponse.json({ error: 'Unknown service' }, { status: 400 })
  }

  const fn = (Svc as unknown as Record<string, (...a: unknown[]) => unknown>)[method]
  if (typeof fn !== 'function') {
    return NextResponse.json({ error: 'Unknown method' }, { status: 400 })
  }

  const userId = session.user.id

  try {
    await authorizeAppDataCall(service, method, args, userId)
    const result = await actingUserStore.run(userId, async () => fn.apply(Svc, args))
    if (result === undefined) {
      return new NextResponse(null, { status: 204 })
    }
    return NextResponse.json(result)
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Error'
    const status = msg === 'Forbidden' ? 403 : 500
    return NextResponse.json({ error: msg }, { status })
  }
}
