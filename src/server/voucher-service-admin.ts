import { getSql } from '@/server/pg'
import { attachItemsCategories } from '@/server/data/inventory-helpers'
import { getActingUserId } from '@/server/request-context'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { CostPlanner } from '@/server/inventory/costing'
import { planVoucherPosting, type PostingLine } from '@/server/voucher-posting'
import type {
  Account,
  InventoryItem,
  InventoryVoucher,
  InventoryVoucherLine,
  JournalEntry,
  UserProfile,
  VoucherAttachment,
  VoucherApprovalStats,
  VoucherFormData,
  VoucherLineFormData,
  VoucherStats,
  VoucherFilters
} from '@/types'

type Pg = ReturnType<typeof getSql>

async function loadUserProfiles(
  sql: Pg,
  userIds: (string | null | undefined)[]
): Promise<Map<string, UserProfile>> {
  const u = Array.from(
    new Set(
      userIds
        .filter((x): x is string => typeof x === 'string' && x.length > 0)
    )
  )
  if (u.length === 0) return new Map()
  const rows = (await sql<UserProfile[]>`
    SELECT * FROM public.user_profiles
    WHERE id = ANY(${u}::uuid[])
  `) as UserProfile[]
  return new Map(rows.map((r) => [r.id, r]))
}

async function loadAccounts(
  sql: Pg,
  accountIds: (number | null | undefined)[]
): Promise<Map<number, Account>> {
  const ids = Array.from(
    new Set(accountIds.filter((x): x is number => x != null && x > 0))
  ) as number[]
  if (ids.length === 0) return new Map()
  const rows = (await sql<Account[]>`
    SELECT * FROM public.accounts
    WHERE id = ANY(${ids}::bigint[])
  `) as Account[]
  return new Map(rows.map((a) => [a.id, a]))
}

async function loadJournals(
  sql: Pg,
  entryIds: (number | null | undefined)[]
): Promise<Map<number, JournalEntry>> {
  const ids = Array.from(
    new Set(entryIds.filter((x): x is number => x != null && x > 0))
  ) as number[]
  if (ids.length === 0) return new Map()
  const rows = (await sql<JournalEntry[]>`
    SELECT * FROM public.journal_entries
    WHERE id = ANY(${ids}::bigint[])
  `) as JournalEntry[]
  return new Map(rows.map((j) => [j.id, j]))
}

async function enrichVouchers(
  sql: Pg,
  rows: InventoryVoucher[]
): Promise<InventoryVoucher[]> {
  if (rows.length === 0) return []
  const vids = rows.map((r) => r.id)
  const allLines = (await sql<InventoryVoucherLine[]>`
    SELECT * FROM public.inventory_voucher_lines
    WHERE voucher_id = ANY(${vids}::bigint[])
    ORDER BY voucher_id, line_number
  `) as InventoryVoucherLine[]

  const itemIds = Array.from(new Set(allLines.map((l) => l.item_id).filter((x) => x > 0)))
  const items = itemIds.length
    ? ((await sql<InventoryItem[]>`
        SELECT * FROM public.inventory_items
        WHERE id = ANY(${itemIds}::bigint[])
      `) as InventoryItem[])
    : []
  const withCat = await attachItemsCategories(sql, items)
  const byItem = new Map(withCat.map((i) => [i.id, i]))

  const atts = (await sql<VoucherAttachment[]>`
    SELECT * FROM public.voucher_attachments
    WHERE voucher_id = ANY(${vids}::bigint[])
    ORDER BY voucher_id, id
  `) as VoucherAttachment[]

  const uids: string[] = []
  for (const r of rows) {
    for (const x of [
      r.requested_by,
      r.finance_approved_by,
      r.rejected_by,
      r.executed_by
    ]) {
      if (x) uids.push(x)
    }
  }
  for (const a of atts) {
    if (a.uploaded_by) uids.push(a.uploaded_by)
  }
  const prof = await loadUserProfiles(sql, uids)

  const aIds: (number | undefined)[] = []
  for (const r of rows) {
    aIds.push(r.destination_account_id ?? undefined, r.payment_account_id ?? undefined)
  }
  const acc = await loadAccounts(sql, aIds)
  const jm = await loadJournals(
    sql,
    rows.map((r) => r.journal_entry_id)
  )

  const linesByV = new Map<number, InventoryVoucherLine[]>()
  for (const l of allLines) {
    const v = l.voucher_id
    const arr = linesByV.get(v) ?? []
    const item = l.item_id ? byItem.get(l.item_id) : undefined
    arr.push({ ...l, item: item } as InventoryVoucherLine)
    linesByV.set(v, arr)
  }

  const attByV = new Map<number, VoucherAttachment[]>()
  for (const a of atts) {
    const arr = attByV.get(a.voucher_id) ?? []
    const u = a.uploaded_by ? prof.get(a.uploaded_by) : undefined
    arr.push(
      a.uploaded_by
        ? ({ ...a, uploaded_by_user: u } as VoucherAttachment)
        : a
    )
    attByV.set(a.voucher_id, arr)
  }

  return rows.map((r) => {
    return {
      ...r,
      lines: linesByV.get(r.id) ?? [],
      attachments: attByV.get(r.id) ?? [],
      requested_by_user: r.requested_by ? prof.get(r.requested_by) : undefined,
      finance_approved_by_user: r.finance_approved_by
        ? prof.get(r.finance_approved_by)
        : undefined,
      rejected_by_user: r.rejected_by ? prof.get(r.rejected_by) : undefined,
      executed_by_user: r.executed_by ? prof.get(r.executed_by) : undefined,
      destination_account: r.destination_account_id
        ? acc.get(r.destination_account_id)
        : undefined,
      payment_account: r.payment_account_id ? acc.get(r.payment_account_id) : undefined,
      journal_entry: r.journal_entry_id
        ? jm.get(r.journal_entry_id)
        : undefined
    } as InventoryVoucher
  })
}

const voucherUpdateableKeys: (keyof VoucherFormData)[] = [
  'voucher_type',
  'description',
  'notes',
  'vendor_name',
  'vendor_contact',
  'purchase_order_number',
  'expected_delivery_date',
  'purpose',
  'destination',
  'cost_center',
  'project_code',
  'destination_account_id',
  'payment_type',
  'payment_account_id',
  'deposit_amount',
  'payment_reference'
]

function formPatch(
  d: Partial<VoucherFormData>
): Partial<Record<string, string | number | null | boolean>> {
  const out: Partial<Record<string, string | number | null | boolean>> = {}
  for (const k of voucherUpdateableKeys) {
    if (k in d) {
      const v = d[k] as string | number | null | boolean | undefined
      if (v === undefined) continue
      if (k === 'destination_account_id' && (v as number) <= 0) {
        out['destination_account_id' as string] = null
        continue
      }
      if (k === 'payment_account_id' && (v as number) <= 0) {
        out['payment_account_id' as string] = null
        continue
      }
      out[k] = v as string | number | null | boolean
    }
  }
  return out
}

export class VoucherServiceAdmin {
  static async getVouchers(
    organizationId: string,
    filters?: VoucherFilters,
    limit?: number,
    offset?: number
  ): Promise<InventoryVoucher[]> {
    const sql = getSql()
    const usePage = limit != null || (offset != null && offset > 0)
    const take = usePage ? limit ?? 50 : null
    const o = offset != null && offset > 0 ? offset : 0
    const search = filters?.search?.trim()
    const rows = (await sql<InventoryVoucher[]>`
      SELECT * FROM public.inventory_vouchers
      WHERE organization_id = ${organizationId}::uuid
        AND ${
          filters?.status?.length
            ? sql` status = ANY(${filters.status}::text[]) `
            : sql` true `
        }
        AND ${
          filters?.voucher_type?.length
            ? sql` voucher_type = ANY(${filters.voucher_type}::text[]) `
            : sql` true `
        }
        AND ${
          filters?.requested_by?.length
            ? sql` requested_by = ANY(${filters.requested_by}::uuid[]) `
            : sql` true `
        }
        AND ${filters?.date_from ? sql` requested_date >= ${filters.date_from}::date ` : sql` true `}
        AND ${filters?.date_to ? sql` requested_date <= ${filters.date_to}::date ` : sql` true `}
        AND ${filters?.amount_min != null ? sql` total_estimated_cost >= ${filters.amount_min} ` : sql` true `}
        AND ${filters?.amount_max != null ? sql` total_estimated_cost <= ${filters.amount_max} ` : sql` true `}
        AND ${
          search
            ? sql` (
            voucher_number ILIKE ${`%${search}%`}
            OR description ILIKE ${`%${search}%`}
            OR COALESCE(vendor_name, '') ILIKE ${`%${search}%`}
            OR COALESCE(purpose, '') ILIKE ${`%${search}%`}
          ) `
            : sql` true `
        }
      ORDER BY created_at DESC
      ${
        usePage && take != null
          ? sql` LIMIT ${take} OFFSET ${o} `
          : sql``
      }
    `) as InventoryVoucher[]

    return enrichVouchers(sql, rows)
  }

  static async getVoucher(id: number): Promise<InventoryVoucher | null> {
    const sql = getSql()
    const rows = (await sql<InventoryVoucher[]>`
      SELECT * FROM public.inventory_vouchers
      WHERE id = ${id}
      LIMIT 1
    `) as InventoryVoucher[]

    const v = rows[0]
    if (!v) return null
    const [out] = await enrichVouchers(sql, [v])
    return out ?? null
  }

  static async createVoucher(
    voucherData: VoucherFormData,
    organizationId: string
  ): Promise<InventoryVoucher> {
    const userId = getActingUserId()
    if (!userId) throw new Error('User not authenticated')
    if (!organizationId) throw new Error('Organization ID is required')

    if (voucherData.supplier_id) {
      try {
        const { SupplierServiceAdmin } = await import('./supplier-service-admin')
        await SupplierServiceAdmin.getSupplierAccountMappings(voucherData.supplier_id)
      } catch (e) {
        console.warn('Could not load supplier account mappings:', e)
      }
    }

    const sql = getSql()
    const timestamp = Date.now().toString().slice(-6)
    const voucherNumber = `${voucherData.voucher_type.toUpperCase()}-${timestamp}`
    const totalEstimated = voucherData.lines.reduce(
      (sum, line) => sum + line.quantity_requested * (line.unit_cost_estimated || 0),
      0
    )

    const vRows = (await sql<InventoryVoucher[]>`
      INSERT INTO public.inventory_vouchers (
        organization_id, voucher_number, voucher_type, status, requested_by, requested_date,
        vendor_name, vendor_contact, purchase_order_number, expected_delivery_date,
        purpose, destination, cost_center, project_code, destination_account_id,
        payment_type, payment_account_id, deposit_amount, payment_reference,
        description, notes, total_estimated_cost
      ) VALUES (
        ${organizationId}::uuid,
        ${voucherNumber},
        ${voucherData.voucher_type}::text,
        'draft' ::text,
        ${userId}::uuid,
        ${(new Date().toISOString().split('T')[0] as string) ?? ''}::date,
        ${voucherData.vendor_name ?? null},
        ${voucherData.vendor_contact ?? null},
        ${voucherData.purchase_order_number ?? null},
        ${voucherData.expected_delivery_date ?? null},
        ${voucherData.purpose ?? null},
        ${voucherData.destination ?? null},
        ${voucherData.cost_center ?? null},
        ${voucherData.project_code ?? null},
        ${voucherData.destination_account_id ?? null},
        ${voucherData.payment_type}::text,
        ${voucherData.payment_account_id ?? null},
        ${voucherData.deposit_amount ?? 0},
        ${voucherData.payment_reference ?? null},
        ${voucherData.description},
        ${voucherData.notes ?? null},
        ${totalEstimated}
      )
      RETURNING *
    `) as InventoryVoucher[]

    const voucher = vRows[0]
    if (!voucher) {
      throw new Error('Failed to create voucher')
    }

    for (let i = 0; i < voucherData.lines.length; i++) {
      const line = voucherData.lines[i] as VoucherLineFormData
      await sql`
        INSERT INTO public.inventory_voucher_lines (
          voucher_id, line_number, item_id, quantity_requested, unit_cost_estimated, notes
        ) VALUES (
          ${voucher.id},
          ${i + 1},
          ${line.item_id},
          ${line.quantity_requested},
          ${line.unit_cost_estimated ?? null},
          ${line.notes ?? null}
        )
      `
    }

    return (await this.getVoucher(voucher.id)) as InventoryVoucher
  }

  static async updateVoucher(
    id: number,
    voucherData: Partial<VoucherFormData>
  ): Promise<InventoryVoucher> {
    const sql = getSql()
    await this.requireStatus(sql, id, ['draft', 'rejected'], 'edited')
    const { lines } = voucherData
    const patch = formPatch(voucherData)
    const nextTotal =
      lines !== undefined
        ? (lines as VoucherLineFormData[]).reduce(
            (s, l) => s + l.quantity_requested * (l.unit_cost_estimated || 0),
            0
          )
        : undefined
    if (Object.keys(patch).length > 0 || nextTotal !== undefined) {
      // postgres.js: combine list fragments (dynamic SET); cast for TS
      const sqlJoin = sql as any
      const sets: any[] = [sql` updated_at = now() `]
      if (patch.voucher_type != null) {
        sets.push(sql` voucher_type = ${String(patch.voucher_type)}::text `)
      }
      if (patch.description !== undefined) {
        sets.push(sql` description = ${String(patch.description)} `)
      }
      if (patch.notes !== undefined) {
        sets.push(sql` notes = ${String(patch.notes ?? '')} `)
      }
      if (patch.vendor_name !== undefined) {
        sets.push(
          sql` vendor_name = ${(patch as { vendor_name?: string | null }).vendor_name ?? null} `
        )
      }
      if (patch.vendor_contact !== undefined) {
        sets.push(
          sql` vendor_contact = ${(patch as { vendor_contact?: string | null }).vendor_contact ?? null} `
        )
      }
      if (patch.purchase_order_number !== undefined) {
        sets.push(
          sql` purchase_order_number = ${
            (patch as { purchase_order_number?: string | null }).purchase_order_number ?? null
          } `
        )
      }
      if (patch.expected_delivery_date !== undefined) {
        sets.push(
          sql` expected_delivery_date = ${
            (patch as { expected_delivery_date?: string | null }).expected_delivery_date ?? null
          } `
        )
      }
      if (patch.purpose !== undefined) {
        sets.push(sql` purpose = ${(patch as { purpose?: string | null }).purpose ?? null} `)
      }
      if (patch.destination !== undefined) {
        sets.push(
          sql` destination = ${(patch as { destination?: string | null }).destination ?? null} `
        )
      }
      if (patch.cost_center !== undefined) {
        sets.push(
          sql` cost_center = ${(patch as { cost_center?: string | null }).cost_center ?? null} `
        )
      }
      if (patch.project_code !== undefined) {
        sets.push(
          sql` project_code = ${(patch as { project_code?: string | null }).project_code ?? null} `
        )
      }
      if (patch.destination_account_id !== undefined) {
        sets.push(
          sql` destination_account_id = ${
            (patch as { destination_account_id?: number | null }).destination_account_id ?? null
          } `
        )
      }
      if (patch.payment_type != null) {
        sets.push(sql` payment_type = ${String(patch.payment_type)}::text `)
      }
      if (patch.payment_account_id !== undefined) {
        sets.push(
          sql` payment_account_id = ${
            (patch as { payment_account_id?: number | null }).payment_account_id ?? null
          } `
        )
      }
      if (patch.deposit_amount !== undefined) {
        const d = (patch as { deposit_amount?: number | null }).deposit_amount ?? 0
        sets.push(sql` deposit_amount = ${d}::double precision `)
      }
      if (patch.payment_reference !== undefined) {
        sets.push(
          sql` payment_reference = ${
            (patch as { payment_reference?: string | null }).payment_reference ?? null
          } `
        )
      }
      if (nextTotal !== undefined) {
        sets.push(sql` total_estimated_cost = ${nextTotal}::double precision `)
      }
      await sql`UPDATE public.inventory_vouchers SET ${sqlJoin(sets, ', ')} WHERE id = ${id}`
    }

    if (lines) {
      await sql`DELETE FROM public.inventory_voucher_lines WHERE voucher_id = ${id}`
      const lineList = lines as VoucherLineFormData[]
      for (let i = 0; i < lineList.length; i++) {
        const line = lineList[i] as VoucherLineFormData
        await sql`
          INSERT INTO public.inventory_voucher_lines (
            voucher_id, line_number, item_id, quantity_requested, unit_cost_estimated, notes
          ) VALUES (
            ${id},
            ${i + 1},
            ${line.item_id},
            ${line.quantity_requested},
            ${line.unit_cost_estimated ?? null},
            ${line.notes ?? null}
          )
        `
      }
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async deleteVoucher(id: number): Promise<void> {
    const sql = getSql()
    await this.requireStatus(sql, id, ['draft', 'rejected', 'cancelled'], 'deleted')
    await sql`DELETE FROM public.inventory_vouchers WHERE id = ${id}`
  }

  // ===============================================
  // VOUCHER WORKFLOW OPERATIONS
  // ===============================================

  static async submitForApproval(
    id: number,
    organizationId: string
  ): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    if (!organizationId) throw new Error('Organization ID is required')

    const sql = getSql()
    await this.requireStatus(sql, id, ['draft', 'rejected'], 'sent for approval')
    let approverId: string | null = null
    const acc = (await sql<{ user_id: string }[]>`
      SELECT user_id::text as user_id FROM public.organization_members
      WHERE organization_id = ${organizationId}::uuid
        AND role = 'accountant'
        AND is_active = true
      LIMIT 1
    `) as { user_id: string }[]

    if (acc[0]) {
      approverId = acc[0].user_id
    } else {
      const own = (await sql<{ user_id: string }[]>`
        SELECT user_id::text as user_id FROM public.organization_members
        WHERE organization_id = ${organizationId}::uuid
          AND role = 'organization_owner'
          AND is_active = true
        LIMIT 1
      `) as { user_id: string }[]

      if (own[0]) {
        approverId = own[0].user_id
      }
    }

    const deadline = new Date()
    deadline.setHours(deadline.getHours() + 48)

    const ex = (await sql<{ id: number; status: string }[]>`
      SELECT id, status::text as status
      FROM public.inventory_vouchers
      WHERE id = ${id}
      LIMIT 1
    `) as { id: number; status: string }[]

    if (!ex[0]) {
      throw new Error(
        'Voucher not found. The voucher system may not be set up yet.'
      )
    }

    if (approverId) {
      await sql`
        UPDATE public.inventory_vouchers
        SET
          status = 'pending_finance' ::text,
          submitted_at = now(),
          approval_deadline = ${deadline}::timestamptz,
          finance_approved_by = ${approverId}::uuid,
          updated_at = now()
        WHERE id = ${id}
      `
    } else {
      await sql`
        UPDATE public.inventory_vouchers
        SET
          status = 'pending_finance' ::text,
          submitted_at = now(),
          approval_deadline = ${deadline}::timestamptz,
          updated_at = now()
        WHERE id = ${id}
      `
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async approveVoucher(
    id: number,
    notes?: string
  ): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    await this.requireStatus(sql, id, ['pending_finance'], 'approved')
    await sql`
      UPDATE public.inventory_vouchers
      SET
        status = 'approved' ::text,
        finance_approved_by = ${acting}::uuid,
        finance_approved_at = now(),
        finance_approval_notes = ${notes ?? null},
        updated_at = now()
      WHERE id = ${id}
    `

    await sql`
      INSERT INTO public.voucher_approvals (voucher_id, approver_id, action, comments)
      VALUES (${id}, ${acting}::uuid, 'approved' ::text, ${notes ?? null})
    `

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async rejectVoucher(
    id: number,
    reason: string
  ): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    await this.requireStatus(sql, id, ['pending_finance'], 'rejected')
    await sql`
      UPDATE public.inventory_vouchers
      SET
        status = 'rejected' ::text,
        rejected_by = ${acting}::uuid,
        rejected_at = now(),
        rejection_reason = ${reason},
        updated_at = now()
      WHERE id = ${id}
    `

    await sql`
      INSERT INTO public.voucher_approvals (voucher_id, approver_id, action, comments)
      VALUES (${id}, ${acting}::uuid, 'rejected' ::text, ${reason})
    `

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async renewExpiredVoucher(
    id: number,
    reason: string
  ): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const ok = (await sql.begin(async (tx) => {
      const rows = (await tx<{ id: number }[]>`
        SELECT id FROM public.inventory_vouchers
        WHERE id = ${id} AND status = 'expired' ::text
        LIMIT 1
      `) as { id: number }[]

      if (!rows[0]) {
        throw new Error('Voucher not found or not expired')
      }
      await tx`
        UPDATE public.inventory_vouchers
        SET
          status = 'draft' ::text,
          submitted_at = NULL,
          approval_deadline = NULL,
          expired_at = NULL,
          renewed_at = now(),
          renewal_count = renewal_count + 1,
          renewal_reason = ${reason},
          updated_at = now()
        WHERE id = ${id}
      `
      await tx`
        UPDATE public.voucher_expiration_log
        SET
          renewed_at = now(),
          renewed_by = ${acting}::uuid,
          renewal_reason = ${reason}
        WHERE voucher_id = ${id}
          AND renewed_at IS NULL
      `
      return true
    })) as boolean

    if (!ok) {
      throw new Error('Failed to renew voucher')
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  // ===============================================
  // VOUCHER EXECUTION OPERATIONS
  // ===============================================

  static async executeVoucher(
    id: number,
    actualQuantities: { [lineId: number]: number },
    actualCosts?: { [lineId: number]: number }
  ): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const voucher = await this.getVoucher(id)
    if (!voucher) throw new Error('Voucher not found')
    await this.requireStatus(sql, id, ['approved'], 'received or issued')
    for (const n of [...Object.values(actualQuantities), ...Object.values(actualCosts ?? {})]) {
      if (!Number.isFinite(Number(n)) || Number(n) < 0) throw new Error('Quantities and costs must be zero or more.')
    }

    const newStatus = voucher.voucher_type === 'purchase' ? 'receiving' : 'issuing'
    await sql`
      UPDATE public.inventory_vouchers
      SET
        status = ${newStatus}::text,
        executed_by = ${acting}::uuid,
        executed_at = now(),
        updated_at = now()
      WHERE id = ${id}
    `

    for (const [lineId, quantity] of Object.entries(actualQuantities)) {
      await sql`
        UPDATE public.inventory_voucher_lines
        SET quantity_actual = ${Number(quantity)}
        WHERE id = ${parseInt(lineId, 10)} AND voucher_id = ${id}
      `
    }
    for (const [lineId, cost] of Object.entries(actualCosts ?? {})) {
      await sql`
        UPDATE public.inventory_voucher_lines
        SET unit_cost_actual = ${Number(cost)}
        WHERE id = ${parseInt(lineId, 10)} AND voucher_id = ${id}
      `
    }

    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  /** The status a step needs. A voucher can't skip ahead, or repeat a step that changes the books. */
  private static async requireStatus(exec: Pg, id: number, allowed: string[], action: string) {
    const rows = (await exec<{ status: string }[]>`SELECT status::text AS status FROM public.inventory_vouchers WHERE id = ${id} LIMIT 1`) as { status: string }[]
    if (!rows[0]) throw new Error('Voucher not found')
    if (!allowed.includes(rows[0].status)) throw new Error(`This voucher is ${rows[0].status.replace('_', ' ')}, so it can't be ${action}.`)
  }

  /** Works out what posting would do from the voucher, its lines and their categories. */
  private static async planPosting(exec: Pg, v: InventoryVoucher, payableAccountId: number | null | undefined, lock: boolean) {
    const rows = (await exec<Record<string, string | number | null>[]>`
      SELECT
        l.id AS line_id, l.item_id, i.name AS item_name,
        l.quantity_requested, l.quantity_actual, l.unit_cost_estimated, l.unit_cost_actual,
        i.quantity_available, i.average_unit_cost, i.costing_method, i.total_value,
        c.inventory_account_id, c.expense_account_id
      FROM public.inventory_voucher_lines l
      INNER JOIN public.inventory_items i ON i.id = l.item_id
      INNER JOIN public.inventory_categories c ON c.id = i.category_id
      WHERE l.voucher_id = ${v.id}
      ORDER BY l.line_number
      ${lock ? exec`FOR UPDATE OF i` : exec``}
    `) as Record<string, string | number | null>[]
    const orNull = (x: string | number | null) => (x === null ? null : Number(x))
    const lines: PostingLine[] = rows.map((r) => ({
      line_id: Number(r.line_id),
      item_id: Number(r.item_id),
      item_name: String(r.item_name),
      quantity_requested: Number(r.quantity_requested),
      quantity_actual: orNull(r.quantity_actual),
      unit_cost_estimated: orNull(r.unit_cost_estimated),
      unit_cost_actual: orNull(r.unit_cost_actual),
      quantity_available: Number(r.quantity_available),
      average_unit_cost: Number(r.average_unit_cost),
      inventory_account_id: Number(r.inventory_account_id),
      expense_account_id: Number(r.expense_account_id),
    }))
    if (v.voucher_type !== 'purchase') {
      const planner = new CostPlanner(exec)
      for (let n = 0; n < lines.length; n++) {
        const l = lines[n]
        const quantity = l.quantity_actual ?? l.quantity_requested
        if (rows[n].costing_method === 'fifo' && quantity > 0) l.issue_cost = await planner.cost({ id: l.item_id, method: 'fifo', on_hand: l.quantity_available, value: Number(rows[n].total_value), average: l.average_unit_cost }, quantity)
      }
    }
    // Vouchers keep the vendor's name, not a link, so the supplier's payable account is found by name.
    let suggested: number | null = null
    if (v.voucher_type === 'purchase' && v.vendor_name) {
      const found = (await exec<{ payable_account_id: number }[]>`
        SELECT m.payable_account_id
        FROM public.suppliers s
        INNER JOIN public.supplier_account_mappings m ON m.supplier_id = s.id
        WHERE s.organization_id = ${v.organization_id}::uuid AND lower(s.name) = lower(${v.vendor_name})
        LIMIT 2
      `) as { payable_account_id: number }[]
      if (found.length === 1) suggested = Number(found[0].payable_account_id)
    }
    const v2 = v as unknown as { payment_type: string; payment_account_id: number | null; deposit_amount: number; destination_account_id: number | null }
    const plan = planVoucherPosting({
      voucher_type: v.voucher_type,
      payment_type: v2.payment_type,
      payment_account_id: orNull(v2.payment_account_id),
      deposit_amount: Number(v2.deposit_amount) || 0,
      destination_account_id: orNull(v2.destination_account_id),
      payable_account_id: payableAccountId ?? suggested,
      lines,
    })
    return { plan, suggested }
  }

  /** Shows what posting will record, without changing anything. */
  static async previewVoucherPosting(id: number, options?: { payable_account_id?: number | null }) {
    const sql = getSql()
    await this.requireStatus(sql, id, ['receiving', 'issuing'], 'posted yet')
    const rows = (await sql<InventoryVoucher[]>`SELECT * FROM public.inventory_vouchers WHERE id = ${id} LIMIT 1`) as InventoryVoucher[]
    const v = rows[0]
    const { plan, suggested } = await this.planPosting(sql, v, options?.payable_account_id, false)
    const ids = plan.lines.map((l) => l.account_id)
    const names = (await sql<{ id: number; code: string; name: string }[]>`
      SELECT id, code, name FROM public.accounts
      WHERE id = ANY(${ids}::bigint[]) AND organization_id = ${v.organization_id}::uuid
    `) as { id: number; code: string; name: string }[]
    const byId = new Map(names.map((a) => [Number(a.id), a]))
    return {
      total: plan.total,
      problems: plan.problems,
      needs_payable: plan.needs_payable,
      suggested_payable_account_id: suggested,
      lines: plan.lines.map((l) => ({ ...l, code: byId.get(l.account_id)?.code ?? '', name: byId.get(l.account_id)?.name ?? `Account ${l.account_id}` })),
    }
  }

  /** Moves the stock and records the entry together: either both happen or neither does. */
  static async postVoucher(id: number, options?: { payable_account_id?: number | null; date?: string; warehouse_id?: number | null }): Promise<InventoryVoucher> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const date = options?.date && /^\d{4}-\d{2}-\d{2}$/.test(options.date) ? options.date : new Date().toISOString().slice(0, 10)
    const sql = getSql()
    await sql.begin(async (rawTx) => {
      const tx = rawTx as unknown as Pg
      const rows = (await tx<InventoryVoucher[]>`SELECT * FROM public.inventory_vouchers WHERE id = ${id} FOR UPDATE`) as InventoryVoucher[]
      const v = rows[0]
      if (!v) throw new Error('Voucher not found')
      if (v.status !== 'receiving' && v.status !== 'issuing') throw new Error(`This voucher is ${String(v.status).replace('_', ' ')}, so it can't be posted.`)
      const linked = (v as unknown as { journal_entry_id: number | null }).journal_entry_id
      if (linked) throw new Error('This voucher has already been posted to your books.')

      const { plan } = await this.planPosting(tx, v, options?.payable_account_id, true)
      if (plan.problems.length) throw new Error(plan.problems[0])

      const label = v.voucher_type === 'purchase' ? `Purchase from ${v.vendor_name ?? 'supplier'}` : `Stock issued${(v as unknown as { purpose?: string }).purpose ? `: ${(v as unknown as { purpose?: string }).purpose}` : ''}`
      const entry = await DataServiceAdmin.insertJournalEntry(
        tx,
        {
          organization_id: v.organization_id,
          entry_number: `JE-${v.voucher_number}`,
          entry_date: date,
          description: `${label} (${v.voucher_number})`,
          reference: v.voucher_number,
          total_amount: plan.total,
          is_posted: true,
          created_by: acting,
          posted_by: acting,
          posted_at: new Date().toISOString(),
        } as unknown as Parameters<typeof DataServiceAdmin.insertJournalEntry>[1],
        plan.lines.map((l, i) => ({ account_id: l.account_id, description: l.description, debit_amount: l.debit, credit_amount: l.credit, line_order: i + 1 })) as unknown as Parameters<typeof DataServiceAdmin.insertJournalEntry>[2]
      )
      if (!entry) throw new Error('Could not record the journal entry')

      for (const m of plan.moves) {
        await DataServiceAdmin.applyInventoryTransaction(tx, {
          organization_id: v.organization_id,
          item_id: m.item_id,
          transaction_type: m.type,
          quantity: m.type === 'out' ? -m.quantity : m.quantity,
          unit_cost: m.unit_cost,
          total_cost: m.total_cost,
          journal_entry_id: entry.id,
          reference: v.voucher_number,
          description: label,
          transaction_date: date,
          created_by: acting,
          warehouse_id: options?.warehouse_id ?? null,
          source_type: 'voucher',
          source_id: id,
        } as unknown as Parameters<typeof DataServiceAdmin.applyInventoryTransaction>[1])
        await tx`
          UPDATE public.inventory_voucher_lines
          SET quantity_actual = ${m.quantity}, unit_cost_actual = ${m.unit_cost}, total_cost = ${m.total_cost}
          WHERE id = ${m.line_id} AND voucher_id = ${id}
        `
      }
      await tx`
        UPDATE public.inventory_vouchers
        SET status = 'posted', journal_entry_id = ${entry.id}, total_actual_cost = ${plan.total}, updated_at = now()
        WHERE id = ${id}
      `
    })
    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  static async completeVoucher(id: number): Promise<InventoryVoucher> {
    const sql = getSql()
    await this.requireStatus(sql, id, ['posted'], 'completed')
    await sql`
      UPDATE public.inventory_vouchers
      SET status = 'completed' ::text, updated_at = now()
      WHERE id = ${id}
    `
    const _v = await this.getVoucher(id)
    if (!_v) throw new Error('Failed to load voucher')
    return _v
  }

  // ===============================================
  // VOUCHER STATISTICS
  // ===============================================

  static async getVoucherStats(organizationId: string): Promise<VoucherStats> {
    const sql = getSql()
    const data = (await sql<
      {
        status: string
        total_estimated_cost: number | null
        submitted_at: string | null
        finance_approved_at: string | null
      }[]
    >`
      SELECT
        status::text as status,
        total_estimated_cost,
        submitted_at,
        finance_approved_at
      FROM public.inventory_vouchers
      WHERE organization_id = ${organizationId}::uuid
    `) as {
      status: string
      total_estimated_cost: number | null
      submitted_at: string | null
      finance_approved_at: string | null
    }[]

    const stats: VoucherStats = {
      total_vouchers: data.length,
      pending_approval: data.filter((v) => v.status === 'pending_finance')
        .length,
      approved: data.filter((v) => v.status === 'approved').length,
      rejected: data.filter((v) => v.status === 'rejected').length,
      expired: data.filter((v) => v.status === 'expired').length,
      completed: data.filter((v) => v.status === 'completed').length,
      total_value: data.reduce((s, v) => s + (v.total_estimated_cost || 0), 0),
      average_approval_time_hours: 0,
      approval_rate_percent: 0
    }

    const totalSubmitted = data.filter((v) => v.status !== 'draft').length
    const totalApproved = data.filter(
      (v) => v.status === 'approved' || v.status === 'completed'
    ).length
    stats.approval_rate_percent =
      totalSubmitted > 0 ? (totalApproved / totalSubmitted) * 100 : 0

    const approvedVouchers = data.filter(
      (v) =>
        v.status === 'approved' && v.submitted_at && v.finance_approved_at
    )
    if (approvedVouchers.length > 0) {
      const totalHours = approvedVouchers.reduce((s, v) => {
        const sub = new Date(v.submitted_at as string)
        const app = new Date(v.finance_approved_at as string)
        return s + (app.getTime() - sub.getTime()) / (1000 * 60 * 60)
      }, 0)
      stats.average_approval_time_hours =
        totalHours / approvedVouchers.length
    }

    return stats
  }

  static async getApprovalStats(
    organizationId: string,
    userId: string
  ): Promise<VoucherApprovalStats> {
    const sql = getSql()
    const data = (await sql<{
      action: string
      created_at: string
      total_estimated_cost: number | null
    }[]>`
      SELECT
        va.action::text as action,
        va.created_at,
        v.total_estimated_cost
      FROM public.voucher_approvals va
      INNER JOIN public.inventory_vouchers v ON v.id = va.voucher_id
      WHERE va.approver_id = ${userId}::uuid
        AND v.organization_id = ${organizationId}::uuid
    `) as { action: string; created_at: string; total_estimated_cost: number | null }[]

    const voucherCost = (row: (typeof data)[0]) => row.total_estimated_cost ?? 0

    const approved = data.filter((a) => a.action === 'approved')
    const rejected = data.filter((a) => a.action === 'rejected')
    const largeAmounts = approved.filter((a) => voucherCost(a) > 10000)

    return {
      total_approved: approved.length,
      total_rejected: rejected.length,
      average_time_hours: 0,
      total_value: approved.reduce((s, a) => s + voucherCost(a), 0),
      pending: 0,
      fastest_approval_minutes: 0,
      large_amounts_count: largeAmounts.length,
      average_large_amount:
        largeAmounts.length > 0
          ? largeAmounts.reduce((s, a) => s + voucherCost(a), 0) / largeAmounts.length
          : 0
    }
  }

  // ===============================================
  // VOUCHER EXPIRATION
  // ===============================================

  static async expireOverdueVouchers(): Promise<number> {
    const sql = getSql()
    const n = (await sql.begin(async (tx) => {
      const due = (await tx<
        { id: number; voucher_number: string; status: string; approval_deadline: string; total_estimated_cost: number | null; organization_id: string }[]
      >`
        SELECT
          v.id, v.voucher_number::text as voucher_number, v.status::text as status,
          v.approval_deadline::text as approval_deadline,
          v.total_estimated_cost, v.organization_id::text as organization_id
        FROM public.inventory_vouchers v
        WHERE v.status = ANY(ARRAY['pending', 'pending_finance', 'approved']::text[])
        AND v.approval_deadline IS NOT NULL
        AND v.approval_deadline < now()
        AND v.expired_at IS NULL
      `) as {
        id: number
        status: string
        approval_deadline: string
        total_estimated_cost: number | null
      }[]

      let count = 0
      for (const v of due) {
        await tx`
          UPDATE public.inventory_vouchers
          SET status = 'expired' ::text, expired_at = now(), updated_at = now()
          WHERE id = ${v.id}
        `
        const c = (await tx<{ c: string }[]>`
          SELECT count(*)::text as c
          FROM public.inventory_voucher_lines vl
          WHERE vl.voucher_id = ${v.id}
        `) as { c: string }[]
        const nLines = c[0] ? parseInt(c[0].c, 10) : 0
        try {
          await tx`
            INSERT INTO public.voucher_expiration_log (
              voucher_id, status_when_expired, expired_at, approval_deadline,
              items_count, total_value
            ) VALUES (
              ${v.id},
              ${v.status}::text,
              now(),
              ${v.approval_deadline}::timestamptz,
              ${nLines},
              ${v.total_estimated_cost ?? 0}::double precision
            )
          `
        } catch (e) {
          console.warn('voucher_expiration_log insert (optional):', e)
        }
        count += 1
      }
      return count
    })) as number

    return n
  }

  static async getExpiredVouchers(organizationId: string): Promise<InventoryVoucher[]> {
    return this.getVouchers(organizationId, { status: ['expired'] })
  }

  // ===============================================
  // VOUCHER ATTACHMENTS
  // ===============================================

  static async uploadAttachment(
    voucherId: number,
    file: File,
    description?: string
  ): Promise<VoucherAttachment> {
    const acting = getActingUserId()
    if (!acting) throw new Error('User not authenticated')
    const sql = getSql()
    const buffer = Buffer.from(new Uint8Array(await file.arrayBuffer()))
    const filePath = `neondb:${voucherId}/${Date.now()}-${file.name}`

    const data = (await sql<VoucherAttachment[]>`
      INSERT INTO public.voucher_attachments (
        voucher_id, file_name, file_path, file_type, file_size, file_data, description, uploaded_by
      ) VALUES (
        ${voucherId},
        ${file.name},
        ${filePath},
        ${file.type},
        ${file.size},
        ${buffer},
        ${description ?? null},
        ${acting}::uuid
      )
      RETURNING *
    `) as VoucherAttachment[]

    const out = data[0]
    if (!out) throw new Error('Failed to create attachment record')
    return out
  }

  static async deleteAttachment(attachmentId: number): Promise<void> {
    const sql = getSql()
    await sql`DELETE FROM public.voucher_attachments WHERE id = ${attachmentId}`
  }
}
