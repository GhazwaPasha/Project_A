import { NextResponse } from 'next/server'
import { auth } from '@/auth'
import { actingUserStore } from '@/server/request-context'
import { assertOrgMembership } from '@/server/app-data-authorize'
import { getSql } from '@/server/pg'
import { VoucherServiceAdmin } from '@/server/voucher-service-admin'

export async function POST(req: Request) {
  const session = await auth()
  if (!session?.user?.id) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }

  let form: FormData
  try {
    form = await req.formData()
  } catch {
    return NextResponse.json({ error: 'Invalid form data' }, { status: 400 })
  }

  const voucherIdRaw = form.get('voucherId')
  const file = form.get('file')
  const description = form.get('description')

  const voucherId = typeof voucherIdRaw === 'string' ? Number(voucherIdRaw) : Number(voucherIdRaw)
  if (!Number.isFinite(voucherId) || voucherId <= 0) {
    return NextResponse.json({ error: 'Invalid voucherId' }, { status: 400 })
  }
  if (!(file instanceof File)) {
    return NextResponse.json({ error: 'Missing file' }, { status: 400 })
  }

  const sql = getSql()
  const rows = await sql<{ organization_id: string }[]>`
    SELECT organization_id::text AS organization_id
    FROM public.inventory_vouchers
    WHERE id = ${voucherId}
    LIMIT 1
  `

  const orgId = rows[0]?.organization_id
  if (!orgId) {
    return NextResponse.json({ error: 'Voucher not found' }, { status: 404 })
  }

  try {
    await assertOrgMembership(session.user.id, orgId)
  } catch {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  const desc = typeof description === 'string' && description.length > 0 ? description : undefined

  try {
    const attachment = await actingUserStore.run(session.user.id, () =>
      VoucherServiceAdmin.uploadAttachment(voucherId, file, desc)
    )
    return NextResponse.json(attachment)
  } catch (e) {
    const msg = e instanceof Error ? e.message : 'Upload failed'
    return NextResponse.json({ error: msg }, { status: 500 })
  }
}
