import { NextResponse } from 'next/server'
import { authInApiRoute } from '@/auth'
import { actingUserStore } from '@/server/request-context'
import { authorizeAppDataCall } from '@/server/app-data-authorize'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { AccountServiceAdmin } from '@/server/account-service-admin'
import { VoucherServiceAdmin } from '@/server/voucher-service-admin'
import { SupplierServiceAdmin } from '@/server/supplier-service-admin'
import { BooksServiceAdmin } from '@/server/books/service'
import { actionLabel, isWrite, recordAudit } from '@/server/audit'
import { orgForCall } from '@/server/app-data-authorize'
import { publicError } from '@/server/public-error'
import { allowRequest, tooMany } from '@/server/rate-limit'
import { InventoryServiceAdmin } from '@/server/inventory/service'

const MAX_CALLS_PER_MINUTE = 600

const services = {
  DataService: DataServiceAdmin,
  AccountService: AccountServiceAdmin,
  VoucherService: VoucherServiceAdmin,
  SupplierService: SupplierServiceAdmin,
  BooksService: BooksServiceAdmin,
  InventoryService: InventoryServiceAdmin,
} as const

export async function POST(req: Request) {
  const session = await authInApiRoute()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  // Well above what a person's screens need, which is a few dozen calls a minute.
  if (!(await allowRequest(`app-data:${session.user.id}`, MAX_CALLS_PER_MINUTE))) return tooMany()

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
    // Worked out first, because what the call deletes can't be looked up afterwards.
    const auditOrg = isWrite(method) ? await orgForCall(service, method, args) : null
    const result = await actingUserStore.run(userId, async () => fn.apply(Svc, args))
    if (auditOrg) {
      const made = (result as { id?: unknown } | null | undefined)?.id
      await recordAudit({ org: auditOrg, userId, action: actionLabel(method), targetType: service.replace('Service', '').toLowerCase(), targetId: typeof args[0] === 'number' ? args[0] : typeof args[1] === 'number' ? args[1] : typeof made === 'number' || typeof made === 'string' ? made : null, details: args.filter((a) => typeof a === 'object') })
    }
    if (result === undefined) {
      return new NextResponse(null, { status: 204 })
    }
    return NextResponse.json(result)
  } catch (e) {
    if (e instanceof Error && e.message === 'Forbidden') {
      return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
    }
    const { status, ...body } = publicError(e)
    if (typeof (e as { code?: unknown } | null)?.code === 'string') console.error('app-data error', service, method, (e as { code?: unknown }).code)
    return NextResponse.json(body, { status })
  }
}
