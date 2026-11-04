import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Plus, Printer, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { AskChip } from '@/components/agent-panel'
import { Badge, Chips, type Tone } from '@/components/chips'
import { Choice, ConfirmDelete, FormBody, Modal, Stat, Stats, Text, selectClass, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, Table, Toolbar, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, iso, num, q, refreshBooks, today, type Account, type Id } from '@/lib/data'
import { cn } from '@/lib/utils'
import { items, unitsQuery, warehousesQuery } from '@/routes/inventory'

export type Kind = 'invoice' | 'bill'
type DocRow = { id: Id; kind: Kind; number: string; status: string; party_name: string; issue_date: string; due_date: string; subtotal: number; tax_total: number; total: number; amount_paid: number; balance: number }
type DocLine = { id: Id; description: string; account_id: Id; quantity: number; unit_price: number; tax_rate_id: Id | null; tax_rate: number; amount: number; tax_amount: number; tax_name?: string | null; item_id?: Id | null; warehouse_id?: Id | null; sku?: string | null; unit_id?: Id | null; unit_name?: string | null; unit_factor?: number; serial_numbers?: string[] | null; credited_quantity?: number; track_serials?: boolean }
export type Doc = DocRow & { customer_id: Id | null; supplier_id: Id | null; notes: string | null; void_reason: string | null; lines: DocLine[]; payments: { id: Id; payment_date: string; amount: number; reference: string | null; credit_note_id?: Id | null }[]; credit_notes?: { id: Id; number: string; credit_date: string; reason: string; total: number; applied: number; refund: number }[] }
type Customer = { id: Id; name: string; email: string | null; phone: string | null; address: string | null; tax_id: string | null; receivable_account_id: Id | null; balance: number }
type Rate = { id: Id; name: string; rate: number; is_active: boolean }
type Preview = { problems: string[]; suggested_control_account_id: number | null; lines: { account_id: number; code: string; name: string; debit: number; credit: number }[] }

const REFRESH = ['documents', 'document', 'customers', 'aged', 'work-summary', 'tax', 'stock', 'low-stock', 'movements']
const docs = (org: string, kind: Kind) => q<DocRow[]>(['documents', org, kind], 'BooksService', 'listDocuments', [org, kind])
export const customersQuery = (org: string) => q<Customer[]>(['customers', org], 'BooksService', 'listCustomers', [org])
export const ratesQuery = (org: string) => q<Rate[]>(['tax', org, 'rates'], 'BooksService', 'listTaxRates', [org])
const postable = (rows: Account[] | undefined, ...types: string[]) => (rows ?? []).filter((a) => a.is_postable !== false && types.includes(a.account_type ?? '')).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))

const overdue = (d: DocRow) => (d.status === 'posted' || d.status === 'partial') && d.due_date.slice(0, 10) < today()
export function statusBadge(d: Pick<DocRow, 'status' | 'due_date'>) {
  if ((d.status === 'posted' || d.status === 'partial') && d.due_date.slice(0, 10) < today()) return { label: 'Overdue', tone: 'bad' as Tone }
  const map: Record<string, { label: string; tone: Tone }> = { draft: { label: 'Draft', tone: 'neutral' }, posted: { label: 'Open', tone: 'warn' }, partial: { label: 'Part paid', tone: 'warn' }, paid: { label: 'Paid', tone: 'good' }, void: { label: 'Void', tone: 'neutral' } }
  return map[d.status] ?? { label: d.status, tone: 'neutral' as Tone }
}
const WORDS = {
  invoice: { title: 'Invoices', one: 'invoice', sub: 'What you have billed customers, and who has paid.', who: 'Customer', owed: 'Customers owe you', control: 'Tracks what customers owe', ask: 'Who owes me the most, and what should I chase first?' },
  bill: { title: 'Bills', one: 'bill', sub: 'What suppliers have billed you, and what is still to pay.', who: 'Supplier', owed: 'You owe suppliers', control: 'Tracks what you owe suppliers', ask: 'Which bills should I pay first?' },
}

function Documents({ kind }: { kind: Kind }) {
  const { org, pro } = useApp()
  const w = WORDS[kind]
  const list = useQuery(docs(org.id, kind))
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const [opened, setOpened] = useState<Id | null>(null)
  const [editing, setEditing] = useState<Doc | 'new' | null>(null)
  const all = useMemo(() => list.data ?? [], [list.data])
  const test: Record<string, (d: DocRow) => boolean> = { draft: (d) => d.status === 'draft', open: (d) => d.status === 'posted' || d.status === 'partial', overdue, paid: (d) => d.status === 'paid', void: (d) => d.status === 'void' }
  const count = (s: string) => all.filter(test[s]).length
  const s = search.trim().toLowerCase()
  const rows = all.filter((d) => (status === 'all' || test[status](d)) && (!s || `${d.number} ${d.party_name}`.toLowerCase().includes(s)))
  const open = all.filter(test.open)
  const sum = (r: DocRow[]) => r.reduce((t, d) => t + num(d.balance), 0)

  return (
    <Screen
      title={w.title}
      sub={w.sub}
      search={<SearchIcon label={`Search ${w.title.toLowerCase()}`} value={search} onChange={setSearch} />}
      actions={<button className={btn.primary} onClick={() => setEditing('new')}><Plus className="size-3.5 mr-1.5" />New {w.one}</button>}
    >
      <Stats cols={3}>
        <Stat label={w.owed} value={`${org.currency} ${figure(sum(open), 0)}`} />
        <Stat label="Overdue" value={`${org.currency} ${figure(sum(all.filter(overdue)), 0)}`} tone={all.some(overdue) ? 'warn' : undefined} />
        <Stat label="Drafts" value={count('draft')} />
      </Stats>
      <Toolbar>
        <Chips label="Status" value={status} onChange={setStatus} options={[{ id: 'all', label: 'All', count: all.length }, { id: 'draft', label: 'Drafts', count: count('draft') }, { id: 'open', label: 'Open', count: count('open') }, { id: 'overdue', label: 'Overdue', count: count('overdue') }, { id: 'paid', label: 'Paid', count: count('paid') }, { id: 'void', label: 'Void', count: count('void') }]} />
        <span className="ml-auto"><AskChip prompt={w.ask}>{w.ask}</AskChip></span>
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title={`No ${w.title.toLowerCase()} yet`} body={`Create your first ${w.one}, or ask the agent to draft one.`} /> : null)}>
        {() => rows.length === 0 ? <Empty title="No matches" body="Try another word or filter." /> : (
          <Paged rows={rows}>
            {(page, pager) => (
              <Table min={680} footer={pager}>
                <thead><tr><Head>Number</Head><Head>{w.who}</Head><Head>Status</Head><Head>Date</Head><Head>Due</Head>{pro ? <Head right>Total</Head> : null}<Head right>Still to {kind === 'invoice' ? 'collect' : 'pay'}</Head></tr></thead>
                <tbody>
                  {page.map((d) => {
                    const b = statusBadge(d)
                    return (
                      <tr key={d.id} tabIndex={0} className="cursor-pointer hover:bg-accent/50 focus-visible:bg-accent/50 outline-none" onClick={() => setOpened(d.id)} onKeyDown={(e) => { if (e.key === 'Enter') setOpened(d.id) }}>
                        <Cell className="fig text-[12.5px]">{d.number}</Cell>
                        <Cell className="max-w-0 w-full truncate">{d.party_name}</Cell>
                        <Cell><Badge dot tone={b.tone}>{b.label}</Badge></Cell>
                        <Cell className="text-muted-foreground">{shortDate(d.issue_date)}</Cell>
                        <Cell className="text-muted-foreground">{shortDate(d.due_date)}</Cell>
                        {pro ? <Cell right>{figure(num(d.total), org.decimals)}</Cell> : null}
                        <Cell right>{d.status === 'void' || d.status === 'draft' ? '' : figure(num(d.balance), org.decimals)}</Cell>
                      </tr>
                    )
                  })}
                </tbody>
              </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {opened !== null ? <DocumentDetail id={opened} kind={kind} onClose={() => setOpened(null)} onEdit={(d) => { setOpened(null); setEditing(d) }} /> : null}
      {editing ? <DocumentForm kind={kind} doc={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={(id) => { setEditing(null); setOpened(id) }} /> : null}
    </Screen>
  )
}
export const Invoices = () => <Documents kind="invoice" />
export const Bills = () => <Documents kind="bill" />

type FormLine = { key: number; item_id: string; unit_id: string; serials: string; description: string; account_id: string; quantity: string; unit_price: string; tax_rate_id: string }
const plusDays = (d: string, n: number) => { const x = new Date(`${d}T00:00:00`); x.setDate(x.getDate() + n); return iso(x) }

function DocumentForm({ kind, doc, onClose, onSaved }: { kind: Kind; doc: Doc | null; onClose: () => void; onSaved: (id: Id) => void }) {
  const { org } = useApp()
  const w = WORDS[kind]
  const chart = useQuery(accounts(org.id))
  const customers = useQuery({ ...customersQuery(org.id), enabled: kind === 'invoice' })
  const suppliers = useQuery({ ...q<{ id: Id; name: string }[]>(['supplier-picker', org.id], 'SupplierService', 'getSuppliersForVoucher', [org.id]), enabled: kind === 'bill' })
  const rates = useQuery(ratesQuery(org.id))
  const stock = useQuery(items(org.id))
  const units = useQuery(unitsQuery(org.id))
  const warehouses = useQuery(warehousesQuery(org.id))
  const openWarehouses = (warehouses.data ?? []).filter((w) => w.is_active)
  const [warehouse, setWarehouse] = useState(String(doc?.lines.find((l) => l.warehouse_id)?.warehouse_id ?? ''))
  const [party, setParty] = useState(String((kind === 'invoice' ? doc?.customer_id : doc?.supplier_id) ?? ''))
  const [name, setName] = useState(doc && !doc.customer_id && !doc.supplier_id ? doc.party_name : '')
  const [issue, setIssue] = useState(doc?.issue_date.slice(0, 10) ?? today())
  const [due, setDue] = useState(doc?.due_date.slice(0, 10) ?? plusDays(today(), 30))
  const [notes, setNotes] = useState(doc?.notes ?? '')
  const [lines, setLines] = useState<FormLine[]>(doc?.lines.map((l, i) => ({ key: i + 1, item_id: l.item_id ? String(l.item_id) : '', unit_id: l.unit_id ? String(l.unit_id) : '', serials: (l.serial_numbers ?? []).join(', '), description: l.description, account_id: String(l.account_id), quantity: String(l.quantity), unit_price: String(l.unit_price), tax_rate_id: l.tax_rate_id ? String(l.tax_rate_id) : '' })) ?? [{ key: 1, item_id: '', unit_id: '', serials: '', description: '', account_id: '', quantity: '1', unit_price: '', tax_rate_id: '' }])
  const [next, setNext] = useState((doc?.lines.length ?? 1) + 1)
  const options = postable(chart.data, ...(kind === 'invoice' ? ['revenue'] : ['expense', 'asset']))
  const active = (rates.data ?? []).filter((r) => r.is_active)
  const rateOf = (id: string) => num(active.find((r) => String(r.id) === id)?.rate)
  const round = (n: number) => Math.round(n * 100) / 100
  const subtotal = lines.reduce((s, l) => s + round(Number(l.quantity) * Number(l.unit_price) || 0), 0)
  const tax = lines.reduce((s, l) => s + round(round(Number(l.quantity) * Number(l.unit_price) || 0) * rateOf(l.tax_rate_id) / 100), 0)
  const update = (key: number, patch: Partial<FormLine>) => setLines((ls) => ls.map((l) => (l.key === key ? { ...l, ...patch } : l)))
  // An item fills in the line. On a bill its stock account is always used, so there is no account to choose.
  const pick = (key: number, id: string) => {
    const item = stock.data?.find((i) => String(i.id) === id)
    update(key, !item ? { item_id: '', unit_id: '', serials: '' } : {
      item_id: id,
      unit_id: '',
      serials: '',
      description: item.name,
      account_id: kind === 'invoice' && item.income_account_id ? String(item.income_account_id) : kind === 'bill' ? '' : lines.find((l) => l.key === key)?.account_id ?? '',
      unit_price: kind === 'invoice' ? (item.selling_price == null ? '' : String(num(item.selling_price))) : num(item.average_unit_cost) ? String(num(item.average_unit_cost)) : '',
    })
  }
  const unitsOf = (l: FormLine) => (units.data ?? []).filter((u) => String(u.item_id) === l.item_id)
  const itemOf = (l: FormLine) => stock.data?.find((i) => String(i.id) === l.item_id)
  // A price is per the unit chosen, so changing the unit moves the price with it.
  const pickUnit = (l: FormLine, id: string) => {
    const was = num(unitsOf(l).find((u) => String(u.id) === l.unit_id)?.factor) || 1
    const now = num(unitsOf(l).find((u) => String(u.id) === id)?.factor) || 1
    update(l.key, { unit_id: id, unit_price: l.unit_price ? String(Math.round((Number(l.unit_price) / was) * now * 10000) / 10000) : '' })
  }
  const stockAccount = (l: FormLine) => kind === 'bill' && Boolean(l.item_id)
  const ready = (party || name.trim()) && lines.every((l) => l.description.trim() && (l.account_id || stockAccount(l)) && Number(l.quantity) > 0 && l.unit_price !== '')
  const save = useSave(() => call<{ id: Id }>('BooksService', 'saveDocument', [org.id, {
    id: doc?.id,
    kind,
    customer_id: kind === 'invoice' && party ? Number(party) : null,
    supplier_id: kind === 'bill' && party ? Number(party) : null,
    party_name: name.trim() || undefined,
    issue_date: issue,
    due_date: due,
    notes: notes.trim() || null,
    lines: lines.map((l) => ({ description: l.description.trim(), account_id: l.account_id ? Number(l.account_id) : null, quantity: Number(l.quantity), unit_price: Number(l.unit_price), tax_rate_id: l.tax_rate_id ? Number(l.tax_rate_id) : null, item_id: l.item_id ? Number(l.item_id) : null, warehouse_id: l.item_id && warehouse ? Number(warehouse) : null, unit_id: l.unit_id ? Number(l.unit_id) : null, serial_numbers: l.serials.trim() || null })),
  }]), { success: 'Draft saved. It is not in your books until you post it.', refresh: REFRESH, onDone: (r) => onSaved(r.id) })
  const people = (kind === 'invoice' ? customers.data : suppliers.data) ?? []

  return (
    <Modal wide open onClose={onClose} title={doc ? `Edit ${doc.number}` : `New ${w.one}`}>
      <FormBody onSubmit={() => save.mutate()} submit="Save draft" pending={save.isPending} onCancel={onClose} disabled={!ready}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label={w.who} placeholder="Choose, or type a name" value={party} onChange={(v) => { setParty(v); if (v) setName('') }} options={people.map((p) => ({ value: String(p.id), label: p.name }))} />
          {party ? <span className="hidden sm:block" /> : <Text label={`Or just a name`} value={name} onChange={setName} />}
          <Text label={kind === 'invoice' ? 'Invoice date' : 'Bill date'} type="date" value={issue} onChange={(v) => { setIssue(v); if (v && due < v) setDue(v) }} />
          <Text label="Due date" type="date" min={issue} value={due} onChange={setDue} />
          {openWarehouses.length > 1 && lines.some((l) => l.item_id) ? <Choice label={kind === 'invoice' ? 'Items leave from' : 'Items arrive at'} placeholder="Default warehouse" value={warehouse} onChange={setWarehouse} options={openWarehouses.map((w) => ({ value: String(w.id), label: w.name }))} /> : null}
        </div>
        <div className="flex flex-col gap-2">
          <div className="hidden md:grid grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_minmax(0,1fr)_56px_84px_minmax(0,0.7fr)_24px] gap-1.5 text-[12px] text-muted-foreground"><span>Stock item</span><span>Description</span><span>{kind === 'invoice' ? 'Income account' : 'Cost account'}</span><span className="text-right">Qty</span><span className="text-right">Price</span><span>Tax</span><span /></div>
          {lines.map((l) => (
            <div key={l.key} className="grid grid-cols-2 md:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)_minmax(0,1fr)_56px_84px_minmax(0,0.7fr)_24px] gap-1.5 items-center max-md:border-b max-md:border-border max-md:pb-2">
              <select aria-label="Stock item" value={l.item_id} onChange={(e) => pick(l.key, e.target.value)} className={cn(selectClass, 'max-md:col-span-2')}>
                <option value="">Not a stock item</option>
                {(stock.data ?? []).map((i) => <option key={i.id} value={String(i.id)}>{i.sku} · {i.name}</option>)}
              </select>
              <Input aria-label="Description" placeholder="Description" value={l.description} onChange={(e) => update(l.key, { description: e.target.value })} className="h-8 max-md:col-span-2" />
              {stockAccount(l) ? <span className="h-8 flex items-center px-2 text-[13px] text-muted-foreground max-md:col-span-2">Stock account</span> : (
              <select aria-label="Account" value={l.account_id} onChange={(e) => update(l.key, { account_id: e.target.value })} className={cn(selectClass, 'max-md:col-span-2')}>
                <option value="">Choose account</option>
                {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
              </select>
              )}
              <Input aria-label="Quantity" inputMode="decimal" value={l.quantity} onChange={(e) => update(l.key, { quantity: e.target.value })} className="h-8 text-right fig" />
              <Input aria-label="Price" inputMode="decimal" placeholder="0.00" value={l.unit_price} onChange={(e) => update(l.key, { unit_price: e.target.value })} className="h-8 text-right fig" />
              <select aria-label="Tax" value={l.tax_rate_id} onChange={(e) => update(l.key, { tax_rate_id: e.target.value })} className={selectClass}>
                <option value="">No tax</option>
                {active.map((r) => <option key={r.id} value={String(r.id)}>{r.name} {r.rate}%</option>)}
              </select>
              <button type="button" aria-label="Remove line" disabled={lines.length < 2} onClick={() => setLines((ls) => ls.filter((x) => x.key !== l.key))} className="grid place-items-center text-muted-foreground cursor-pointer disabled:opacity-30"><X className="size-3.5" /></button>
              {unitsOf(l).length || itemOf(l)?.track_serials ? (
                <div className="col-span-full grid sm:grid-cols-[140px_minmax(0,1fr)] gap-1.5 mb-1">
                  {unitsOf(l).length ? (
                    <select aria-label="Unit" value={l.unit_id} onChange={(e) => pickUnit(l, e.target.value)} className={selectClass}>
                      <option value="">{itemOf(l)?.unit_of_measure}</option>
                      {unitsOf(l).map((u) => <option key={u.id} value={String(u.id)}>{u.name} ({u.factor})</option>)}
                    </select>
                  ) : <span className="max-sm:hidden" />}
                  {itemOf(l)?.track_serials ? <Input aria-label="Serial numbers" placeholder={kind === 'invoice' ? 'Serial numbers, separated by commas. Blank takes the oldest.' : 'Serial numbers, separated by commas. Blank creates them.'} value={l.serials} onChange={(e) => update(l.key, { serials: e.target.value })} className="h-8" /> : null}
                </div>
              ) : null}
            </div>
          ))}
          <div className="flex flex-wrap items-center justify-between gap-3 mt-1 text-[13px]">
            <button type="button" onClick={() => { setLines((ls) => [...ls, { key: next, item_id: '', unit_id: '', serials: '', description: '', account_id: '', quantity: '1', unit_price: '', tax_rate_id: '' }]); setNext((k) => k + 1) }} className="inline-flex items-center gap-1 font-medium cursor-pointer"><Plus className="size-3.5" />Add line</button>
            <span className="flex gap-4"><span>Subtotal <span className="fig ml-1">{figure(subtotal, org.decimals)}</span></span><span>Tax <span className="fig ml-1">{figure(tax, org.decimals)}</span></span><span className="font-semibold">Total <span className="fig ml-1">{figure(subtotal + tax, org.decimals)}</span></span></span>
          </div>
        </div>
        <Text label="Notes" value={notes} onChange={setNotes} />
      </FormBody>
    </Modal>
  )
}

function DocumentDetail({ id, kind, onClose, onEdit }: { id: Id; kind: Kind; onClose: () => void; onEdit: (d: Doc) => void }) {
  const { org, pro } = useApp()
  const w = WORDS[kind]
  const query = useQuery(q<Doc>(['document', id], 'BooksService', 'getDocument', [org.id, id]))
  const d = query.data
  const remove = useSave(() => call('BooksService', 'deleteDocument', [org.id, id]), { success: 'Draft deleted', refresh: REFRESH, onDone: onClose })
  const [voiding, setVoiding] = useState(false)
  const [crediting, setCrediting] = useState(false)
  const [reason, setReason] = useState('')
  const voided = useSave(() => call('BooksService', 'voidDocument', [org.id, id, { reason: reason.trim() }]), { success: 'Voided. Its entry has been reversed.', refresh: REFRESH, onDone: () => { refreshBooks(); setVoiding(false) } })
  const badge = d ? statusBadge(d) : null
  return (
    <Modal wide open onClose={onClose} title={d?.number ?? w.title}>
      {!d ? <p className="text-muted-foreground">{query.isError ? query.error.message : 'Loading…'}</p> : (
        <div className="flex flex-col gap-3.5 min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-[13px] text-muted-foreground">
            {badge ? <Badge dot tone={badge.tone}>{badge.label}</Badge> : null}
            <span className="font-medium text-foreground">{d.party_name}</span>
            <span>{shortDate(d.issue_date)}, due {shortDate(d.due_date)}</span>
          </div>
          <div className="border border-border rounded-[8px] overflow-x-auto">
            <table className="w-full text-[13px] min-w-[480px]">
              <thead><tr><Head>Description</Head><Head right>Qty</Head><Head right>Price</Head><Head>Tax</Head><Head right>Amount</Head></tr></thead>
              <tbody>
                {d.lines.map((l) => <tr key={l.id}><Cell>{l.sku ? <span className="fig text-[12.5px] text-muted-foreground mr-1.5">{l.sku}</span> : null}{l.description}{l.serial_numbers?.length ? <span className="block fig text-[12px] text-muted-foreground">{l.serial_numbers.join(', ')}</span> : null}</Cell><Cell right>{figure(num(l.quantity), 0)}{l.unit_name ? ` ${l.unit_name}` : ''}</Cell><Cell right>{figure(num(l.unit_price), org.decimals)}</Cell><Cell className="text-muted-foreground">{l.tax_name ?? ''}</Cell><Cell right>{figure(num(l.amount), org.decimals)}</Cell></tr>)}
                <tr><td colSpan={4} className="px-3.5 py-1 text-right text-muted-foreground">Subtotal</td><Cell right className="border-b-0">{figure(num(d.subtotal), org.decimals)}</Cell></tr>
                <tr><td colSpan={4} className="px-3.5 py-1 text-right text-muted-foreground">Tax</td><Cell right className="border-b-0">{figure(num(d.tax_total), org.decimals)}</Cell></tr>
                <tr className="font-semibold"><td colSpan={4} className="px-3.5 py-1 text-right">Total</td><Cell right className="border-b-0">{figure(num(d.total), org.decimals)}</Cell></tr>
                {d.payments.length ? <tr><td colSpan={4} className="px-3.5 py-1 text-right text-muted-foreground">Still to {kind === 'invoice' ? 'collect' : 'pay'}</td><Cell right className="border-b-0">{figure(num(d.balance), org.decimals)}</Cell></tr> : null}
              </tbody>
            </table>
          </div>
          {d.notes ? <p className="text-[13px] text-muted-foreground">{d.notes}</p> : null}
          {d.void_reason ? <p className="text-[13px] text-muted-foreground">Voided: {d.void_reason}</p> : null}
          {d.payments.length ? (
            <section className="text-[13px]">
              <h3 className="font-semibold mb-1">Payments</h3>
              <ul className="flex flex-col gap-0.5">{d.payments.map((p) => <li key={p.id} className="flex justify-between gap-3"><span className="text-muted-foreground">{shortDate(p.payment_date)}{p.reference ? `, ${p.reference}` : ''}{p.credit_note_id ? ', credit' : ''}</span><span className="fig">{figure(num(p.amount), org.decimals)}</span></li>)}</ul>
            </section>
          ) : null}
          {d.credit_notes?.length ? (
            <section className="text-[13px]">
              <h3 className="font-semibold mb-1">{kind === 'invoice' ? 'Credit notes' : 'Supplier credits'}</h3>
              <ul className="flex flex-col gap-0.5">{d.credit_notes.map((n) => <li key={n.id} className="flex justify-between gap-3"><span className="text-muted-foreground min-w-0"><span className="fig">{n.number}</span>, {shortDate(n.credit_date)}, {n.reason}{num(n.refund) ? `, ${figure(num(n.refund), org.decimals)} refunded` : ''}</span><span className="fig shrink-0">{figure(num(n.total), org.decimals)}</span></li>)}</ul>
            </section>
          ) : null}
          {crediting ? <CreditNoteForm doc={d} onClose={() => setCrediting(false)} /> : null}
          {d.status === 'draft' ? <PostDocument doc={d} /> : null}
          {d.status === 'posted' || d.status === 'partial' ? <RecordPayment doc={d} /> : null}
          {voiding ? (
            <FormBody onSubmit={() => voided.mutate()} submit={`Void ${w.one}`} pending={voided.isPending} onCancel={() => setVoiding(false)} disabled={!reason.trim()}>
              <Text label="Why is this being voided?" required value={reason} onChange={setReason} />
              <p className="text-[12.5px] text-muted-foreground">This adds an opposite entry to your books, dated today, and keeps the record.</p>
            </FormBody>
          ) : null}
          <div className="flex flex-wrap items-center gap-2 justify-end border-t border-border pt-3">
            <span className="mr-auto"><AskChip prompt={`Explain ${w.one} ${d.number} and what should happen next.`}>Explain this {w.one}</AskChip></span>
            {d.status === 'draft' ? <><ConfirmDelete label="Delete" pending={remove.isPending} onConfirm={() => remove.mutate()} /><button className={btn.plain} onClick={() => onEdit(d)}>Edit</button></> : null}
            {d.status === 'posted' && !voiding ? <button className={btn.plain} onClick={() => setVoiding(true)}>Void</button> : null}
            {['posted', 'partial', 'paid'].includes(d.status) && !crediting && d.lines.some((l) => num(l.quantity) - num(l.credited_quantity) > 0) ? <button className={btn.plain} onClick={() => setCrediting(true)}>{kind === 'invoice' ? 'Credit note' : 'Supplier credit'}</button> : null}
            {d.status !== 'draft' || pro ? <Link to={`/print/document/${d.id}`} className={cn(btn.plain)}><Printer className="size-3.5 mr-1.5" />Print or export</Link> : null}
          </div>
        </div>
      )}
    </Modal>
  )
}

/** Takes back all or part of a posted document. Comes off what's still owed first, and the rest is refunded. */
function CreditNoteForm({ doc, onClose }: { doc: Doc; onClose: () => void }) {
  const { org } = useApp()
  const chart = useQuery(accounts(org.id))
  const sale = doc.kind === 'invoice'
  const open = doc.lines.filter((l) => num(l.quantity) - num(l.credited_quantity) > 0)
  const [date, setDate] = useState(today())
  const [reason, setReason] = useState('')
  const [bank, setBank] = useState('')
  const [rows, setRows] = useState<Record<string, { quantity: string; restock: boolean; serials: string }>>(Object.fromEntries(open.map((l) => [String(l.id), { quantity: String(num(l.quantity) - num(l.credited_quantity)), restock: true, serials: '' }])))
  const update = (id: Id, patch: Partial<{ quantity: string; restock: boolean; serials: string }>) => setRows((r) => ({ ...r, [String(id)]: { ...r[String(id)], ...patch } }))
  const worth = (l: DocLine) => {
    const q = Number(rows[String(l.id)]?.quantity) || 0
    return (q / num(l.quantity)) * (num(l.amount) + num(l.tax_amount))
  }
  const total = open.reduce((s, l) => s + worth(l), 0)
  const refund = Math.max(total - num(doc.balance), 0)
  const needsBank = refund > 0.004
  const save = useSave(() => call('BooksService', 'createCreditNote', [org.id, doc.id, {
    date, reason: reason.trim(), refund_account_id: needsBank && bank ? Number(bank) : null,
    lines: open.filter((l) => Number(rows[String(l.id)].quantity) > 0).map((l) => ({ line_id: Number(l.id), quantity: Number(rows[String(l.id)].quantity), restock: rows[String(l.id)].restock, serial_numbers: rows[String(l.id)].serials.trim() || null })),
  }]), { success: 'Credit recorded. Your books are updated.', refresh: [...REFRESH, 'accounts'], onDone: () => { refreshBooks(); onClose() } })
  const tooMany = open.some((l) => (Number(rows[String(l.id)]?.quantity) || 0) > num(l.quantity) - num(l.credited_quantity))
  return (
    <section aria-label={sale ? 'Credit note' : 'Supplier credit'} className="border border-border rounded-[8px] p-3">
      <FormBody onSubmit={() => save.mutate()} submit={`Credit ${figure(total, org.decimals)}`} pending={save.isPending} onCancel={onClose} disabled={!reason.trim() || !(total > 0) || tooMany || (needsBank && !bank)}>
        <h3 className="font-semibold text-[13.5px]">{sale ? 'What are you taking back?' : 'What is the supplier crediting?'}</h3>
        <div className="flex flex-col gap-2">
          {open.map((l) => (
            <div key={l.id} className="flex flex-col gap-1.5 text-[13px]">
              <div className="grid grid-cols-[minmax(0,1fr)_88px] gap-2 items-center">
                <span className="min-w-0 truncate">{l.description} <span className="text-muted-foreground">({figure(num(l.quantity) - num(l.credited_quantity), 0)} left{l.unit_name ? `, ${l.unit_name}` : ''})</span></span>
                <Input aria-label={`Quantity of ${l.description}`} inputMode="decimal" value={rows[String(l.id)].quantity} onChange={(e) => update(l.id, { quantity: e.target.value })} className="h-8 text-right fig" />
              </div>
              {l.item_id && sale ? <label className="flex items-center gap-2 text-muted-foreground cursor-pointer"><input type="checkbox" className="size-3.5" checked={rows[String(l.id)].restock} onChange={(e) => update(l.id, { restock: e.target.checked })} />Put it back in stock</label> : null}
              {l.item_id && !sale ? <p className="text-[12.5px] text-muted-foreground">Goes back to the supplier, so it leaves your stock.</p> : null}
              {l.serial_numbers?.length ? <Input aria-label={`Serial numbers of ${l.description}`} placeholder="Serial numbers, if only some are coming back" value={rows[String(l.id)].serials} onChange={(e) => update(l.id, { serials: e.target.value })} className="h-8" /> : null}
            </div>
          ))}
        </div>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Why?" required value={reason} onChange={setReason} />
          <Text label="Date" type="date" value={date} onChange={setDate} />
          {needsBank ? <Choice label={sale ? 'Refund from' : 'Refund comes into'} required hint={`${figure(refund, org.decimals)} has already been paid.`} placeholder="Select account" value={bank} onChange={setBank} options={postable(chart.data, 'asset')} /> : null}
        </div>
      </FormBody>
    </section>
  )
}

function PostDocument({ doc }: { doc: Doc }) {
  const { org } = useApp()
  const chart = useQuery(accounts(org.id))
  const [control, setControl] = useState('')
  const controlId = control ? Number(control) : null
  const preview = useQuery(q<Preview>(['document', doc.id, 'preview', controlId], 'BooksService', 'previewDocument', [org.id, doc.id, { control_account_id: controlId }]))
  const post = useSave(() => call('BooksService', 'postDocument', [org.id, doc.id, { control_account_id: controlId }]), { success: 'Posted to your books', refresh: REFRESH, onDone: refreshBooks })
  const p = preview.data
  return (
    <section aria-label="Post to your books" className="border border-border rounded-[8px] p-3 flex flex-col gap-2.5">
      <h3 className="font-semibold text-[13.5px]">Post to your books</h3>
      {p?.lines.length ? (
        <table className="w-full text-[13px]">
          <thead><tr><Head>Account</Head><Head right>Debit</Head><Head right>Credit</Head></tr></thead>
          <tbody>{p.lines.map((l) => <tr key={`${l.account_id}-${l.debit}-${l.credit}`}><Cell><span className="fig text-muted-foreground mr-1.5">{l.code}</span>{l.name}</Cell><Cell right>{l.debit ? figure(l.debit, org.decimals) : ''}</Cell><Cell right>{l.credit ? figure(l.credit, org.decimals) : ''}</Cell></tr>)}</tbody>
        </table>
      ) : null}
      {p?.problems.length ? <ul role="alert" className="text-[13px] text-destructive">{p.problems.map((x) => <li key={x}>{x}</li>)}</ul> : null}
      {preview.isError ? <p role="alert" className="text-[13px] text-destructive">{preview.error.message}</p> : null}
      <div className="flex flex-wrap items-end gap-3">
        <Choice className="flex-1 min-w-[220px]" label={WORDS[doc.kind].control} placeholder={p?.suggested_control_account_id ? "Use this customer's or supplier's account" : 'Select account'} value={control} onChange={setControl} options={postable(chart.data, doc.kind === 'invoice' ? 'asset' : 'liability')} />
        <button className={btn.primary} disabled={!p || p.problems.length > 0 || post.isPending} onClick={() => post.mutate()}>{post.isPending ? 'Posting…' : `Post ${figure(num(doc.total), org.decimals)}`}</button>
      </div>
    </section>
  )
}

function RecordPayment({ doc }: { doc: Doc }) {
  const { org } = useApp()
  const chart = useQuery(accounts(org.id))
  const [amount, setAmount] = useState(String(num(doc.balance)))
  const [date, setDate] = useState(today())
  const [bank, setBank] = useState('')
  const [reference, setReference] = useState('')
  const save = useSave(() => call('BooksService', 'recordPayment', [org.id, doc.id, { date, amount: Number(amount), bank_account_id: Number(bank), reference: reference.trim() || null }]), { success: 'Payment recorded', refresh: REFRESH, onDone: refreshBooks })
  return (
    <section aria-label="Record a payment" className="border border-border rounded-[8px] p-3 flex flex-col gap-2.5">
      <h3 className="font-semibold text-[13.5px]">{doc.kind === 'invoice' ? 'Record money received' : 'Record a payment'}</h3>
      <FormBody onSubmit={() => save.mutate()} submit="Record" pending={save.isPending} disabled={!bank || !(Number(amount) > 0)}>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
          <Text label="Amount" inputMode="decimal" value={amount} onChange={setAmount} />
          <Text label="Date" type="date" value={date} onChange={setDate} />
          <Choice label={doc.kind === 'invoice' ? 'Paid into' : 'Paid from'} placeholder="Select account" value={bank} onChange={setBank} options={postable(chart.data, 'asset')} />
          <Text label="Reference" value={reference} onChange={setReference} />
        </div>
      </FormBody>
    </section>
  )
}

export function Customers() {
  const { org } = useApp()
  const list = useQuery(customersQuery(org.id))
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<Partial<Customer> | null>(null)
  const s = search.trim().toLowerCase()
  const rows = (list.data ?? []).filter((c) => !s || `${c.name} ${c.email ?? ''} ${c.phone ?? ''}`.toLowerCase().includes(s))
  return (
    <Screen title="Customers" sub="Who you bill, and what each one owes you." search={<SearchIcon label="Search customers" value={search} onChange={setSearch} />} actions={<button className={btn.primary} onClick={() => setEditing({})}><Plus className="size-3.5 mr-1.5" />New customer</button>}>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No customers yet" body="Add the people and businesses you bill." /> : null)}>
        {() => (
          <Paged rows={rows}>
            {(page, pager) => (
              <Table min={560} footer={pager}>
                <thead><tr><Head>Customer</Head><Head>Email</Head><Head>Phone</Head><Head right>Owes you</Head></tr></thead>
                <tbody>{page.map((c) => <tr key={c.id} tabIndex={0} className="cursor-pointer hover:bg-accent/50" onClick={() => setEditing(c)} onKeyDown={(e) => { if (e.key === 'Enter') setEditing(c) }}><Cell>{c.name}</Cell><Cell className="text-muted-foreground">{c.email ?? ''}</Cell><Cell className="text-muted-foreground">{c.phone ?? ''}</Cell><Cell right>{figure(num(c.balance), org.decimals)}</Cell></tr>)}</tbody>
              </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {editing ? <CustomerForm customer={editing} onClose={() => setEditing(null)} /> : null}
    </Screen>
  )
}

function CustomerForm({ customer, onClose }: { customer: Partial<Customer>; onClose: () => void }) {
  const { org } = useApp()
  const chart = useQuery(accounts(org.id))
  const [f, setF] = useState({ name: customer.name ?? '', email: customer.email ?? '', phone: customer.phone ?? '', address: customer.address ?? '', tax_id: customer.tax_id ?? '', receivable: customer.receivable_account_id ? String(customer.receivable_account_id) : '' })
  const set = (k: keyof typeof f) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const save = useSave(() => call('BooksService', 'saveCustomer', [org.id, { id: customer.id, name: f.name, email: f.email, phone: f.phone, address: f.address, tax_id: f.tax_id, receivable_account_id: f.receivable ? Number(f.receivable) : null }]), { success: 'Customer saved', refresh: REFRESH, onDone: onClose })
  const archive = useSave(() => call('BooksService', 'archiveCustomer', [org.id, customer.id]), { success: 'Customer removed from the list', refresh: REFRESH, onDone: onClose })
  return (
    <Modal open onClose={onClose} title={customer.id ? 'Edit customer' : 'New customer'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save customer" pending={save.isPending} onCancel={onClose} disabled={!f.name.trim()}>
        <Text label="Name" required value={f.name} onChange={set('name')} />
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Email" type="email" value={f.email} onChange={set('email')} />
          <Text label="Phone" value={f.phone} onChange={set('phone')} />
          <Text label="Tax ID" value={f.tax_id} onChange={set('tax_id')} />
          <Choice label="Account for what they owe" placeholder="Choose when posting" value={f.receivable} onChange={set('receivable')} options={postable(chart.data, 'asset')} />
        </div>
        <Text label="Address" value={f.address} onChange={set('address')} />
        {customer.id ? <ConfirmDelete label="Remove this customer" pending={archive.isPending} onConfirm={() => archive.mutate()} /> : null}
      </FormBody>
    </Modal>
  )
}
