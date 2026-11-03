import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Badge, Chips, type Tone } from '@/components/chips'
import { Choice, ConfirmDelete, FormBody, Modal, Stat, Stats, Text, selectClass, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, Table, Tabs, Toolbar, btn } from '@/components/page'
import { AskChip } from '@/components/agent-panel'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { num, q, refreshBooks, today, type Id } from '@/lib/data'
import { INVENTORY_TABS, STOCK_REFRESH, items, unitsQuery, useCanWriteStock, warehousesQuery } from '@/routes/inventory'

type Row = { id: Id; number: string; status: string; supplier_name: string; order_date: string; expected_date: string | null; warehouse_name: string; total: number; ordered: number; received: number; has_unbilled: boolean }
type Line = { id: Id; item_id: Id; quantity: number; quantity_received: number; unit_cost: number; item_name: string; sku: string; unit_of_measure: string; track_lots: boolean; track_serials: boolean; unit_id: Id | null; unit_name: string | null; unit_factor: number }
type Receipt = { id: Id; number: string; receipt_date: string; total: number; bill_id: Id | null; bill_number: string | null }
type Order = { id: Id; number: string; status: string; supplier_id: Id | null; supplier_name: string; warehouse_id: Id; warehouse_name: string; order_date: string; expected_date: string | null; notes: string | null; lines: Line[]; receipts: Receipt[] }
type Settings = { grni_account_id: number | null; grni_code: string | null; grni_name: string | null; default_costing_method: 'average' | 'fifo' }

export const settingsQuery = (org: string) => q<Settings>(['stock', org, 'settings'], 'InventoryService', 'getSettings', [org])
const STATUS: Record<string, { label: string; tone: Tone }> = { draft: { label: 'Draft', tone: 'neutral' }, approved: { label: 'Approved', tone: 'warn' }, partial: { label: 'Part received', tone: 'warn' }, received: { label: 'Received', tone: 'good' }, cancelled: { label: 'Cancelled', tone: 'neutral' } }

export function PurchaseOrders() {
  const { org, pro } = useApp()
  const canWrite = useCanWriteStock()
  const list = useQuery(q<Row[]>(['stock', org.id, 'orders'], 'InventoryService', 'listPurchaseOrders', [org.id]))
  const [status, setStatus] = useState('all')
  const [search, setSearch] = useState('')
  const [opened, setOpened] = useState<Id | null>(null)
  const [editing, setEditing] = useState<Order | 'new' | null>(null)
  const all = list.data ?? []
  const s = search.trim().toLowerCase()
  const rows = all.filter((r) => (status === 'all' || (status === 'open' ? r.status === 'approved' || r.status === 'partial' : r.status === status)) && (!s || `${r.number} ${r.supplier_name}`.toLowerCase().includes(s)))
  const open = all.filter((r) => r.status === 'approved' || r.status === 'partial')
  const committed = open.reduce((t, r) => t + num(r.total) * (1 - (num(r.ordered) ? num(r.received) / num(r.ordered) : 0)), 0)
  return (
    <Screen
      title="Inventory"
      sub={pro ? 'Purchase orders, goods received, and bills from what arrived.' : 'What you have ordered from suppliers, and what has arrived.'}
      search={<SearchIcon label="Search purchase orders" value={search} onChange={setSearch} />}
      actions={canWrite ? <button className={btn.primary} onClick={() => setEditing('new')}><Plus className="size-3.5 mr-1.5" />New order</button> : undefined}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Stats cols={3}>
        <Stat label="Waiting to arrive" value={open.length} />
        <Stat label={pro ? 'Committed' : 'Still to come, worth'} value={`${org.currency} ${figure(committed, 0)}`} />
        <Stat label="Arrived, no bill yet" value={all.filter((r) => r.has_unbilled).length} tone={all.some((r) => r.has_unbilled) ? 'warn' : undefined} />
      </Stats>
      <Toolbar>
        <Chips label="Status" value={status} onChange={setStatus} options={[{ id: 'all', label: 'All', count: all.length }, { id: 'draft', label: 'Drafts', count: all.filter((r) => r.status === 'draft').length }, { id: 'open', label: 'Waiting', count: open.length }, { id: 'received', label: 'Received', count: all.filter((r) => r.status === 'received').length }, { id: 'cancelled', label: 'Cancelled', count: all.filter((r) => r.status === 'cancelled').length }]} />
        <span className="ml-auto"><AskChip prompt="Look at my purchase orders. What is late, and what still needs a bill?">What needs chasing?</AskChip></span>
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No purchase orders yet" body="Create one here, or draft them from the Planner." /> : null)}>
        {() => rows.length === 0 ? <Empty title="No matches" body="Try another word or filter." /> : (
          <Paged rows={rows}>
            {(page, pager) => (
              <Table min={760} footer={pager}>
                <thead><tr><Head>Number</Head><Head>Supplier</Head><Head>Status</Head><Head>Ordered</Head><Head>Expected</Head><Head right>Received</Head><Head right>Total</Head></tr></thead>
                <tbody>
                  {page.map((r) => {
                    const late = (r.status === 'approved' || r.status === 'partial') && r.expected_date && r.expected_date < today()
                    return (
                      <tr key={r.id} tabIndex={0} className="cursor-pointer hover:bg-accent/50 focus-visible:bg-accent/50 outline-none" onClick={() => setOpened(r.id)} onKeyDown={(e) => { if (e.key === 'Enter') setOpened(r.id) }}>
                        <Cell className="fig text-[12.5px]">{r.number}</Cell>
                        <Cell className="max-w-0 w-full truncate">{r.supplier_name}</Cell>
                        <Cell><span className="flex items-center gap-1.5"><Badge dot tone={STATUS[r.status]?.tone}>{STATUS[r.status]?.label ?? r.status}</Badge>{late ? <Badge dot tone="bad">Late</Badge> : null}{r.has_unbilled ? <Badge>No bill</Badge> : null}</span></Cell>
                        <Cell className="text-muted-foreground">{shortDate(r.order_date)}</Cell>
                        <Cell className="text-muted-foreground">{r.expected_date ? shortDate(r.expected_date) : ''}</Cell>
                        <Cell right>{figure(num(r.received), 0)} of {figure(num(r.ordered), 0)}</Cell>
                        <Cell right>{figure(num(r.total), org.decimals)}</Cell>
                      </tr>
                    )
                  })}
                </tbody>
              </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {opened !== null ? <OrderDetail id={opened} onClose={() => setOpened(null)} onEdit={(o) => { setOpened(null); setEditing(o) }} /> : null}
      {editing ? <OrderForm order={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={(id) => { setEditing(null); setOpened(id) }} /> : null}
    </Screen>
  )
}

type FormLine = { key: number; item_id: string; unit_id: string; quantity: string; unit_cost: string }

function OrderForm({ order, onClose, onSaved }: { order: Order | null; onClose: () => void; onSaved: (id: Id) => void }) {
  const { org } = useApp()
  const list = useQuery(items(org.id))
  const suppliers = useQuery(q<{ id: Id; name: string }[]>(['supplier-picker', org.id], 'SupplierService', 'getSuppliersForVoucher', [org.id]))
  const warehouses = useQuery(warehousesQuery(org.id))
  const units = useQuery(unitsQuery(org.id))
  const active = (warehouses.data ?? []).filter((w) => w.is_active)
  const [supplier, setSupplier] = useState(order?.supplier_id ? String(order.supplier_id) : '')
  const [name, setName] = useState(order && !order.supplier_id ? order.supplier_name : '')
  const [warehouse, setWarehouse] = useState(order ? String(order.warehouse_id) : '')
  const [date, setDate] = useState(order?.order_date.slice(0, 10) ?? today())
  const [expected, setExpected] = useState(order?.expected_date?.slice(0, 10) ?? '')
  const [notes, setNotes] = useState(order?.notes ?? '')
  const [lines, setLines] = useState<FormLine[]>(order?.lines.map((l, i) => ({ key: i + 1, item_id: String(l.item_id), unit_id: l.unit_id ? String(l.unit_id) : '', quantity: String(num(l.quantity)), unit_cost: String(num(l.unit_cost)) })) ?? [{ key: 1, item_id: '', unit_id: '', quantity: '', unit_cost: '' }])
  const [next, setNext] = useState((order?.lines.length ?? 1) + 1)
  const update = (key: number, patch: Partial<FormLine>) => setLines((ls) => ls.map((l) => (l.key === key ? { ...l, ...patch } : l)))
  const pick = (key: number, id: string) => {
    const item = list.data?.find((i) => String(i.id) === id)
    update(key, { item_id: id, unit_id: '', ...(item && num(item.average_unit_cost) ? { unit_cost: String(num(item.average_unit_cost)) } : {}) })
    if (item?.preferred_supplier_id && !supplier && !name) setSupplier(String(item.preferred_supplier_id))
  }
  const unitsOf = (l: FormLine) => (units.data ?? []).filter((u) => String(u.item_id) === l.item_id)
  // A cost is per the unit chosen, so changing the unit moves the suggested cost with it.
  const pickUnit = (l: FormLine, id: string) => {
    const was = num(unitsOf(l).find((u) => String(u.id) === l.unit_id)?.factor) || 1
    const now = num(unitsOf(l).find((u) => String(u.id) === id)?.factor) || 1
    update(l.key, { unit_id: id, unit_cost: l.unit_cost ? String(Math.round((Number(l.unit_cost) / was) * now * 10000) / 10000) : '' })
  }
  const total = lines.reduce((t, l) => t + (Number(l.quantity) * Number(l.unit_cost) || 0), 0)
  const remove = useSave(() => call('InventoryService', 'cancelPurchaseOrder', [org.id, order?.id]), { success: 'Order cancelled', refresh: STOCK_REFRESH, onDone: onClose })
  const save = useSave(() => call<{ id: Id }>('InventoryService', 'savePurchaseOrder', [org.id, {
    id: order?.id, supplier_id: supplier ? Number(supplier) : null, supplier_name: name.trim() || null, warehouse_id: warehouse ? Number(warehouse) : null, order_date: date, expected_date: expected || null, notes: notes.trim() || null,
    lines: lines.map((l) => ({ item_id: Number(l.item_id), unit_id: l.unit_id ? Number(l.unit_id) : null, quantity: Number(l.quantity), unit_cost: Number(l.unit_cost) || 0 })),
  }]), { success: 'Draft saved. Nothing changes until it is approved and the goods arrive.', refresh: STOCK_REFRESH, onDone: (r) => onSaved(r.id) })
  return (
    <Modal wide open onClose={onClose} title={order ? `Edit ${order.number}` : 'New purchase order'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save draft" pending={save.isPending} onCancel={onClose} disabled={!(supplier || name.trim()) || lines.some((l) => !l.item_id || !(Number(l.quantity) > 0))}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label="Supplier" placeholder="Choose, or type a name" value={supplier} onChange={(v) => { setSupplier(v); if (v) setName('') }} options={(suppliers.data ?? []).map((s) => ({ value: String(s.id), label: s.name }))} />
          {supplier ? <Choice label="Deliver to" placeholder="Default warehouse" value={warehouse} onChange={setWarehouse} options={active.map((w) => ({ value: String(w.id), label: w.name }))} /> : <Text label="Or just a name" value={name} onChange={setName} />}
          {!supplier ? <Choice label="Deliver to" placeholder="Default warehouse" value={warehouse} onChange={setWarehouse} options={active.map((w) => ({ value: String(w.id), label: w.name }))} /> : null}
          <Text label="Order date" type="date" value={date} onChange={setDate} />
          <Text label="Expected" type="date" min={date} value={expected} onChange={setExpected} />
        </div>
        <div className="flex flex-col gap-1.5">
          <div className="hidden md:grid grid-cols-[minmax(0,1fr)_96px_72px_96px_96px_24px] gap-1.5 text-[12px] text-muted-foreground"><span>Item</span><span>Unit</span><span className="text-right">Qty</span><span className="text-right">Cost each</span><span className="text-right">Amount</span><span /></div>
          {lines.map((l) => (
            <div key={l.key} className="grid grid-cols-2 md:grid-cols-[minmax(0,1fr)_96px_72px_96px_96px_24px] gap-1.5 items-center max-md:border-b max-md:border-border max-md:pb-2">
              <select aria-label="Item" value={l.item_id} onChange={(e) => pick(l.key, e.target.value)} className={selectClass}>
                <option value="">Select item</option>
                {(list.data ?? []).map((i) => <option key={i.id} value={String(i.id)}>{i.sku} · {i.name}</option>)}
              </select>
              <select aria-label="Unit" value={l.unit_id} onChange={(e) => pickUnit(l, e.target.value)} className={selectClass}>
                <option value="">{list.data?.find((i) => String(i.id) === l.item_id)?.unit_of_measure ?? 'Base unit'}</option>
                {unitsOf(l).map((u) => <option key={u.id} value={String(u.id)}>{u.name}</option>)}
              </select>
              <Input aria-label="Quantity" inputMode="decimal" value={l.quantity} onChange={(e) => update(l.key, { quantity: e.target.value })} className="h-8 text-right fig" />
              <Input aria-label="Cost each" inputMode="decimal" placeholder="0.00" value={l.unit_cost} onChange={(e) => update(l.key, { unit_cost: e.target.value })} className="h-8 text-right fig" />
              <span className="fig text-[13px] text-right">{figure(Number(l.quantity) * Number(l.unit_cost) || 0, org.decimals)}</span>
              <button type="button" aria-label="Remove line" disabled={lines.length < 2} onClick={() => setLines((ls) => ls.filter((x) => x.key !== l.key))} className="grid place-items-center text-muted-foreground cursor-pointer disabled:opacity-30"><X className="size-3.5" /></button>
            </div>
          ))}
          <div className="flex items-center justify-between text-[13px] mt-1">
            <button type="button" onClick={() => { setLines((ls) => [...ls, { key: next, item_id: '', unit_id: '', quantity: '', unit_cost: '' }]); setNext((k) => k + 1) }} className="inline-flex items-center gap-1 font-medium cursor-pointer"><Plus className="size-3.5" />Add line</button>
            <span className="font-semibold">Total <span className="fig ml-1">{figure(total, org.decimals)}</span></span>
          </div>
        </div>
        <Text label="Notes" value={notes} onChange={setNotes} />
        {order ? <ConfirmDelete label="Cancel this order" pending={remove.isPending} onConfirm={() => remove.mutate()} /> : null}
      </FormBody>
    </Modal>
  )
}

function OrderDetail({ id, onClose, onEdit }: { id: Id; onClose: () => void; onEdit: (o: Order) => void }) {
  const { org, canSeeBooks } = useApp()
  const canWrite = useCanWriteStock()
  const query = useQuery(q<Order>(['stock', org.id, 'order', id], 'InventoryService', 'getPurchaseOrder', [org.id, id]))
  const settings = useQuery(settingsQuery(org.id))
  const [receiving, setReceiving] = useState(false)
  const approve = useSave(() => call('InventoryService', 'approvePurchaseOrder', [org.id, id]), { success: 'Approved', refresh: STOCK_REFRESH })
  const cancel = useSave(() => call('InventoryService', 'cancelPurchaseOrder', [org.id, id]), { success: 'Order closed', refresh: STOCK_REFRESH })
  const bill = useSave(() => call<{ id: Id }>('InventoryService', 'createBillFromReceipts', [org.id, id]), { success: 'Draft bill created. Review and post it under Bills.', refresh: [...STOCK_REFRESH, 'documents'] })
  const setup = useSave(() => call('InventoryService', 'createGrniAccount', [org.id]), { success: 'Account created', refresh: [...STOCK_REFRESH, 'accounts'] })
  const o = query.data
  const open = o?.status === 'approved' || o?.status === 'partial'
  const unbilled = (o?.receipts ?? []).some((r) => !r.bill_id && num(r.total) > 0)
  const noAccount = settings.data && !settings.data.grni_account_id
  return (
    <Modal wide open onClose={onClose} title={o?.number ?? 'Purchase order'}>
      {!o ? <p className="text-muted-foreground">{query.isError ? query.error.message : 'Loading…'}</p> : (
        <div className="flex flex-col gap-3.5 min-w-0">
          <div className="flex flex-wrap items-center gap-2 text-[13px] text-muted-foreground">
            <Badge dot tone={STATUS[o.status]?.tone}>{STATUS[o.status]?.label ?? o.status}</Badge>
            <span className="font-medium text-foreground">{o.supplier_name}</span>
            <span>Ordered {shortDate(o.order_date)}{o.expected_date ? `, expected ${shortDate(o.expected_date)}` : ''}, to {o.warehouse_name}</span>
          </div>
          <div className="border border-border rounded-[8px] overflow-x-auto">
            <table className="w-full text-[13px] min-w-[520px]">
              <thead><tr><Head>SKU</Head><Head>Item</Head><Head right>Ordered</Head><Head right>Received</Head><Head right>Cost each</Head><Head right>Amount</Head></tr></thead>
              <tbody>
                {o.lines.map((l) => <tr key={l.id}><Cell className="fig text-[12.5px] text-muted-foreground">{l.sku}</Cell><Cell>{l.item_name}{l.unit_name ? <span className="ml-1.5 text-muted-foreground">in {l.unit_name} of {num(l.unit_factor)}</span> : null}</Cell><Cell right>{figure(num(l.quantity), 0)}</Cell><Cell right>{figure(num(l.quantity_received), 0)}</Cell><Cell right>{figure(num(l.unit_cost), org.decimals)}</Cell><Cell right>{figure(num(l.quantity) * num(l.unit_cost), org.decimals)}</Cell></tr>)}
              </tbody>
            </table>
          </div>
          {o.notes ? <p className="text-[13px] text-muted-foreground">{o.notes}</p> : null}
          {o.receipts.length ? (
            <section className="text-[13px]">
              <h3 className="font-semibold mb-1">Goods received</h3>
              <ul className="flex flex-col gap-0.5">{o.receipts.map((r) => <li key={r.id} className="flex flex-wrap items-center justify-between gap-3"><span className="text-muted-foreground"><span className="fig">{r.number}</span>, {shortDate(r.receipt_date)}</span><span className="flex items-center gap-2">{r.bill_number ? <Badge dot tone="good">Bill {r.bill_number}</Badge> : <Badge dot tone="warn">No bill yet</Badge>}<span className="fig">{figure(num(r.total), org.decimals)}</span></span></li>)}</ul>
            </section>
          ) : null}
          {open && noAccount ? (
            <div className="border border-border rounded-[8px] p-3 text-[13px] flex flex-wrap items-center justify-between gap-2">
              <span>{canSeeBooks ? 'Goods need an account to wait in until the supplier’s bill arrives.' : 'An accountant needs to finish setting this up before goods can be received.'}</span>
              {canSeeBooks ? <button className={btn.plain} disabled={setup.isPending} onClick={() => setup.mutate()}>Create the account</button> : null}
            </div>
          ) : null}
          {receiving ? <ReceiveForm order={o} onClose={() => setReceiving(false)} /> : null}
          <div className="flex flex-wrap items-center gap-2 justify-end border-t border-border pt-3">
            {canWrite && o.status === 'draft' ? <button className={btn.plain} onClick={() => onEdit(o)}>Edit</button> : null}
            {canWrite && open ? <button className={btn.plain} disabled={cancel.isPending} onClick={() => cancel.mutate()}>{o.receipts.length ? 'Nothing more is coming' : 'Cancel order'}</button> : null}
            {canSeeBooks && unbilled ? <button className={btn.plain} disabled={bill.isPending} onClick={() => bill.mutate(undefined, { onSuccess: refreshBooks })}>Create bill from what arrived</button> : null}
            {canSeeBooks && o.status === 'draft' ? <button className={btn.primary} disabled={approve.isPending} onClick={() => approve.mutate()}>Approve order</button> : null}
            {!canSeeBooks && o.status === 'draft' ? <span className="text-[12.5px] text-muted-foreground">Waiting for an accountant to approve.</span> : null}
            {canWrite && open && !receiving ? <button className={btn.primary} disabled={Boolean(noAccount)} onClick={() => setReceiving(true)}>Receive goods</button> : null}
          </div>
        </div>
      )}
    </Modal>
  )
}

function ReceiveForm({ order: o, onClose }: { order: Order; onClose: () => void }) {
  const { org } = useApp()
  const left = o.lines.filter((l) => num(l.quantity) - num(l.quantity_received) > 0)
  const [date, setDate] = useState(today())
  const [rows, setRows] = useState<Record<string, { quantity: string; lot: string; expiry: string; serials: string }>>(Object.fromEntries(left.map((l) => [String(l.id), { quantity: String(num(l.quantity) - num(l.quantity_received)), lot: '', expiry: '', serials: '' }])))
  const update = (id: Id, patch: Partial<{ quantity: string; lot: string; expiry: string; serials: string }>) => setRows((r) => ({ ...r, [String(id)]: { ...r[String(id)], ...patch } }))
  const save = useSave(() => call('InventoryService', 'receivePurchaseOrder', [org.id, o.id, { date, lines: left.map((l) => ({ line_id: l.id, quantity: Number(rows[String(l.id)].quantity) || 0, lot_number: rows[String(l.id)].lot.trim() || null, expiry_date: rows[String(l.id)].expiry || null, serial_numbers: rows[String(l.id)].serials.trim() || null })) }]), { success: 'Received. Stock and your books are updated.', refresh: STOCK_REFRESH, onDone: () => { refreshBooks(); onClose() } })
  return (
    <FormBody onSubmit={() => save.mutate()} submit="Record receipt" pending={save.isPending} onCancel={onClose} disabled={!left.some((l) => Number(rows[String(l.id)]?.quantity) > 0)}>
      <h3 className="font-semibold text-[13.5px]">What arrived</h3>
      <div className="flex flex-col gap-2">
        {left.map((l) => (
          <div key={l.id} className="grid sm:grid-cols-[minmax(0,1fr)_88px_minmax(0,110px)_minmax(0,130px)] gap-1.5 items-center text-[13px]">
            <span className="min-w-0 truncate">{l.item_name} <span className="text-muted-foreground">({figure(num(l.quantity) - num(l.quantity_received), 0)} {l.unit_name ?? l.unit_of_measure} to come)</span></span>
            <Input aria-label={`Quantity of ${l.item_name}`} inputMode="decimal" value={rows[String(l.id)].quantity} onChange={(e) => update(l.id, { quantity: e.target.value })} className="h-8 text-right fig" />
            {l.track_lots ? <Input aria-label={`Batch of ${l.item_name}`} placeholder="Batch" value={rows[String(l.id)].lot} onChange={(e) => update(l.id, { lot: e.target.value })} className="h-8" /> : <span />}
            {l.track_lots ? <Input aria-label={`Expiry of ${l.item_name}`} type="date" value={rows[String(l.id)].expiry} onChange={(e) => update(l.id, { expiry: e.target.value })} className="h-8" /> : <span />}
            {l.track_serials ? <Input aria-label={`Serial numbers of ${l.item_name}`} placeholder="Serial numbers, separated by commas. Blank creates them." value={rows[String(l.id)].serials} onChange={(e) => update(l.id, { serials: e.target.value })} className="h-8 sm:col-span-4" /> : null}
          </div>
        ))}
      </div>
      <Text label="Date received" type="date" value={date} onChange={setDate} />
    </FormBody>
  )
}
