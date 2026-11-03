import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from '@tanstack/react-router'
import { ArrowLeft, Plus, Trash2, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { AskChip } from '@/components/agent-panel'
import { Badge, Chips, type Tone } from '@/components/chips'
import { Choice, FormBody, Modal, Stat, Stats, Text, Toggle, selectClass, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, Table, Tabs, Toolbar, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { num, q, today, type Id } from '@/lib/data'
import { cn } from '@/lib/utils'
import { INVENTORY_TABS, ItemForm, MOVE_LABEL, MOVE_TONE, STOCK_REFRESH, items, marginOf, useCanWriteStock, warehousesQuery, type Item, type ItemDraft, type Unit, type Warehouse } from '@/routes/inventory'

type Level = { warehouse_id: Id; warehouse_name: string; quantity: number }
type Lot = { id: Id; lot_number: string; expiry_date: string | null; quantity: number; warehouse_name: string; warehouse_id: Id; status: 'expired' | 'soon' | 'ok' | null }
export type ItemDetail = Item & { category_name: string | null; supplier_name: string | null; levels: Level[]; lots: Lot[]; on_order: number; units: Unit[]; serials: { id: Id; serial_number: string; warehouse_name: string | null }[] }
type CardRow = { id: Id; date: string; transaction_type: keyof typeof MOVE_LABEL; quantity: number; unit_cost: number | null; total_cost: number | null; reference: string | null; description: string | null; journal_entry_id: Id | null; warehouse_name: string | null; lots: string | null; serials: string | null; balance: number }

export const EXPIRY: Record<string, { label: string; tone: Tone }> = { expired: { label: 'Expired', tone: 'bad' }, soon: { label: 'Expires soon', tone: 'warn' }, ok: { label: 'In date', tone: 'good' } }

/** One item in full: where it is, which batches, what it costs, and everything that ever happened to it. */
export function ItemPage() {
  const { itemId } = useParams({ strict: false }) as { itemId: string }
  const { org, pro } = useApp()
  const canWrite = useCanWriteStock()
  const id = Number(itemId)
  const detail = useQuery(q<ItemDetail>(['stock', org.id, 'item', id], 'InventoryService', 'getItemDetail', [org.id, id]))
  const warehouses = useQuery(warehousesQuery(org.id))
  const [warehouse, setWarehouse] = useState('all')
  const card = useQuery(q<CardRow[]>(['stock', org.id, 'card', id, warehouse], 'InventoryService', 'getStockCard', [org.id, id, warehouse === 'all' ? null : Number(warehouse)]))
  const [editing, setEditing] = useState<ItemDraft | null>(null)
  const d = detail.data
  const margin = d ? marginOf(d) : null
  return (
    <Screen
      title={d?.name ?? 'Item'}
      sub={d ? <span className="flex flex-wrap items-center gap-x-2"><span className="fig">SKU {d.sku}</span>{d.barcode ? <span className="fig">Barcode {d.barcode}</span> : null}{d.category_name ? <span>{d.category_name}</span> : null}</span> : undefined}
      actions={<>
        <Link to="/inventory" className={btn.plain}><ArrowLeft className="size-3.5 mr-1.5" />All items</Link>
        {canWrite && d ? <button className={btn.primary} onClick={() => setEditing({ id: d.id, category_id: String(d.category_id), sku: d.sku, name: d.name, description: d.description ?? '', unit_of_measure: d.unit_of_measure, reorder_point: String(num(d.reorder_point)), reorder_quantity: String(num(d.reorder_quantity)), barcode: d.barcode ?? '', selling_price: d.selling_price == null ? '' : String(num(d.selling_price)), income_account_id: d.income_account_id ? String(d.income_account_id) : '', preferred_supplier_id: d.preferred_supplier_id ? String(d.preferred_supplier_id) : '', lead_time_days: String(d.lead_time_days ?? 14), track_lots: Boolean(d.track_lots), track_serials: Boolean(d.track_serials), costing_method: d.costing_method ?? 'average' })}>Edit item</button> : null}
      </>}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Loaded query={detail}>
        {(i) => (
          <>
            <Stats>
              <Stat label="On hand" value={`${figure(num(i.quantity_available), 0)} ${i.unit_of_measure}`} tone={num(i.reorder_point) > 0 && num(i.quantity_available) <= num(i.reorder_point) ? 'warn' : undefined} />
              <Stat label="On order" value={`${figure(num(i.on_order), 0)} ${i.unit_of_measure}`} />
              <Stat label={pro ? 'Average cost' : 'Cost each'} value={figure(num(i.average_unit_cost), org.decimals)} />
              <Stat label="Value" value={`${org.currency} ${figure(num(i.total_value), 0)}`} />
            </Stats>
            <div className="grid lg:grid-cols-2 gap-3.5">
              <section aria-label="Details" className="sheet p-3 grid grid-cols-2 gap-x-4 gap-y-2 text-[13px] content-start">
                {[
                  ['Selling price', i.selling_price == null ? 'Not set' : figure(num(i.selling_price), org.decimals)],
                  ['Margin', margin === null ? 'Not set' : `${figure(margin, 1)}%`],
                  ['Reorder at', `${figure(num(i.reorder_point), 0)} ${i.unit_of_measure}`],
                  ['Reorder amount', `${figure(num(i.reorder_quantity), 0)} ${i.unit_of_measure}`],
                  ['Bought from', i.supplier_name ?? 'Not set'],
                  ['Delivery takes', `${i.lead_time_days ?? 14} days`],
                  ['Tracking', i.track_lots ? 'Batches' : i.track_serials ? 'Serial numbers' : 'Quantity only'],
                  ['Costing', i.costing_method === 'fifo' ? 'First in, first out' : 'Moving average'],
                ].map(([k, v]) => <div key={k}><p className="text-[12px] text-muted-foreground">{k}</p><p>{v}</p></div>)}
                {i.description ? <div className="col-span-2"><p className="text-[12px] text-muted-foreground">Description</p><p>{i.description}</p></div> : null}
              </section>
              <div className="flex flex-col gap-3.5 min-w-0">
                <Table min={300}>
                  <thead><tr><Head>Warehouse</Head><Head right>On hand</Head></tr></thead>
                  <tbody>
                    {i.levels.length ? i.levels.map((l) => <tr key={l.warehouse_id}><Cell>{l.warehouse_name}</Cell><Cell right>{figure(num(l.quantity), 0)} {i.unit_of_measure}</Cell></tr>) : <tr><Cell className="text-muted-foreground">None in any warehouse</Cell><Cell right>0</Cell></tr>}
                  </tbody>
                </Table>
                {i.track_lots ? (
                  <Table min={420}>
                    <thead><tr><Head>Batch</Head><Head>Warehouse</Head><Head>Expiry</Head><Head right>Quantity</Head></tr></thead>
                    <tbody>
                      {i.lots.length ? i.lots.map((l) => (
                        <tr key={l.id}>
                          <Cell className="fig text-[12.5px]">{l.lot_number}</Cell>
                          <Cell className="text-muted-foreground">{l.warehouse_name}</Cell>
                          <Cell>{l.expiry_date ? <span className="flex items-center gap-2">{shortDate(l.expiry_date)}{l.status && l.status !== 'ok' ? <Badge dot tone={EXPIRY[l.status].tone}>{EXPIRY[l.status].label}</Badge> : null}</span> : <span className="text-muted-foreground">None</span>}</Cell>
                          <Cell right>{figure(num(l.quantity), 0)}</Cell>
                        </tr>
                      )) : <tr><td colSpan={4} className="px-3.5 py-2 text-muted-foreground text-[13px]">No batches in stock.</td></tr>}
                    </tbody>
                  </Table>
                ) : null}
                <UnitsTable item={i} canWrite={canWrite} />
              </div>
            </div>
            {i.track_serials ? <SerialsTable item={i} /> : null}
          </>
        )}
      </Loaded>
      <Toolbar>
        <h2 className="font-semibold text-[14px]">Stock card</h2>
        {(warehouses.data?.length ?? 0) > 1 ? <Chips label="Warehouse" value={warehouse} onChange={setWarehouse} options={[{ id: 'all', label: 'All' }, ...(warehouses.data ?? []).map((w) => ({ id: String(w.id), label: w.name }))]} /> : null}
        <span className="ml-auto"><AskChip prompt={`Look at the stock card for ${d?.name ?? 'this item'}. Is anything unusual, and when should I reorder?`}>Anything unusual here?</AskChip></span>
      </Toolbar>
      <Loaded query={card} empty={(rows) => (rows.length === 0 ? <Empty title="No movements yet" body="Everything that happens to this item appears here, with a running balance." /> : null)}>
        {(rows) => (
          <Paged rows={rows}>
            {(page, pager) => (
              <Table min={760} footer={pager}>
                <thead><tr><Head>Date</Head><Head>Type</Head><Head>Reference</Head><Head>Warehouse</Head>{i_lots(d) ? <Head>{d?.track_serials ? 'Serials' : 'Batch'}</Head> : null}<Head right>Quantity</Head><Head right>Cost</Head><Head right>Balance</Head></tr></thead>
                <tbody>
                  {page.map((m) => (
                    <tr key={m.id}>
                      <Cell className="text-muted-foreground whitespace-nowrap">{shortDate(m.date)}</Cell>
                      <Cell><Badge dot tone={MOVE_TONE[m.transaction_type]}>{MOVE_LABEL[m.transaction_type]}</Badge></Cell>
                      <Cell className="fig text-[12.5px] text-muted-foreground">{m.reference ?? ''}</Cell>
                      <Cell className="text-muted-foreground">{m.warehouse_name ?? ''}</Cell>
                      {i_lots(d) ? <Cell className="fig text-[12.5px] text-muted-foreground max-w-[220px] truncate">{d?.track_serials ? m.serials ?? '' : m.lots ?? ''}</Cell> : null}
                      <Cell right>{num(m.quantity) > 0 ? '+' : ''}{figure(num(m.quantity), 0)}</Cell>
                      <Cell right>{m.total_cost != null ? figure(num(m.total_cost), org.decimals) : ''}</Cell>
                      <Cell right>{figure(num(m.balance), 0)}</Cell>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {editing ? <ItemForm key={String(editing.id)} draft={editing} onClose={() => setEditing(null)} /> : null}
    </Screen>
  )
}
const i_lots = (d?: ItemDetail) => Boolean(d?.track_lots || d?.track_serials)

/** Other units this item is bought or sold in. Stock is always kept in its own unit. */
function UnitsTable({ item, canWrite }: { item: ItemDetail; canWrite: boolean }) {
  const { org } = useApp()
  const [adding, setAdding] = useState(false)
  const [name, setName] = useState('')
  const [factor, setFactor] = useState('')
  const save = useSave(() => call('InventoryService', 'saveUnit', [org.id, { item_id: item.id, name: name.trim(), factor: Number(factor) }]), { success: 'Unit added', refresh: STOCK_REFRESH, onDone: () => { setAdding(false); setName(''); setFactor('') } })
  const remove = useSave((id: Id) => call('InventoryService', 'deleteUnit', [org.id, id]), { success: 'Unit removed', refresh: STOCK_REFRESH })
  return (
    <Table min={300}>
      <thead><tr><Head>Unit</Head><Head right>Holds</Head><Head right>{canWrite ? <button className="font-medium text-foreground cursor-pointer inline-flex items-center gap-1" onClick={() => setAdding(true)}><Plus className="size-3" />Add unit</button> : null}</Head></tr></thead>
      <tbody>
        <tr><Cell>{item.unit_of_measure} <Badge>Base</Badge></Cell><Cell right>1</Cell><Cell right>{''}</Cell></tr>
        {item.units.map((u) => <tr key={u.id}><Cell>{u.name}</Cell><Cell right>{num(u.factor)} {item.unit_of_measure}</Cell><Cell right>{canWrite ? <button aria-label={`Remove ${u.name}`} disabled={remove.isPending} onClick={() => remove.mutate(u.id)} className="text-muted-foreground cursor-pointer"><Trash2 className="size-3.5" /></button> : ''}</Cell></tr>)}
      </tbody>
      {adding ? (
        <tfoot><tr><td colSpan={3} className="p-0">
          <Modal open onClose={() => setAdding(false)} title="Add a unit">
            <FormBody onSubmit={() => save.mutate()} submit="Add unit" pending={save.isPending} onCancel={() => setAdding(false)} disabled={!name.trim() || !(Number(factor) > 0)}>
              <div className="grid sm:grid-cols-2 gap-3">
                <Text label="Unit name" placeholder="Box, Pallet, Dozen" value={name} onChange={setName} />
                <Text label={`How many ${item.unit_of_measure} in one`} inputMode="decimal" value={factor} onChange={setFactor} />
              </div>
            </FormBody>
          </Modal>
        </td></tr></tfoot>
      ) : null}
    </Table>
  )
}

function SerialsTable({ item }: { item: ItemDetail }) {
  return (
    <section className="flex flex-col gap-2" aria-label="Serial numbers">
      <h2 className="font-semibold text-[14px]">Serial numbers in stock <span className="text-muted-foreground font-normal">{item.serials.length}</span></h2>
      {item.serials.length === 0 ? <Empty title="None in stock" body="Units appear here as they arrive." /> : (
        <Paged rows={item.serials} size={12}>
          {(page, pager) => (
            <Table min={360} footer={pager}>
              <thead><tr><Head>Serial number</Head><Head>Warehouse</Head></tr></thead>
              <tbody>{page.map((s) => <tr key={s.id}><Cell className="fig text-[12.5px]">{s.serial_number}</Cell><Cell className="text-muted-foreground">{s.warehouse_name ?? ''}</Cell></tr>)}</tbody>
            </Table>
          )}
        </Paged>
      )}
    </section>
  )
}

type WhDraft = { id?: Id; name: string; code: string; address: string; is_default: boolean; is_active: boolean }

export function Warehouses() {
  const { org } = useApp()
  const canWrite = useCanWriteStock()
  const list = useQuery(warehousesQuery(org.id))
  const [draft, setDraft] = useState<WhDraft | null>(null)
  const [moving, setMoving] = useState(false)
  const all = list.data ?? []
  const active = all.filter((w) => w.is_active)
  return (
    <Screen
      title="Inventory"
      sub="Where your stock is kept, and moving it between places."
      actions={canWrite ? <>
        <button className={btn.plain} disabled={active.length < 2} title={active.length < 2 ? 'Add a second warehouse first' : undefined} onClick={() => setMoving(true)}>Transfer stock</button>
        <button className={btn.primary} onClick={() => setDraft({ name: '', code: '', address: '', is_default: false, is_active: true })}><Plus className="size-3.5 mr-1.5" />New warehouse</button>
      </> : undefined}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No warehouses yet" body="A Main warehouse is created when you first need one." /> : null)}>
        {(rows) => (
          <Table min={560}>
            <thead><tr><Head>Warehouse</Head><Head>Code</Head><Head right>Items</Head><Head right>Units</Head><Head right>Value</Head></tr></thead>
            <tbody>
              {rows.map((w) => (
                <tr key={w.id} className={cn('hover:bg-accent/50', canWrite && 'cursor-pointer')} onClick={canWrite ? () => setDraft({ id: w.id, name: w.name, code: w.code ?? '', address: w.address ?? '', is_default: w.is_default, is_active: w.is_active }) : undefined}>
                  <Cell><span className="flex items-center gap-2">{w.name}{w.is_default ? <Badge>Default</Badge> : null}{!w.is_active ? <Badge tone="warn">Closed</Badge> : null}</span>{w.address ? <span className="block text-[12.5px] text-muted-foreground">{w.address}</span> : null}</Cell>
                  <Cell className="fig text-[12.5px] text-muted-foreground">{w.code ?? ''}</Cell>
                  <Cell right>{figure(num(w.items), 0)}</Cell>
                  <Cell right>{figure(num(w.units), 0)}</Cell>
                  <Cell right>{figure(num(w.value), org.decimals)}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Loaded>
      {draft ? <WarehouseForm key={String(draft.id ?? 'new')} draft={draft} onClose={() => setDraft(null)} /> : null}
      {moving ? <TransferForm warehouses={active} onClose={() => setMoving(false)} /> : null}
    </Screen>
  )
}

function WarehouseForm({ draft, onClose }: { draft: WhDraft; onClose: () => void }) {
  const { org } = useApp()
  const [f, setF] = useState(draft)
  const save = useSave(() => call('InventoryService', 'saveWarehouse', [org.id, { id: f.id, name: f.name.trim(), code: f.code.trim() || null, address: f.address.trim() || null, is_default: f.is_default, is_active: f.is_active }]), { success: 'Warehouse saved', refresh: STOCK_REFRESH, onDone: onClose })
  return (
    <Modal open onClose={onClose} title={f.id != null ? 'Edit warehouse' : 'New warehouse'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save warehouse" pending={save.isPending} onCancel={onClose} disabled={!f.name.trim()}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Name" required value={f.name} onChange={(v) => setF((x) => ({ ...x, name: v }))} />
          <Text label="Short code" value={f.code} onChange={(v) => setF((x) => ({ ...x, code: v }))} />
        </div>
        <Text label="Address" value={f.address} onChange={(v) => setF((x) => ({ ...x, address: v }))} />
        <Toggle label="Default warehouse" hint="Used when a movement doesn't say where." checked={f.is_default} onChange={(v) => setF((x) => ({ ...x, is_default: v }))} />
        {f.id != null ? <Toggle label="Open" hint="A warehouse has to be empty before it can close." checked={f.is_active} onChange={(v) => setF((x) => ({ ...x, is_active: v }))} /> : null}
      </FormBody>
    </Modal>
  )
}

function TransferForm({ warehouses, onClose }: { warehouses: Warehouse[]; onClose: () => void }) {
  const { org } = useApp()
  const list = useQuery(items(org.id))
  const [from, setFrom] = useState(String(warehouses.find((w) => w.is_default)?.id ?? warehouses[0]?.id ?? ''))
  const [to, setTo] = useState(String(warehouses.find((w) => !w.is_default)?.id ?? ''))
  const [date, setDate] = useState(today())
  const [reference, setReference] = useState('')
  const [lines, setLines] = useState([{ key: 1, item_id: '', quantity: '', serials: '' }])
  const [next, setNext] = useState(2)
  const save = useSave(() => call('InventoryService', 'transferStock', [org.id, { from_warehouse_id: Number(from), to_warehouse_id: Number(to), date, reference: reference.trim() || null, lines: lines.map((l) => ({ item_id: Number(l.item_id), quantity: Number(l.quantity), serial_numbers: l.serials.trim() || null })) }]), { success: 'Stock moved', refresh: STOCK_REFRESH, onDone: onClose })
  const options = warehouses.map((w) => ({ value: String(w.id), label: w.name }))
  const update = (key: number, patch: Partial<(typeof lines)[number]>) => setLines((ls) => ls.map((l) => (l.key === key ? { ...l, ...patch } : l)))
  return (
    <Modal wide open onClose={onClose} title="Transfer stock">
      <FormBody onSubmit={() => save.mutate()} submit="Move stock" pending={save.isPending} onCancel={onClose} disabled={!from || !to || from === to || lines.some((l) => !l.item_id || !(Number(l.quantity) > 0))}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label="From" value={from} onChange={setFrom} options={options} />
          <Choice label="To" placeholder="Select warehouse" value={to} onChange={setTo} options={options} />
          <Text label="Date" type="date" value={date} onChange={setDate} />
          <Text label="Reference" placeholder="Created for you if left blank" value={reference} onChange={setReference} />
        </div>
        <div className="flex flex-col gap-1.5">
          {lines.map((l) => (
            <div key={l.key} className="grid grid-cols-[minmax(0,1fr)_88px_24px] gap-1.5 items-center">
              <select aria-label="Item" value={l.item_id} onChange={(e) => update(l.key, { item_id: e.target.value, serials: '' })} className={selectClass}>
                <option value="">Select item</option>
                {(list.data ?? []).map((i) => <option key={i.id} value={String(i.id)}>{i.sku} · {i.name}</option>)}
              </select>
              <Input aria-label="Quantity" inputMode="decimal" placeholder="Qty" value={l.quantity} onChange={(e) => update(l.key, { quantity: e.target.value })} className="h-8 text-right fig" />
              <button type="button" aria-label="Remove line" disabled={lines.length < 2} onClick={() => setLines((ls) => ls.filter((x) => x.key !== l.key))} className="grid place-items-center text-muted-foreground cursor-pointer disabled:opacity-30"><X className="size-3.5" /></button>
              {list.data?.find((i) => String(i.id) === l.item_id)?.track_serials ? <Input aria-label="Serial numbers" placeholder="Serial numbers, separated by commas. Blank takes the oldest." value={l.serials} onChange={(e) => update(l.key, { serials: e.target.value })} className="h-8 col-span-3" /> : null}
            </div>
          ))}
          <div><button type="button" onClick={() => { setLines((ls) => [...ls, { key: next, item_id: '', quantity: '', serials: '' }]); setNext((k) => k + 1) }} className="inline-flex items-center gap-1 text-[13px] font-medium cursor-pointer"><Plus className="size-3.5" />Add line</button></div>
        </div>
        <p className="text-[12.5px] text-muted-foreground">This changes where stock is, not what it's worth, so your books don't change. Batches go first-to-expire and keep their expiry date.</p>
      </FormBody>
    </Modal>
  )
}
