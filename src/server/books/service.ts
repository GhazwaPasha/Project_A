import { getSql } from '@/server/pg'
import { getActingUserId } from '@/server/request-context'
import { DataServiceAdmin } from '@/server/data-service-admin'
import { netAmountForAccountType } from '@/server/data/ledger-sql'
import {
  agedReport, documentEntry, documentTotals, forecastSeries, matchCandidates, money, paymentEntry, reconciliation,
  reversalLines, stockEntry, statementAmount, taxSummary, type EntryLine,
} from '@/server/books/rules'
import { nextNumber } from '@/server/numbering'
import { costOfSalesEntry, parseSerials } from '@/server/inventory/rules'
import { CostPlanner } from '@/server/inventory/costing'

type Pg = ReturnType<typeof getSql>
type Row = Record<string, any> // eslint-disable-line @typescript-eslint/no-explicit-any
const DATE = /^\d{4}-\d{2}-\d{2}$/
const today = () => new Date().toISOString().slice(0, 10)
const requireDate = (d: unknown, label = 'Date') => {
  if (typeof d !== 'string' || !DATE.test(d) || Number.isNaN(Date.parse(d))) throw new Error(`${label} must be a real date.`)
  return d
}
const positive = (n: unknown, label: string) => {
  const v = Number(n)
  if (!Number.isFinite(v) || v <= 0) throw new Error(`${label} must be more than zero.`)
  return v
}
const label = (s: unknown) => (typeof s === 'string' && s.trim() ? s.trim() : null)
function acting() {
  const id = getActingUserId()
  if (!id) throw new Error('User not authenticated')
  return id
}

export type DocumentForm = {
  kind: 'invoice' | 'bill'
  customer_id?: number | null
  supplier_id?: number | null
  party_name?: string
  issue_date: string
  due_date: string
  notes?: string | null
  lines: { description: string; account_id?: number | null; quantity: number; unit_price: number; tax_rate_id?: number | null; item_id?: number | null; warehouse_id?: number | null; unit_id?: number | null; serial_numbers?: string[] | string | null }[]
}

/** Every method takes the organization first, and every query is limited to it. */
export class BooksServiceAdmin {
  // ---- Entries ----

  private static async post(tx: Pg, org: string, e: { number: string; date: string; description: string; reference?: string | null; reverses?: number | null }, lines: EntryLine[]) {
    const user = acting()
    const entry = await DataServiceAdmin.insertJournalEntry(
      tx,
      { organization_id: org, entry_number: e.number, entry_date: e.date, description: e.description, reference: e.reference ?? null, total_amount: 0, is_posted: true, created_by: user, posted_by: user, posted_at: new Date().toISOString() } as never,
      lines.map((l, i) => ({ account_id: l.account_id, description: l.description, debit_amount: l.debit, credit_amount: l.credit, line_order: i + 1 })) as never
    )
    if (!entry) throw new Error('Could not record the entry.')
    if (e.reverses) await tx`UPDATE public.journal_entries SET reverses_entry_id = ${e.reverses} WHERE id = ${entry.id}`
    return Number(entry.id)
  }

  /** Reverses by adding the opposite entry, so history stays intact. Work that created an entry must be undone from where it started. */
  static async reverseEntry(org: string, entryId: number, options: { date?: string; reason?: string } = {}) {
    const date = options.date ? requireDate(options.date) : today()
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [e] = (await tx`SELECT * FROM public.journal_entries WHERE id = ${entryId} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!e) throw new Error('Entry not found.')
      if (e.reverses_entry_id) throw new Error('This entry is itself a reversal.')
      const [done] = (await tx`SELECT id FROM public.journal_entries WHERE reverses_entry_id = ${entryId} LIMIT 1`) as Row[]
      if (done) throw new Error('This entry has already been reversed.')
      const [source] = (await tx`
        SELECT 'an invoice or bill' AS what FROM public.trade_documents WHERE journal_entry_id = ${entryId}
        UNION ALL SELECT 'a payment' FROM public.trade_payments WHERE journal_entry_id = ${entryId}
        UNION ALL SELECT 'a voucher' FROM public.inventory_vouchers WHERE journal_entry_id = ${entryId}
        UNION ALL SELECT 'a stock movement' FROM public.inventory_transactions WHERE journal_entry_id = ${entryId}
        UNION ALL SELECT 'a bank line' FROM public.bank_statement_lines b JOIN public.journal_entry_lines l ON l.id = b.matched_journal_line_id WHERE l.journal_entry_id = ${entryId}
        LIMIT 1
      `) as Row[]
      if (source) throw new Error(`This entry came from ${source.what}. Undo it there, so the two stay in step.`)
      const lines = (await tx`SELECT account_id, description, debit_amount, credit_amount FROM public.journal_entry_lines WHERE journal_entry_id = ${entryId} ORDER BY line_order`) as Row[]
      const id = await this.post(tx, org, {
        number: `REV-${e.entry_number}`,
        date,
        description: `Reversal of ${e.entry_number}${label(options.reason) ? `: ${label(options.reason)}` : ''}`,
        reference: e.entry_number,
        reverses: entryId,
      }, reversalLines(lines.map((l) => ({ account_id: Number(l.account_id), description: l.description, debit: Number(l.debit_amount), credit: Number(l.credit_amount) }))))
      return { entry_id: id }
    })
  }

  // ---- Period closing ----

  static async getBooksLock(org: string) {
    const sql = getSql()
    const history = (await sql`
      SELECT id, through_date::text AS through_date, notes, closed_at::text AS closed_at, reopened_at::text AS reopened_at, reopen_reason
      FROM public.period_closes WHERE organization_id = ${org}::uuid ORDER BY closed_at DESC LIMIT 24
    `) as Row[]
    const open = history.filter((h) => !h.reopened_at).sort((a, b) => (a.through_date < b.through_date ? 1 : -1))
    return { closed_through: open[0]?.through_date ?? null, history }
  }

  /** What's worth sorting out before closing. Warnings, apart from unbalanced books. */
  static async getCloseChecklist(org: string, through: string) {
    requireDate(through)
    const sql = getSql()
    const [books] = (await sql`
      SELECT COALESCE(SUM(l.debit_amount), 0)::float AS dr, COALESCE(SUM(l.credit_amount), 0)::float AS cr
      FROM public.journal_entry_lines l JOIN public.journal_entries e ON e.id = l.journal_entry_id
      WHERE e.organization_id = ${org}::uuid AND e.entry_date <= ${through}::date
    `) as Row[]
    const [counts] = (await sql`
      SELECT
        (SELECT COUNT(*)::int FROM public.trade_documents WHERE organization_id = ${org}::uuid AND status = 'draft' AND issue_date <= ${through}::date) AS draft_documents,
        (SELECT COUNT(*)::int FROM public.bank_statement_lines WHERE organization_id = ${org}::uuid AND status = 'unmatched' AND statement_date <= ${through}::date) AS unmatched_bank_lines,
        (SELECT COUNT(*)::int FROM public.agent_proposals WHERE organization_id = ${org}::uuid AND status = 'pending' AND entry_date <= ${through}::date) AS pending_proposals,
        (SELECT COUNT(*)::int FROM public.inventory_transactions WHERE organization_id = ${org}::uuid AND journal_entry_id IS NULL AND COALESCE(total_cost, 0) <> 0 AND transaction_date <= ${through}::date) AS unposted_stock,
        (SELECT COUNT(*)::int FROM public.inventory_vouchers WHERE organization_id = ${org}::uuid AND status IN ('receiving', 'issuing')) AS unposted_vouchers
    `) as Row[]
    return { balanced: Math.abs(Number(books.dr) - Number(books.cr)) < 0.005, ...counts }
  }

  static async closeBooks(org: string, form: { through: string; notes?: string }) {
    const through = requireDate(form.through)
    if (through > today()) throw new Error("You can't close a period that hasn't finished.")
    const checks = await this.getCloseChecklist(org, through)
    if (!checks.balanced) throw new Error("The books don't balance up to this date, so they can't be closed.")
    const lock = await this.getBooksLock(org)
    if (lock.closed_through && through <= lock.closed_through) throw new Error(`The books are already closed through ${lock.closed_through}.`)
    await getSql()`INSERT INTO public.period_closes (organization_id, through_date, notes, closed_by) VALUES (${org}::uuid, ${through}::date, ${label(form.notes)}, ${acting()}::uuid)`
    return this.getBooksLock(org)
  }

  /** Reopens the latest close. A reason is required, because it changes figures people may already rely on. */
  static async reopenBooks(org: string, form: { reason: string }) {
    const reason = label(form.reason)
    if (!reason) throw new Error('Say why the period is being reopened.')
    const rows = await getSql()`
      UPDATE public.period_closes SET reopened_at = now(), reopened_by = ${acting()}::uuid, reopen_reason = ${reason}
      WHERE id = (SELECT id FROM public.period_closes WHERE organization_id = ${org}::uuid AND reopened_at IS NULL ORDER BY through_date DESC LIMIT 1)
      RETURNING id
    `
    if (!rows.length) throw new Error('No closed period to reopen.')
    return this.getBooksLock(org)
  }

  // ---- Stock movements ----

  static async listUnpostedStock(org: string) {
    return getSql()`
      SELECT t.id, t.transaction_type, t.quantity::float, t.total_cost::float, t.transaction_date::text AS transaction_date, t.reference, i.name AS item_name
      FROM public.inventory_transactions t JOIN public.inventory_items i ON i.id = t.item_id
      WHERE t.organization_id = ${org}::uuid AND t.journal_entry_id IS NULL AND COALESCE(t.total_cost, 0) <> 0
      ORDER BY t.transaction_date DESC LIMIT 200
    `
  }

  private static async postMovement(tx: Pg, org: string, id: number, offset: number | null | undefined) {
    const [t] = (await tx`
      SELECT t.*, t.transaction_date::text AS txn_date, i.name AS item_name, c.inventory_account_id, c.expense_account_id
      FROM public.inventory_transactions t
      JOIN public.inventory_items i ON i.id = t.item_id
      JOIN public.inventory_categories c ON c.id = i.category_id
      WHERE t.id = ${id} AND t.organization_id = ${org}::uuid
      FOR UPDATE OF t
    `) as Row[]
    if (!t) throw new Error('Stock movement not found.')
    if (t.journal_entry_id) throw new Error('This stock movement is already in your books.')
    const plan = stockEntry({ type: t.transaction_type, quantity: Number(t.quantity), total_cost: Number(t.total_cost ?? 0), inventory_account_id: Number(t.inventory_account_id), expense_account_id: Number(t.expense_account_id), offset_account_id: offset ? Number(offset) : null })
    if (plan.problem) throw new Error(plan.problem)
    if (!plan.lines) return null
    const entry = await this.post(tx, org, { number: `JE-STK-${id}`, date: t.txn_date, description: `Stock ${t.transaction_type === 'adjustment' ? 'correction' : t.transaction_type}: ${t.item_name}`, reference: t.reference }, plan.lines)
    await tx`UPDATE public.inventory_transactions SET journal_entry_id = ${entry} WHERE id = ${id}`
    return entry
  }

  /** Puts a movement someone already recorded into the books. */
  static async postStockMovement(org: string, id: number, options: { offset_account_id?: number | null } = {}) {
    const entry = await getSql().begin((raw) => this.postMovement(raw as unknown as Pg, org, Number(id), options.offset_account_id))
    return { entry_id: entry }
  }

  /** Records the stock change and its entry together, so neither can happen alone. */
  static async recordStockMovement(org: string, form: { item_id: number; transaction_type: 'in' | 'out' | 'adjustment'; quantity: number; unit_cost?: number | null; reference?: string | null; description?: string | null; transaction_date: string; offset_account_id?: number | null; warehouse_id?: number | null; lot_id?: number | null; lot_number?: string | null; expiry_date?: string | null; serial_numbers?: string[] | string | null }) {
    const date = requireDate(form.transaction_date)
    const quantity = Number(form.quantity)
    if (!Number.isFinite(quantity) || quantity === 0) throw new Error('Quantity must not be zero.')
    if (form.transaction_type !== 'adjustment' && quantity < 0) throw new Error('Quantity must be more than zero.')
    const user = acting()
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const row = await DataServiceAdmin.applyInventoryTransaction(tx, {
        organization_id: org, item_id: Number(form.item_id), transaction_type: form.transaction_type,
        quantity: form.transaction_type === 'out' ? -quantity : quantity,
        unit_cost: form.unit_cost ?? null,
        total_cost: form.unit_cost ? money(Math.abs(quantity) * Number(form.unit_cost)) : null,
        journal_entry_id: null, reference: label(form.reference), description: label(form.description), transaction_date: date, created_by: user,
        warehouse_id: form.warehouse_id ?? null, lot_id: form.lot_id ?? null, lot_number: label(form.lot_number), expiry_date: form.expiry_date ? requireDate(form.expiry_date, 'Expiry date') : null, serial_numbers: form.serial_numbers ?? null,
      } as never)
      if (!row) throw new Error('Could not record the movement.')
      const entry = await this.postMovement(tx, org, Number(row.id), form.offset_account_id)
      return { id: Number(row.id), entry_id: entry }
    })
  }

  // ---- Customers and tax rates ----

  static listCustomers(org: string) {
    return getSql()`
      SELECT c.*, COALESCE(o.balance, 0)::float AS balance
      FROM public.customers c
      LEFT JOIN (SELECT customer_id, SUM(total - amount_paid) AS balance FROM public.trade_documents WHERE status IN ('posted', 'partial') GROUP BY customer_id) o ON o.customer_id = c.id
      WHERE c.organization_id = ${org}::uuid AND c.is_active ORDER BY c.name
    `
  }

  static async saveCustomer(org: string, form: { id?: number; name: string; email?: string; phone?: string; address?: string; tax_id?: string; receivable_account_id?: number | null }) {
    const name = label(form.name)
    if (!name) throw new Error('Customer name is required.')
    const sql = getSql()
    const values = { email: label(form.email), phone: label(form.phone), address: label(form.address), tax_id: label(form.tax_id), receivable: form.receivable_account_id ?? null }
    const rows = form.id
      ? await sql`UPDATE public.customers SET name = ${name}, email = ${values.email}, phone = ${values.phone}, address = ${values.address}, tax_id = ${values.tax_id}, receivable_account_id = ${values.receivable}, updated_at = now() WHERE id = ${form.id} AND organization_id = ${org}::uuid RETURNING *`
      : await sql`INSERT INTO public.customers (organization_id, name, email, phone, address, tax_id, receivable_account_id, created_by) VALUES (${org}::uuid, ${name}, ${values.email}, ${values.phone}, ${values.address}, ${values.tax_id}, ${values.receivable}, ${acting()}::uuid) RETURNING *`
    if (!rows[0]) throw new Error('Customer not found.')
    return rows[0]
  }

  static async archiveCustomer(org: string, id: number) {
    await getSql()`UPDATE public.customers SET is_active = false, updated_at = now() WHERE id = ${id} AND organization_id = ${org}::uuid`
  }

  static listTaxRates(org: string) {
    return getSql()`SELECT id, name, rate::float, sales_account_id, purchase_account_id, is_active FROM public.tax_rates WHERE organization_id = ${org}::uuid ORDER BY is_active DESC, name`
  }

  static async saveTaxRate(org: string, form: { id?: number; name: string; rate: number; sales_account_id: number; purchase_account_id: number; is_active?: boolean }) {
    const name = label(form.name)
    const rate = Number(form.rate)
    if (!name) throw new Error('Name the tax rate.')
    if (!Number.isFinite(rate) || rate < 0 || rate > 100) throw new Error('The rate must be between 0 and 100.')
    if (!form.sales_account_id || !form.purchase_account_id) throw new Error('Choose the accounts this tax goes to.')
    const sql = getSql()
    const rows = form.id
      ? await sql`UPDATE public.tax_rates SET name = ${name}, rate = ${rate}, sales_account_id = ${form.sales_account_id}, purchase_account_id = ${form.purchase_account_id}, is_active = ${form.is_active ?? true} WHERE id = ${form.id} AND organization_id = ${org}::uuid RETURNING id`
      : await sql`INSERT INTO public.tax_rates (organization_id, name, rate, sales_account_id, purchase_account_id) VALUES (${org}::uuid, ${name}, ${rate}, ${form.sales_account_id}, ${form.purchase_account_id}) RETURNING id`
    if (!rows[0]) throw new Error('Tax rate not found.')
    return rows[0]
  }

  // ---- Invoices and bills ----

  static listDocuments(org: string, kind: 'invoice' | 'bill') {
    return getSql()`
      SELECT id, kind, number, status, party_name, issue_date::text AS issue_date, due_date::text AS due_date, subtotal::float, tax_total::float, total::float, amount_paid::float, (total - amount_paid)::float AS balance
      FROM public.trade_documents WHERE organization_id = ${org}::uuid AND kind = ${kind}
      ORDER BY issue_date DESC, id DESC LIMIT 500
    `
  }

  static async getDocument(org: string, id: number) {
    const sql = getSql()
    const [d] = (await sql`
      SELECT d.*, d.issue_date::text AS issue_date, d.due_date::text AS due_date, d.subtotal::float, d.tax_total::float, d.total::float, d.amount_paid::float, (d.total - d.amount_paid)::float AS balance,
             COALESCE(c.receivable_account_id, m.payable_account_id) AS suggested_control_account_id
      FROM public.trade_documents d
      LEFT JOIN public.customers c ON c.id = d.customer_id
      LEFT JOIN public.supplier_account_mappings m ON m.supplier_id = d.supplier_id
      WHERE d.id = ${id} AND d.organization_id = ${org}::uuid
    `) as Row[]
    if (!d) throw new Error('Document not found.')
    const lines = await sql`
      SELECT l.id, l.description, l.account_id, l.quantity::float, l.unit_price::float, l.tax_rate_id, l.tax_rate::float, l.amount::float, l.tax_amount::float, r.name AS tax_name,
             l.item_id, l.warehouse_id, l.cost_amount::float, l.unit_name, l.unit_factor::float, l.serial_numbers, (SELECT u.id FROM public.item_units u WHERE u.item_id = l.item_id AND u.name = l.unit_name) AS unit_id, i.sku, i.name AS item_name, w.name AS warehouse_name
      FROM public.trade_document_lines l LEFT JOIN public.tax_rates r ON r.id = l.tax_rate_id
      LEFT JOIN public.inventory_items i ON i.id = l.item_id LEFT JOIN public.warehouses w ON w.id = l.warehouse_id
      WHERE l.document_id = ${id} ORDER BY l.line_order
    `
    const payments = await sql`SELECT id, payment_date::text AS payment_date, amount::float, reference, bank_account_id FROM public.trade_payments WHERE document_id = ${id} ORDER BY payment_date, id`
    return { ...d, lines, payments }
  }

  private static async writeLines(tx: Pg, org: string, id: number, form: DocumentForm) {
    if (!form.lines?.length) throw new Error('Add at least one line.')
    const rateIds = form.lines.map((l) => l.tax_rate_id).filter(Boolean).map(Number)
    const rates = rateIds.length ? ((await tx`SELECT id, rate::float FROM public.tax_rates WHERE organization_id = ${org}::uuid AND id = ANY(${rateIds}::bigint[])`) as Row[]) : []
    const rateOf = (rid?: number | null) => {
      if (!rid) return 0
      const r = rates.find((x) => Number(x.id) === Number(rid))
      if (!r) throw new Error('That tax rate is not available.')
      return Number(r.rate)
    }
    const itemIds = form.lines.map((l) => l.item_id).filter(Boolean).map(Number)
    const items = itemIds.length ? ((await tx`
      SELECT i.id, i.income_account_id, c.inventory_account_id FROM public.inventory_items i JOIN public.inventory_categories c ON c.id = i.category_id
      WHERE i.organization_id = ${org}::uuid AND i.id = ANY(${itemIds}::bigint[])
    `) as Row[]) : []
    const warehouseIds = form.lines.map((l) => l.warehouse_id).filter(Boolean).map(Number)
    const warehouses = warehouseIds.length ? ((await tx`SELECT id FROM public.warehouses WHERE organization_id = ${org}::uuid AND id = ANY(${warehouseIds}::bigint[])`) as Row[]) : []
    // A bought item always goes to its stock account, or stock and the books would disagree. A sold item uses the account chosen, or its own.
    const lines = form.lines.map((l) => {
      if (l.warehouse_id && !warehouses.some((w) => Number(w.id) === Number(l.warehouse_id))) throw new Error('Warehouse not found.')
      if (!l.item_id) return l
      const item = items.find((x) => Number(x.id) === Number(l.item_id))
      if (!item) throw new Error('Item not found.')
      return { ...l, account_id: form.kind === 'bill' ? Number(item.inventory_account_id) : l.account_id || (item.income_account_id ? Number(item.income_account_id) : null) }
    })
    const unitIds = lines.map((l) => l.unit_id).filter(Boolean).map(Number)
    const units = unitIds.length ? ((await tx`
      SELECT u.id, u.item_id, u.name, u.factor::float AS factor FROM public.item_units u JOIN public.inventory_items i ON i.id = u.item_id
      WHERE i.organization_id = ${org}::uuid AND u.id = ANY(${unitIds}::bigint[])
    `) as Row[]) : []
    const unitOf = (l: { unit_id?: number | null; item_id?: number | null }) => {
      if (!l.unit_id) return null
      const u = units.find((x) => Number(x.id) === Number(l.unit_id) && Number(x.item_id) === Number(l.item_id))
      if (!u) throw new Error('That unit is not set up for this item.')
      return u
    }
    const accountIds = lines.map((l) => Number(l.account_id)).filter(Boolean)
    const known = (await tx`SELECT id FROM public.accounts WHERE organization_id = ${org}::uuid AND id = ANY(${accountIds}::bigint[])`) as Row[]
    const priced = lines.map((l) => {
      if (!label(l.description)) throw new Error('Every line needs a description.')
      if (!known.some((a) => Number(a.id) === Number(l.account_id))) throw new Error('Choose an account for every line.')
      const quantity = positive(l.quantity, 'Quantity')
      const unit_price = Number(l.unit_price)
      if (!Number.isFinite(unit_price) || unit_price < 0) throw new Error("A line's price can't be negative.")
      return { ...l, quantity, unit_price, tax_rate: rateOf(l.tax_rate_id) }
    })
    const totals = documentTotals(priced)
    await tx`DELETE FROM public.trade_document_lines WHERE document_id = ${id}`
    for (let i = 0; i < priced.length; i++) {
      const l = priced[i]
      await tx`
        INSERT INTO public.trade_document_lines (document_id, line_order, description, account_id, quantity, unit_price, tax_rate_id, tax_rate, amount, tax_amount, item_id, warehouse_id, unit_name, unit_factor, serial_numbers)
        VALUES (${id}, ${i + 1}, ${l.description.trim()}, ${Number(l.account_id)}, ${l.quantity}, ${l.unit_price}, ${l.tax_rate_id ? Number(l.tax_rate_id) : null}, ${l.tax_rate}, ${totals.lines[i].amount}, ${totals.lines[i].tax_amount}, ${l.item_id ? Number(l.item_id) : null}, ${l.warehouse_id ? Number(l.warehouse_id) : null}, ${unitOf(l)?.name ?? null}, ${unitOf(l)?.factor ?? 1}, ${l.item_id && parseSerials(l.serial_numbers).length ? parseSerials(l.serial_numbers) : null})
      `
    }
    await tx`UPDATE public.trade_documents SET subtotal = ${totals.subtotal}, tax_total = ${totals.tax_total}, total = ${totals.total}, updated_at = now() WHERE id = ${id}`
  }

  private static async partyName(tx: Pg, org: string, form: DocumentForm) {
    if (form.customer_id) {
      const [c] = (await tx`SELECT name FROM public.customers WHERE id = ${form.customer_id} AND organization_id = ${org}::uuid`) as Row[]
      if (!c) throw new Error('Customer not found.')
      return c.name as string
    }
    if (form.supplier_id) {
      const [s] = (await tx`SELECT name FROM public.suppliers WHERE id = ${form.supplier_id} AND organization_id = ${org}::uuid`) as Row[]
      if (!s) throw new Error('Supplier not found.')
      return s.name as string
    }
    const name = label(form.party_name)
    if (!name) throw new Error(form.kind === 'invoice' ? 'Choose who this invoice is for.' : 'Choose who this bill is from.')
    return name
  }

  /** Saves a draft. A draft doesn't touch the books until someone posts it. */
  static async saveDocument(org: string, form: DocumentForm & { id?: number }) {
    return getSql().begin((raw) => this.saveDocumentIn(raw as unknown as Pg, org, form))
  }

  /** The same, inside the caller's transaction. */
  static async saveDocumentIn(tx: Pg, org: string, form: DocumentForm & { id?: number }) {
    if (form.kind !== 'invoice' && form.kind !== 'bill') throw new Error('Unknown document type.')
    const issue = requireDate(form.issue_date, 'Issue date')
    const due = requireDate(form.due_date, 'Due date')
    if (due < issue) throw new Error("The due date can't be before the issue date.")
    const party = await this.partyName(tx, org, form)
    const customer = form.kind === 'invoice' ? form.customer_id ?? null : null
    const supplier = form.kind === 'bill' ? form.supplier_id ?? null : null
    let id = Number(form.id ?? 0)
    if (id) {
      const [d] = (await tx`SELECT status FROM public.trade_documents WHERE id = ${id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!d) throw new Error('Document not found.')
      if (d.status !== 'draft') throw new Error('Only a draft can be edited.')
      await tx`UPDATE public.trade_documents SET customer_id = ${customer}, supplier_id = ${supplier}, party_name = ${party}, issue_date = ${issue}::date, due_date = ${due}::date, notes = ${label(form.notes)}, updated_at = now() WHERE id = ${id}`
    } else {
      const number = await nextNumber(tx, org, form.kind === 'invoice' ? 'INV' : 'BILL', 'public.trade_documents', 'number')
      const [row] = (await tx`
        INSERT INTO public.trade_documents (organization_id, kind, number, customer_id, supplier_id, party_name, issue_date, due_date, notes, created_by)
        VALUES (${org}::uuid, ${form.kind}, ${number}, ${customer}, ${supplier}, ${party}, ${issue}::date, ${due}::date, ${label(form.notes)}, ${acting()}::uuid)
        RETURNING id
      `) as Row[]
      id = Number(row.id)
    }
    await this.writeLines(tx, org, id, form)
    return { id }
  }

  static async deleteDocument(org: string, id: number) {
    const rows = await getSql()`DELETE FROM public.trade_documents WHERE id = ${id} AND organization_id = ${org}::uuid AND status = 'draft' RETURNING id`
    if (!rows.length) throw new Error('Only a draft can be deleted. Void it instead.')
  }

  private static async entryForDocument(tx: Pg, doc: Row, control: number) {
    const lines = (await tx`
      SELECT l.account_id, l.quantity::float, l.unit_price::float, l.tax_rate::float, r.sales_account_id, r.purchase_account_id
      FROM public.trade_document_lines l LEFT JOIN public.tax_rates r ON r.id = l.tax_rate_id
      WHERE l.document_id = ${doc.id} ORDER BY l.line_order
    `) as Row[]
    return documentEntry(doc.kind, control, lines.map((l) => ({
      account_id: Number(l.account_id), quantity: Number(l.quantity), unit_price: Number(l.unit_price), tax_rate: Number(l.tax_rate),
      tax_account_id: (doc.kind === 'invoice' ? l.sales_account_id : l.purchase_account_id) ? Number(doc.kind === 'invoice' ? l.sales_account_id : l.purchase_account_id) : null,
    })))
  }

  /** Item lines of a document, with what each sold line costs. Selling everything takes the item's whole value, so no cents get left behind. */
  private static async stockLines(tx: Pg, docId: number) {
    const rows = (await tx`
      SELECT l.id, l.item_id, l.warehouse_id, l.quantity::float * l.unit_factor::float AS quantity, l.amount::float, l.cost_amount::float, l.serial_numbers,
             i.name AS item_name, i.costing_method, i.quantity_available::float AS on_hand, i.total_value::float AS value, i.average_unit_cost::float AS average, c.inventory_account_id, c.expense_account_id
      FROM public.trade_document_lines l
      JOIN public.inventory_items i ON i.id = l.item_id
      JOIN public.inventory_categories c ON c.id = i.category_id
      WHERE l.document_id = ${docId} ORDER BY l.item_id, l.id
    `) as Row[]
    const planner = new CostPlanner(tx)
    const out: Row[] = []
    for (const r of rows) out.push({ ...r, cost: await planner.cost({ id: Number(r.item_id), method: r.costing_method, on_hand: Number(r.on_hand), value: Number(r.value), average: Number(r.average) }, Number(r.quantity)) })
    return out
  }

  /** Shows the exact entry posting would make, with account names, without changing anything. */
  static async previewDocument(org: string, id: number, options: { control_account_id?: number | null } = {}) {
    const sql = getSql()
    const doc = (await this.getDocument(org, id)) as Row
    const control = Number(options.control_account_id ?? doc.suggested_control_account_id ?? 0)
    const problems: string[] = []
    if (!control) problems.push(doc.kind === 'invoice' ? 'Choose the account that tracks what customers owe you.' : 'Choose the account that tracks what you owe suppliers.')
    if (!(Number(doc.total) > 0)) problems.push('This document has no amount.')
    const stock = await this.stockLines(sql as unknown as Pg, id)
    const lines = await this.entryForDocument(sql as unknown as Pg, doc, control || -1)
    if (doc.kind === 'invoice' && stock.length) {
      lines.push(...costOfSalesEntry(stock.map((s) => ({ expense_account_id: Number(s.expense_account_id), inventory_account_id: Number(s.inventory_account_id), amount: s.cost }))))
      const levels = (await sql`
        SELECT l.item_id, l.warehouse_id, l.quantity::float, w.is_default, w.name FROM public.stock_levels l JOIN public.warehouses w ON w.id = l.warehouse_id
        WHERE w.organization_id = ${org}::uuid AND l.item_id = ANY(${stock.map((s) => Number(s.item_id))}::bigint[])
      `) as Row[]
      const wanted: Record<string, number> = {}
      stock.forEach((s) => {
        const level = levels.find((l) => Number(l.item_id) === Number(s.item_id) && (s.warehouse_id ? Number(l.warehouse_id) === Number(s.warehouse_id) : l.is_default))
        const key = `${s.item_id}:${s.warehouse_id ?? ''}`
        wanted[key] = (wanted[key] ?? 0) + Number(s.quantity)
        if (wanted[key] > Number(level?.quantity ?? 0) + 1e-9) problems.push(`Only ${Number(level?.quantity ?? 0)} of ${s.item_name} in ${level?.name ?? 'that warehouse'}.`)
      })
    }
    const ids = lines.map((l) => l.account_id).filter((x) => x > 0)
    const names = (await sql`SELECT id, code, name FROM public.accounts WHERE organization_id = ${org}::uuid AND id = ANY(${ids}::bigint[])`) as Row[]
    return {
      problems,
      suggested_control_account_id: doc.suggested_control_account_id ? Number(doc.suggested_control_account_id) : null,
      lines: lines.filter((l) => l.account_id > 0).map((l) => {
        const a = names.find((x) => Number(x.id) === l.account_id)
        return { ...l, code: a?.code ?? '', name: a?.name ?? `Account ${l.account_id}` }
      }),
    }
  }

  static async postDocument(org: string, id: number, options: { control_account_id?: number | null } = {}) {
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [d] = (await tx`
        SELECT d.*, d.issue_date::text AS issue_text, COALESCE(c.receivable_account_id, m.payable_account_id) AS suggested
        FROM public.trade_documents d
        LEFT JOIN public.customers c ON c.id = d.customer_id
        LEFT JOIN public.supplier_account_mappings m ON m.supplier_id = d.supplier_id
        WHERE d.id = ${id} AND d.organization_id = ${org}::uuid FOR UPDATE OF d
      `) as Row[]
      if (!d) throw new Error('Document not found.')
      if (d.status !== 'draft') throw new Error('This document has already been posted.')
      if (!(Number(d.total) > 0)) throw new Error('This document has no amount.')
      const control = Number(options.control_account_id ?? d.suggested ?? 0)
      if (!control) throw new Error('Choose the account this goes to.')
      const lines = await this.entryForDocument(tx, d, control)
      await tx`SELECT id FROM public.inventory_items WHERE id IN (SELECT item_id FROM public.trade_document_lines WHERE document_id = ${id}) ORDER BY id FOR UPDATE`
      const stock = await this.stockLines(tx, id)
      const sale = d.kind === 'invoice'
      if (sale) lines.push(...costOfSalesEntry(stock.map((s) => ({ expense_account_id: Number(s.expense_account_id), inventory_account_id: Number(s.inventory_account_id), amount: s.cost }))))
      const what = sale ? 'Invoice' : 'Bill'
      const entry = await this.post(tx, org, { number: `JE-${d.number}`, date: d.issue_text, description: `${what} ${d.number}, ${d.party_name}`, reference: d.number }, lines)
      for (const s of stock) {
        const moved = (await DataServiceAdmin.applyInventoryTransaction(tx, {
          organization_id: org, item_id: Number(s.item_id), transaction_type: sale ? 'out' : 'in', quantity: sale ? -Number(s.quantity) : Number(s.quantity),
          unit_cost: sale ? null : Number(s.amount) / Number(s.quantity), total_cost: sale ? s.cost : Number(s.amount), journal_entry_id: entry, reference: d.number, description: `${what} ${d.number}, ${d.party_name}`,
          transaction_date: d.issue_text, created_by: acting(), warehouse_id: s.warehouse_id ? Number(s.warehouse_id) : null, source_type: 'document', source_id: id, serial_numbers: s.serial_numbers ?? null,
        } as never)) as Row
        await tx`UPDATE public.trade_document_lines SET cost_amount = ${sale ? s.cost : Number(s.amount)}, serial_numbers = ${moved.serials?.length ? moved.serials : null} WHERE id = ${s.id}`
      }
      await tx`UPDATE public.trade_documents SET status = 'posted', control_account_id = ${control}, journal_entry_id = ${entry}, updated_at = now() WHERE id = ${id}`
    })
    return this.getDocument(org, id)
  }

  static async recordPayment(org: string, documentId: number, form: { date: string; amount: number; bank_account_id: number; reference?: string | null }) {
    const date = requireDate(form.date)
    const amount = money(positive(form.amount, 'Amount'))
    if (!form.bank_account_id) throw new Error('Choose the bank or cash account.')
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [d] = (await tx`SELECT * FROM public.trade_documents WHERE id = ${documentId} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!d) throw new Error('Document not found.')
      if (d.status !== 'posted' && d.status !== 'partial') throw new Error(d.status === 'paid' ? 'This is already fully paid.' : 'Post this before recording a payment.')
      const balance = money(Number(d.total) - Number(d.amount_paid))
      if (amount > balance) throw new Error(`That's more than the ${balance.toFixed(2)} still open.`)
      const [{ n }] = (await tx`SELECT COUNT(*)::int + 1 AS n FROM public.trade_payments WHERE document_id = ${documentId}`) as Row[]
      const entry = await this.post(tx, org, { number: `JE-${d.number}-P${n}`, date, description: `Payment ${d.kind === 'invoice' ? 'from' : 'to'} ${d.party_name}, ${d.number}`, reference: label(form.reference) ?? d.number }, paymentEntry(d.kind, Number(d.control_account_id), Number(form.bank_account_id), amount))
      await tx`INSERT INTO public.trade_payments (organization_id, document_id, payment_date, amount, bank_account_id, reference, journal_entry_id, created_by) VALUES (${org}::uuid, ${documentId}, ${date}::date, ${amount}, ${form.bank_account_id}, ${label(form.reference)}, ${entry}, ${acting()}::uuid)`
      const paid = money(Number(d.amount_paid) + amount)
      await tx`UPDATE public.trade_documents SET amount_paid = ${paid}, status = ${paid >= Number(d.total) ? 'paid' : 'partial'}, updated_at = now() WHERE id = ${documentId}`
    })
    return this.getDocument(org, documentId)
  }

  /** Cancels a posted document by reversing its entry. One with payments has to have them dealt with first. */
  static async voidDocument(org: string, id: number, form: { reason: string; date?: string }) {
    const reason = label(form.reason)
    if (!reason) throw new Error('Say why this is being voided.')
    const date = form.date ? requireDate(form.date) : today()
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [d] = (await tx`SELECT *, issue_date::text AS issue_text FROM public.trade_documents WHERE id = ${id} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!d) throw new Error('Document not found.')
      if (d.status !== 'posted') throw new Error(d.status === 'draft' ? 'Delete a draft instead of voiding it.' : d.status === 'void' ? 'This is already void.' : 'This has payments against it, so it cannot be voided.')
      const [e] = (await tx`SELECT entry_number FROM public.journal_entries WHERE id = ${d.journal_entry_id}`) as Row[]
      const lines = (await tx`SELECT account_id, description, debit_amount, credit_amount FROM public.journal_entry_lines WHERE journal_entry_id = ${d.journal_entry_id} ORDER BY line_order`) as Row[]
      const reversal = await this.post(tx, org, { number: `REV-${e.entry_number}`, date, description: `Void ${d.number}: ${reason}`, reference: d.number, reverses: Number(d.journal_entry_id) }, reversalLines(lines.map((l) => ({ account_id: Number(l.account_id), description: l.description, debit: Number(l.debit_amount), credit: Number(l.credit_amount) }))))
      // Stock goes back the way it came, at the value it left or arrived at, which is what the reversal puts back in the books.
      const sale = d.kind === 'invoice'
      const stock = (await tx`SELECT item_id, warehouse_id, quantity::float * unit_factor::float AS quantity, cost_amount::float FROM public.trade_document_lines WHERE document_id = ${id} AND item_id IS NOT NULL ORDER BY item_id, id`) as Row[]
      // Movements were made in this same order, so each line undoes its own: same batches, serials and cost.
      const made = (await tx`SELECT id, item_id FROM public.inventory_transactions WHERE organization_id = ${org}::uuid AND source_type = 'document' AND source_id = ${id} AND transaction_type = ${sale ? 'out' : 'in'} ORDER BY item_id, id`) as Row[]
      for (let n = 0; n < stock.length; n++) {
        const s = stock[n]
        const cost = Number(s.cost_amount ?? 0)
        await DataServiceAdmin.applyInventoryTransaction(tx, {
          organization_id: org, item_id: Number(s.item_id), transaction_type: sale ? 'in' : 'out', quantity: sale ? Number(s.quantity) : -Number(s.quantity),
          unit_cost: null, total_cost: cost, journal_entry_id: reversal, reference: d.number, description: `Void ${d.number}: ${reason}`,
          transaction_date: date, created_by: acting(), warehouse_id: s.warehouse_id ? Number(s.warehouse_id) : null, source_type: 'document', source_id: id,
          from_transaction_ids: made[n] ? [Number(made[n].id)] : null, layer_date: d.issue_text,
        } as never)
      }
      // A voided bill's goods are still received, so they can go on a new bill.
      if (!sale) await tx`UPDATE public.goods_receipts SET bill_id = NULL WHERE bill_id = ${id}`
      await tx`UPDATE public.trade_documents SET status = 'void', void_reason = ${reason}, updated_at = now() WHERE id = ${id}`
    })
    return this.getDocument(org, id)
  }

  /** Age is measured from the due date. Payments dated after the as-of date still count as unpaid then. */
  static async getAgedReport(org: string, kind: 'invoice' | 'bill', asOf?: string) {
    const date = asOf ? requireDate(asOf) : today()
    const docs = (await getSql()`
      SELECT d.id, d.party_name, d.number, d.due_date::text AS due_date,
             (d.total - COALESCE((SELECT SUM(p.amount) FROM public.trade_payments p WHERE p.document_id = d.id AND p.payment_date <= ${date}::date), 0))::float AS balance
      FROM public.trade_documents d
      WHERE d.organization_id = ${org}::uuid AND d.kind = ${kind} AND d.status IN ('posted', 'partial', 'paid') AND d.issue_date <= ${date}::date
    `) as Row[]
    const open = docs.filter((d) => Number(d.balance) > 0.004).map((d) => ({ id: d.id, party_name: d.party_name, number: d.number, due_date: d.due_date, balance: Number(d.balance) }))
    return { as_of: date, ...agedReport(open, date), documents: open }
  }

  // ---- Tax ----

  /** On an accrual basis: tax counts from the document's date, whether or not it's been paid yet. */
  static async getTaxSummary(org: string, from: string, to: string) {
    requireDate(from); requireDate(to)
    if (to < from) throw new Error("The end date can't be before the start.")
    const sql = getSql()
    const rows = (await sql`
      SELECT d.kind, r.name AS rate_name, l.tax_rate::float AS rate, l.amount::float, l.tax_amount::float
      FROM public.trade_document_lines l
      JOIN public.trade_documents d ON d.id = l.document_id
      LEFT JOIN public.tax_rates r ON r.id = l.tax_rate_id
      WHERE d.organization_id = ${org}::uuid AND d.status IN ('posted', 'partial', 'paid') AND d.issue_date BETWEEN ${from}::date AND ${to}::date
    `) as Row[]
    return { from, to, ...taxSummary(rows.map((r) => ({ kind: r.kind, rate_name: r.rate_name, rate: Number(r.rate), amount: Number(r.amount), tax_amount: Number(r.tax_amount) }))) }
  }

  static listTaxReturns(org: string) {
    return getSql()`SELECT id, period_from::text AS period_from, period_to::text AS period_to, output_tax::float, input_tax::float, net_tax::float, reference, filed_at::text AS filed_at FROM public.tax_returns WHERE organization_id = ${org}::uuid ORDER BY period_to DESC LIMIT 60`
  }

  /** Keeps a record of what was filed. This doesn't file anything with a tax authority. */
  static async recordTaxReturn(org: string, form: { from: string; to: string; reference?: string | null }) {
    const s = await this.getTaxSummary(org, form.from, form.to)
    const sql = getSql()
    const [overlap] = (await sql`SELECT id FROM public.tax_returns WHERE organization_id = ${org}::uuid AND period_from <= ${form.to}::date AND period_to >= ${form.from}::date LIMIT 1`) as Row[]
    if (overlap) throw new Error('A return for part of this period is already recorded.')
    const rows = await sql`INSERT INTO public.tax_returns (organization_id, period_from, period_to, output_tax, input_tax, net_tax, reference, filed_by) VALUES (${org}::uuid, ${form.from}::date, ${form.to}::date, ${s.output_tax}, ${s.input_tax}, ${s.net_tax}, ${label(form.reference)}, ${acting()}::uuid) RETURNING id`
    return rows[0]
  }

  // ---- Bank reconciliation ----

  /** Importing the same statement twice adds nothing. Two identical lines in one file stay two lines. */
  static async importStatement(org: string, accountId: number, rows: { date: string; description: string; reference?: string; amount?: string; debit?: string; credit?: string }[]) {
    if (!Array.isArray(rows) || !rows.length) throw new Error('No statement lines found.')
    if (rows.length > 5000) throw new Error('Import up to 5,000 lines at a time.')
    const [a] = (await getSql()`SELECT id FROM public.accounts WHERE id = ${accountId} AND organization_id = ${org}::uuid`) as Row[]
    if (!a) throw new Error('Account not found.')
    const seen: Record<string, number> = {}
    const problems: string[] = []
    const clean: { date: string; description: string; reference: string | null; amount: number; key: string }[] = []
    rows.forEach((r, i) => {
      const amount = statementAmount(r)
      const date = String(r.date ?? '').trim()
      if (!DATE.test(date) || Number.isNaN(Date.parse(date))) return void problems.push(`Line ${i + 2}: the date must look like 2026-01-31.`)
      if (amount === null || amount === 0) return void problems.push(`Line ${i + 2}: no amount found.`)
      const description = label(r.description) ?? 'Bank line'
      const base = `${date}|${amount.toFixed(2)}|${description}|${label(r.reference) ?? ''}`
      seen[base] = (seen[base] ?? 0) + 1
      clean.push({ date, description, reference: label(r.reference), amount, key: `${base}|${seen[base]}` })
    })
    if (problems.length) throw new Error(problems.slice(0, 5).join(' '))
    let added = 0
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      for (const l of clean) {
        const inserted = await tx`
          INSERT INTO public.bank_statement_lines (organization_id, account_id, statement_date, description, reference, amount, dedupe_key)
          VALUES (${org}::uuid, ${accountId}, ${l.date}::date, ${l.description}, ${l.reference}, ${l.amount}, ${l.key})
          ON CONFLICT (organization_id, account_id, dedupe_key) DO NOTHING RETURNING id
        `
        added += inserted.length
      }
    })
    return { added, skipped: clean.length - added }
  }

  /** The bank's lines, this account's ledger lines the bank hasn't matched, and where the two stand. */
  static async getReconciliation(org: string, accountId: number, options: { as_of?: string; statement_balance?: number | null } = {}) {
    const asOf = options.as_of ? requireDate(options.as_of) : today()
    const sql = getSql()
    const lines = (await sql`
      SELECT id, statement_date::text AS date, description, reference, amount::float, status, matched_journal_line_id
      FROM public.bank_statement_lines
      WHERE organization_id = ${org}::uuid AND account_id = ${accountId} AND statement_date <= ${asOf}::date
      ORDER BY statement_date DESC, id DESC LIMIT 1000
    `) as Row[]
    const [first] = (await sql`SELECT MIN(statement_date)::text AS d FROM public.bank_statement_lines WHERE organization_id = ${org}::uuid AND account_id = ${accountId}`) as Row[]
    const from = first?.d ?? asOf
    const ledger = (await sql`
      SELECT l.id, e.entry_date::text AS date, e.entry_number, COALESCE(l.description, e.description) AS description, (l.debit_amount - l.credit_amount)::float AS amount
      FROM public.journal_entry_lines l JOIN public.journal_entries e ON e.id = l.journal_entry_id
      WHERE e.organization_id = ${org}::uuid AND l.account_id = ${accountId} AND e.entry_date BETWEEN (${from}::date - 7) AND ${asOf}::date
        AND NOT EXISTS (SELECT 1 FROM public.bank_statement_lines b WHERE b.matched_journal_line_id = l.id)
      ORDER BY e.entry_date DESC, l.id DESC LIMIT 1000
    `) as Row[]
    const [book] = (await sql`
      SELECT COALESCE(SUM(l.debit_amount - l.credit_amount), 0)::float AS balance
      FROM public.journal_entry_lines l JOIN public.journal_entries e ON e.id = l.journal_entry_id
      WHERE e.organization_id = ${org}::uuid AND l.account_id = ${accountId} AND e.entry_date <= ${asOf}::date
    `) as Row[]
    const unmatched = lines.filter((l) => l.status === 'unmatched')
    const ledgerRows = ledger.map((l) => ({ id: Number(l.id), date: String(l.date), entry_number: String(l.entry_number), description: String(l.description ?? ''), amount: Number(l.amount) }))
    // Entries from the week before the statement can still match its lines, but only later ones count as waiting on the bank.
    const outstanding = ledgerRows.filter((l) => l.date >= from)
    return {
      as_of: asOf,
      book_balance: money(Number(book.balance)),
      lines: lines.map((l) => ({ ...l, id: Number(l.id), amount: Number(l.amount), candidates: l.status === 'unmatched' ? matchCandidates({ date: l.date, amount: Number(l.amount) }, ledgerRows).slice(0, 3) : [] })),
      outstanding,
      summary: options.statement_balance === undefined || options.statement_balance === null ? null : reconciliation({ statement_balance: Number(options.statement_balance), book_balance: Number(book.balance), outstanding, unmatched_statement: unmatched.map((l) => ({ amount: Number(l.amount) })) }),
      history: await sql`SELECT id, as_of::text AS as_of, statement_balance::float, book_balance::float, completed_at::text AS completed_at FROM public.bank_reconciliations WHERE organization_id = ${org}::uuid AND account_id = ${accountId} ORDER BY as_of DESC LIMIT 12`,
    }
  }

  static async matchStatementLine(org: string, lineId: number, journalLineId: number) {
    await getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [b] = (await tx`SELECT * FROM public.bank_statement_lines WHERE id = ${lineId} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!b) throw new Error('Bank line not found.')
      if (b.status !== 'unmatched') throw new Error('This line is already dealt with.')
      const [l] = (await tx`
        SELECT l.account_id, (l.debit_amount - l.credit_amount)::float AS amount
        FROM public.journal_entry_lines l JOIN public.journal_entries e ON e.id = l.journal_entry_id
        WHERE l.id = ${journalLineId} AND e.organization_id = ${org}::uuid
      `) as Row[]
      if (!l) throw new Error('Ledger line not found.')
      if (Number(l.account_id) !== Number(b.account_id)) throw new Error('That line is on a different account.')
      if (money(Number(l.amount)) !== money(Number(b.amount))) throw new Error("The amounts don't match.")
      const [used] = (await tx`SELECT id FROM public.bank_statement_lines WHERE matched_journal_line_id = ${journalLineId} LIMIT 1`) as Row[]
      if (used) throw new Error('That ledger line is already matched to another bank line.')
      await tx`UPDATE public.bank_statement_lines SET status = 'matched', matched_journal_line_id = ${journalLineId} WHERE id = ${lineId}`
    })
  }

  static async unmatchStatementLine(org: string, lineId: number) {
    await getSql()`UPDATE public.bank_statement_lines SET status = 'unmatched', matched_journal_line_id = NULL WHERE id = ${lineId} AND organization_id = ${org}::uuid`
  }

  static async ignoreStatementLine(org: string, lineId: number) {
    const rows = await getSql()`UPDATE public.bank_statement_lines SET status = 'ignored' WHERE id = ${lineId} AND organization_id = ${org}::uuid AND status = 'unmatched' RETURNING id`
    if (!rows.length) throw new Error('This line is already dealt with.')
  }

  /** For something the books don't have yet, like a bank fee: records it and matches it in one step. */
  static async createEntryFromStatementLine(org: string, lineId: number, form: { offset_account_id: number; description?: string }) {
    if (!form.offset_account_id) throw new Error('Choose what this was for.')
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      const [b] = (await tx`SELECT *, statement_date::text AS date_text FROM public.bank_statement_lines WHERE id = ${lineId} AND organization_id = ${org}::uuid FOR UPDATE`) as Row[]
      if (!b) throw new Error('Bank line not found.')
      if (b.status !== 'unmatched') throw new Error('This line is already dealt with.')
      const amount = money(Math.abs(Number(b.amount)))
      const bank = Number(b.account_id)
      const offset = Number(form.offset_account_id)
      const lines: EntryLine[] = Number(b.amount) > 0
        ? [{ account_id: bank, debit: amount, credit: 0, description: null }, { account_id: offset, debit: 0, credit: amount, description: null }]
        : [{ account_id: offset, debit: amount, credit: 0, description: null }, { account_id: bank, debit: 0, credit: amount, description: null }]
      const entry = await this.post(tx, org, { number: `JE-BANK-${lineId}`, date: b.date_text, description: label(form.description) ?? b.description, reference: b.reference }, lines)
      const [own] = (await tx`SELECT id FROM public.journal_entry_lines WHERE journal_entry_id = ${entry} AND account_id = ${bank} LIMIT 1`) as Row[]
      await tx`UPDATE public.bank_statement_lines SET status = 'matched', matched_journal_line_id = ${own.id} WHERE id = ${lineId}`
      return { entry_id: entry }
    })
  }

  static async completeReconciliation(org: string, accountId: number, form: { as_of: string; statement_balance: number }) {
    const statement = Number(form.statement_balance)
    if (!Number.isFinite(statement)) throw new Error('Enter the balance on the statement.')
    const r = await this.getReconciliation(org, accountId, { as_of: form.as_of, statement_balance: statement })
    if (!r.summary?.balanced) throw new Error(r.summary?.difference ? `There's still a difference of ${r.summary.difference.toFixed(2)}.` : 'Some bank lines are still unmatched.')
    const rows = await getSql()`INSERT INTO public.bank_reconciliations (organization_id, account_id, as_of, statement_balance, book_balance, completed_by) VALUES (${org}::uuid, ${accountId}, ${form.as_of}::date, ${statement}, ${r.book_balance}, ${acting()}::uuid) RETURNING id`
    return rows[0]
  }

  // ---- Budgets and forecasts ----

  static listBudgets(org: string) {
    return getSql()`
      SELECT b.id, b.name, b.year, COALESCE(SUM(l.amount), 0)::float AS total
      FROM public.budgets b LEFT JOIN public.budget_lines l ON l.budget_id = b.id
      WHERE b.organization_id = ${org}::uuid GROUP BY b.id ORDER BY b.year DESC, b.name
    `
  }

  static async saveBudget(org: string, form: { id?: number; name: string; year: number; lines: { account_id: number; month: number; amount: number }[] }) {
    const name = label(form.name)
    if (!name) throw new Error('Name the budget.')
    const year = Number(form.year)
    if (!Number.isInteger(year) || year < 2000 || year > 2100) throw new Error('Enter a real year.')
    return getSql().begin(async (raw) => {
      const tx = raw as unknown as Pg
      let id = Number(form.id ?? 0)
      if (id) {
        const rows = await tx`UPDATE public.budgets SET name = ${name}, year = ${year} WHERE id = ${id} AND organization_id = ${org}::uuid RETURNING id`
        if (!rows.length) throw new Error('Budget not found.')
      } else {
        const [row] = (await tx`INSERT INTO public.budgets (organization_id, name, year, created_by) VALUES (${org}::uuid, ${name}, ${year}, ${acting()}::uuid) RETURNING id`) as Row[]
        id = Number(row.id)
      }
      const ids = Array.from(new Set((form.lines ?? []).map((l) => Number(l.account_id))))
      const known = ids.length ? ((await tx`SELECT id FROM public.accounts WHERE organization_id = ${org}::uuid AND account_type IN ('revenue', 'expense') AND id = ANY(${ids}::bigint[])`) as Row[]) : []
      if (known.length !== ids.length) throw new Error('A budget covers income and expense accounts only.')
      await tx`DELETE FROM public.budget_lines WHERE budget_id = ${id}`
      for (const l of form.lines ?? []) {
        const amount = Number(l.amount)
        if (!amount) continue
        if (!Number.isFinite(amount) || amount < 0) throw new Error("A budget amount can't be negative.")
        if (!(l.month >= 1 && l.month <= 12)) throw new Error('Unknown month.')
        await tx`INSERT INTO public.budget_lines (budget_id, account_id, month, amount) VALUES (${id}, ${Number(l.account_id)}, ${l.month}, ${money(amount)})`
      }
      return { id }
    })
  }

  static async deleteBudget(org: string, id: number) {
    await getSql()`DELETE FROM public.budgets WHERE id = ${id} AND organization_id = ${org}::uuid`
  }

  /** Budget against what actually happened, per account and month. Calendar months of the budget's year. */
  static async getBudgetReport(org: string, id: number) {
    const sql = getSql()
    const [b] = (await sql`SELECT id, name, year FROM public.budgets WHERE id = ${id} AND organization_id = ${org}::uuid`) as Row[]
    if (!b) throw new Error('Budget not found.')
    const budgeted = (await sql`
      SELECT l.account_id, l.month, l.amount::float, a.code, a.name, a.account_type::text AS account_type
      FROM public.budget_lines l JOIN public.accounts a ON a.id = l.account_id WHERE l.budget_id = ${id}
    `) as Row[]
    const actual = (await sql`
      SELECT l.account_id, EXTRACT(MONTH FROM e.entry_date)::int AS month, a.code, a.name, a.account_type::text AS account_type,
             SUM(l.debit_amount)::float AS dr, SUM(l.credit_amount)::float AS cr
      FROM public.journal_entry_lines l
      JOIN public.journal_entries e ON e.id = l.journal_entry_id
      JOIN public.accounts a ON a.id = l.account_id
      WHERE e.organization_id = ${org}::uuid AND a.account_type IN ('revenue', 'expense')
        AND e.entry_date >= make_date(${Number(b.year)}::int, 1, 1) AND e.entry_date < make_date(${Number(b.year) + 1}::int, 1, 1)
      GROUP BY 1, 2, 3, 4, 5
    `) as Row[]
    type Acc = { account_id: number; code: string; name: string; account_type: string; budget: number[]; actual: number[]; budget_total: number; actual_total: number; variance: number }
    const accounts: Acc[] = []
    const row = (r: Row) => {
      let a = accounts.find((x) => x.account_id === Number(r.account_id))
      if (!a) {
        a = { account_id: Number(r.account_id), code: r.code, name: r.name, account_type: r.account_type, budget: Array(12).fill(0), actual: Array(12).fill(0), budget_total: 0, actual_total: 0, variance: 0 }
        accounts.push(a)
      }
      return a
    }
    budgeted.forEach((r) => { row(r).budget[r.month - 1] = Number(r.amount) })
    actual.forEach((r) => { row(r).actual[r.month - 1] = money(netAmountForAccountType(Number(r.dr), Number(r.cr), r.account_type)) })
    accounts.forEach((a) => {
      a.budget_total = money(a.budget.reduce((s, v) => s + v, 0))
      a.actual_total = money(a.actual.reduce((s, v) => s + v, 0))
      a.variance = money(a.actual_total - a.budget_total)
    })
    accounts.sort((x, y) => (x.account_type === y.account_type ? x.code.localeCompare(y.code) : x.account_type === 'revenue' ? -1 : 1))
    const total = (t: string, k: 'budget_total' | 'actual_total') => money(accounts.filter((a) => a.account_type === t).reduce((s, a) => s + a[k], 0))
    return { id: b.id, name: b.name, year: Number(b.year), accounts, revenue: { budget: total('revenue', 'budget_total'), actual: total('revenue', 'actual_total') }, expense: { budget: total('expense', 'budget_total'), actual: total('expense', 'actual_total') } }
  }

  /** An estimate from the last 12 months plus what's already due in or out. It says how much history it's based on. */
  static async getForecast(org: string, months = 6) {
    const n = Math.min(Math.max(Math.floor(Number(months)) || 6, 1), 12)
    const sql = getSql()
    const history = (await sql`
      WITH m AS (SELECT generate_series(date_trunc('month', now()) - interval '12 months', date_trunc('month', now()) - interval '1 month', interval '1 month')::date AS start)
      SELECT to_char(m.start, 'YYYY-MM') AS month,
        COALESCE(SUM(CASE WHEN a.account_type = 'revenue' THEN l.credit_amount - l.debit_amount END), 0)::float AS revenue,
        COALESCE(SUM(CASE WHEN a.account_type = 'expense' THEN l.debit_amount - l.credit_amount END), 0)::float AS expenses
      FROM m
      LEFT JOIN public.journal_entries e ON e.organization_id = ${org}::uuid AND date_trunc('month', e.entry_date)::date = m.start
      LEFT JOIN public.journal_entry_lines l ON l.journal_entry_id = e.id
      LEFT JOIN public.accounts a ON a.id = l.account_id
      GROUP BY m.start ORDER BY m.start
    `) as Row[]
    const months_of_history = history.filter((h) => Number(h.revenue) || Number(h.expenses)).length
    const revenue = forecastSeries(history.map((h) => Number(h.revenue)), n)
    const expenses = forecastSeries(history.map((h) => Number(h.expenses)), n)
    const [cash] = (await sql`
      SELECT COALESCE(SUM(l.debit_amount - l.credit_amount), 0)::float AS balance
      FROM public.journal_entry_lines l JOIN public.accounts a ON a.id = l.account_id
      WHERE a.organization_id = ${org}::uuid AND a.account_type = 'asset'
        AND (a.name ~* '(cash|bank)' OR a.id IN (SELECT account_id FROM public.bank_statement_lines WHERE organization_id = ${org}::uuid))
    `) as Row[]
    const open = (await sql`
      SELECT kind, to_char(GREATEST(due_date, CURRENT_DATE), 'YYYY-MM') AS month, SUM(total - amount_paid)::float AS amount
      FROM public.trade_documents WHERE organization_id = ${org}::uuid AND status IN ('posted', 'partial') GROUP BY 1, 2
    `) as Row[]
    const now = new Date()
    let running = money(Number(cash.balance))
    const start = running
    const rows = Array.from({ length: n }, (_v, i) => {
      const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth() + i, 1))
      const month = d.toISOString().slice(0, 7)
      const due = (kind: string) => money(open.filter((o) => o.kind === kind && o.month === month).reduce((s, o) => s + Number(o.amount), 0))
      const receipts = due('invoice')
      const payments = due('bill')
      const net = money(revenue[i] - expenses[i])
      running = money(running + net)
      return { month, revenue: revenue[i], expenses: expenses[i], net, receivable_due: receipts, payable_due: payments, cash: running }
    })
    return { months_of_history, confidence: months_of_history >= 6 ? 'reasonable' : months_of_history >= 3 ? 'low' : 'very low', cash_today: start, history, rows }
  }

  // ---- Overview, for screens and the agent ----

  static async getWorkSummary(org: string) {
    const [c] = (await getSql()`
      SELECT
        (SELECT COUNT(*)::int FROM public.trade_documents WHERE organization_id = ${org}::uuid AND kind = 'invoice' AND status IN ('posted', 'partial') AND due_date < CURRENT_DATE) AS overdue_invoices,
        (SELECT COUNT(*)::int FROM public.trade_documents WHERE organization_id = ${org}::uuid AND kind = 'bill' AND status IN ('posted', 'partial') AND due_date < CURRENT_DATE) AS overdue_bills,
        (SELECT COUNT(*)::int FROM public.bank_statement_lines WHERE organization_id = ${org}::uuid AND status = 'unmatched') AS unmatched_bank_lines
    `) as Row[]
    return c
  }
}
