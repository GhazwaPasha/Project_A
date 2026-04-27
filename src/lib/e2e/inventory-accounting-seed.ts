import { DataService } from '@/lib/data-service'
import type { Account, InventoryCategory, InventoryItem } from '@/types'

export type E2EInventorySeedResult = {
  organizationId: string
  runId: string
  accounts: {
    inventory: number
    cogs: number
    cash: number
    ap: number
  }
  categoryIds: number[]
  itemIds: number[]
  transactionIds: number[]
  journalEntryIds: number[]
  log: string[]
}

function log(lines: string[], m: string) {
  lines.push(m)
}

function firstPostable(accounts: Account[], pred: (a: Account) => boolean): Account | null {
  const c = accounts.filter((a) => a.is_postable).find(pred)
  return c ?? null
}

function pickGlAccounts(accounts: Account[], lines: string[]): E2EInventorySeedResult['accounts'] {
  const inv =
    firstPostable(
      accounts,
      (a) =>
        /inventory|stock|merchandise|warehouse/i.test(a.name) && a.account_type === 'asset'
    ) ??
    firstPostable(accounts, (a) => a.account_type === 'asset' && /invent|stock/i.test(a.name)) ??
    firstPostable(accounts, (a) => a.account_type === 'asset')
  const cogs =
    firstPostable(accounts, (a) => /cogs|cost of goods|cos\s|merchandis/i.test(a.name)) ??
    firstPostable(accounts, (a) => a.account_type === 'expense')
  const cash =
    firstPostable(accounts, (a) => /cash|bank|checking|operating|petty/i.test(a.name) && a.account_type === 'asset') ??
    firstPostable(accounts, (a) => a.account_type === 'asset' && a.id !== inv?.id)
  const ap =
    firstPostable(accounts, (a) => /payable|a\/p|ap |supplier|trade pay/i.test(a.name) && a.account_type === 'liability') ??
    firstPostable(accounts, (a) => a.account_type === 'liability' && a.id !== inv?.id)

  if (!inv || !cogs) {
    throw new Error('Could not find postable inventory asset and expense (COGS) accounts in the chart of accounts.')
  }
  if (!cash) {
    throw new Error('Could not find a postable cash/bank (asset) account to pair with the journal seed.')
  }
  if (!ap) {
    throw new Error('Could not find a postable accounts payable (liability) account for the journal seed.')
  }
  if (ap.id === cash.id) {
    throw new Error('A/P and cash resolve to the same account — add distinct liability and bank accounts to the COA.')
  }
  if (ap.id === inv.id || cash.id === inv.id) {
    throw new Error('GL accounts for seed must be distinct: inventory, cash, and A/P all need different account IDs.')
  }

  return { inventory: inv.id, cogs: cogs.id, cash: cash.id, ap: ap.id }
}

/**
 * Creates 20+ inventory records (categories, items, stock movements) and 5 posted journal
 * entries that hit the same GL accounts, using the same `/api/app-data` path as the UI.
 */
export async function runE2EInventoryAccountingSeed(organizationId: string): Promise<E2EInventorySeedResult> {
  const logLines: string[] = []
  const runId = `E2E-${Date.now()}`

  const accounts = await DataService.getAccounts(organizationId, true)
  const { inventory, cogs, cash, ap } = pickGlAccounts(accounts, logLines)
  log(logLines, `GL: inventory #${inventory}, COGS #${cogs}, cash #${cash}, A/P #${ap}`)

  const categoryNames = [
    `${runId} Raw materials`,
    `${runId} Packaging`,
    `${runId} Spare parts`,
  ]

  const createdCategories: InventoryCategory[] = []
  for (const name of categoryNames) {
    const c = await DataService.createInventoryCategory({
      organization_id: organizationId,
      name,
      description: 'E2E seed',
      inventory_account_id: inventory,
      expense_account_id: cogs,
      parent_id: null,
      is_active: true,
      created_by: null,
    })
    if (c) {
      createdCategories.push(c)
      log(logLines, `Category: ${c.name} (#${c.id})`)
    }
  }

  const itemsPlanned: Array<{
    sku: string
    name: string
    category: InventoryCategory
    uom: string
    cost: number
  }> = [
    { sku: `${runId}-RM-01`, name: 'Steel sheet', category: createdCategories[0], uom: 'kg', cost: 2.4 },
    { sku: `${runId}-RM-02`, name: 'Aluminum bar', category: createdCategories[0], uom: 'kg', cost: 3.1 },
    { sku: `${runId}-RM-03`, name: 'Copper wire', category: createdCategories[0], uom: 'm', cost: 0.85 },
    { sku: `${runId}-PK-01`, name: 'Carton box (M)', category: createdCategories[1], uom: 'pcs', cost: 0.6 },
    { sku: `${runId}-PK-02`, name: 'Shrink film roll', category: createdCategories[1], uom: 'roll', cost: 12 },
    { sku: `${runId}-SP-01`, name: 'Bearing 6202', category: createdCategories[2], uom: 'pcs', cost: 4.2 },
  ]

  const itemRows: InventoryItem[] = []
  for (const p of itemsPlanned) {
    const it = await DataService.createInventoryItem({
      organization_id: organizationId,
      category_id: p.category.id,
      sku: p.sku,
      name: p.name,
      description: 'E2E seed item',
      unit_of_measure: p.uom,
      quantity_in: 0,
      quantity_out: 0,
      average_unit_cost: p.cost,
      reorder_point: 5,
      reorder_quantity: 20,
      is_active: true,
      created_by: null,
    })
    if (it) {
      itemRows.push(it)
      log(logLines, `Item: ${it.sku} ${it.name} (#${it.id})`)
    }
  }

  const transIds: number[] = []
  const journalDate = new Date('2026-01-10').toISOString().split('T')[0]!

  const stockMoves: Array<{
    item: InventoryItem
    type: 'in' | 'out' | 'adjustment'
    qty: number
    cost?: number
    dayOffset: number
  }> = [
    { item: itemRows[0], type: 'in', qty: 200, cost: 2.4, dayOffset: 0 },
    { item: itemRows[0], type: 'in', qty: 50, cost: 2.45, dayOffset: 1 },
    { item: itemRows[0], type: 'out', qty: 30, dayOffset: 2 },
    { item: itemRows[1], type: 'in', qty: 120, cost: 3.1, dayOffset: 0 },
    { item: itemRows[1], type: 'out', qty: 40, dayOffset: 3 },
    { item: itemRows[1], type: 'adjustment', qty: 2, dayOffset: 4 },
    { item: itemRows[2], type: 'in', qty: 500, cost: 0.85, dayOffset: 1 },
    { item: itemRows[2], type: 'out', qty: 100, dayOffset: 2 },
    { item: itemRows[2], type: 'out', qty: 25, dayOffset: 3 },
    { item: itemRows[3], type: 'in', qty: 800, cost: 0.6, dayOffset: 0 },
    { item: itemRows[3], type: 'out', qty: 200, dayOffset: 2 },
    { item: itemRows[4], type: 'in', qty: 40, cost: 12, dayOffset: 0 },
    { item: itemRows[4], type: 'in', qty: 10, cost: 12.1, dayOffset: 1 },
    { item: itemRows[4], type: 'out', qty: 8, dayOffset: 3 },
    { item: itemRows[5], type: 'in', qty: 60, cost: 4.2, dayOffset: 0 },
    { item: itemRows[5], type: 'in', qty: 24, cost: 4.2, dayOffset: 1 },
    { item: itemRows[5], type: 'out', qty: 12, dayOffset: 2 },
    { item: itemRows[0], type: 'out', qty: 5, dayOffset: 5 },
    { item: itemRows[3], type: 'in', qty: 50, cost: 0.62, dayOffset: 5 },
    { item: itemRows[2], type: 'adjustment', qty: -3, dayOffset: 5 },
  ]

  for (let i = 0; i < stockMoves.length; i++) {
    const m = stockMoves[i]
    const d = new Date('2026-01-10')
    d.setDate(d.getDate() + m.dayOffset)
    const dStr = d.toISOString().split('T')[0]!

    const q =
      m.type === 'out' ? -Math.abs(m.qty) : m.type === 'in' ? Math.abs(m.qty) : m.qty
    const ucost = m.cost != null && m.type === 'in' ? m.cost : m.cost ?? 0
    const totalCost = m.type === 'in' && ucost > 0 ? Math.abs(q) * ucost : null
    const line = await DataService.createInventoryTransaction({
      organization_id: organizationId,
      item_id: m.item.id,
      transaction_type: m.type,
      quantity: q,
      unit_cost: m.type === 'in' && ucost > 0 ? ucost : null,
      total_cost: totalCost,
      journal_entry_id: null,
      reference: `SEED-${runId}-T${i + 1}`,
      description: `E2E stock move ${i + 1}/${stockMoves.length}`,
      transaction_date: dStr,
      created_by: null,
    })
    if (line) {
      transIds.push(line.id)
    }
  }
  log(logLines, `Recorded ${transIds.length} inventory transactions (target 20+).`)

  const journalEntryIds: number[] = []
  const je = async (
    i: number,
    amount: number,
    date: string,
    desc: string,
    lines: { account_id: number; d: number; c: number }[]
  ) => {
    const tDr = lines.reduce((s, l) => s + l.d, 0)
    const tCr = lines.reduce((s, l) => s + l.c, 0)
    if (Math.abs(tDr - tCr) > 0.005) {
      log(logLines, `skip JE#${i}: not balanced (dr ${tDr} vs cr ${tCr})`)
      return null
    }
    if (Math.abs(tDr - amount) > 0.005) {
      log(logLines, `Warning JE#${i}: amount hint ${amount} vs debits ${tDr}`)
    }
    return DataService.createJournalEntry(
      {
        organization_id: organizationId,
        entry_number: `JE-${runId}-${i}`,
        entry_date: date,
        description: desc,
        reference: `E2E seed ${i}`,
        total_amount: tDr,
        is_posted: true,
        created_by: null,
        posted_by: null,
        posted_at: new Date().toISOString(),
      },
      lines.map((l, li) => ({
        account_id: l.account_id,
        description: desc,
        debit_amount: l.d,
        credit_amount: l.c,
        line_order: li + 1,
      }))
    )
  }

  const p1 = await je(1, 2400, journalDate, 'E2E: Purchase — receive materials on credit', [
    { account_id: inventory, d: 2400, c: 0 },
    { account_id: ap, d: 0, c: 2400 },
  ])
  if (p1) journalEntryIds.push(p1.id)
  const p2 = await je(2, 500, journalDate, 'E2E: Petty cash purchase of consumables', [
    { account_id: inventory, d: 500, c: 0 },
    { account_id: cash, d: 0, c: 500 },
  ])
  if (p2) journalEntryIds.push(p2.id)
  const p3 = await je(3, 320, journalDate, 'E2E: Recognize COGS for shipment (GL)', [
    { account_id: cogs, d: 320, c: 0 },
    { account_id: inventory, d: 0, c: 320 },
  ])
  if (p3) journalEntryIds.push(p3.id)
  const p4 = await je(4, 2000, journalDate, 'E2E: Pay part of A/P (cash)', [
    { account_id: ap, d: 2000, c: 0 },
    { account_id: cash, d: 0, c: 2000 },
  ])
  if (p4) journalEntryIds.push(p4.id)
  const p5 = await je(5, 150, journalDate, 'E2E: Additional COGS to align with ops', [
    { account_id: cogs, d: 150, c: 0 },
    { account_id: inventory, d: 0, c: 150 },
  ])
  if (p5) journalEntryIds.push(p5.id)
  log(logLines, `Posted ${journalEntryIds.length} journal entries to inventory / COGS / A&P / cash.`)

  return {
    organizationId,
    runId,
    accounts: { inventory, cogs, cash, ap },
    categoryIds: createdCategories.map((c) => c.id),
    itemIds: itemRows.map((i) => i.id),
    transactionIds: transIds,
    journalEntryIds,
    log: logLines,
  }
}
