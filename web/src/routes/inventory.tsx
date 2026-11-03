import { useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { Download, Plus, Upload } from 'lucide-react'
import { AskChip } from '@/components/agent-panel'
import { Choice, ConfirmDelete, FormBody, Modal, Stat, Stats, Text, Toggle, download, parseCsv, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, Table, Tabs, Toolbar, btn } from '@/components/page'
import { Badge, Chip, Chips, type Tone } from '@/components/chips'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, num, q, refreshBooks, today, type Id, type Money, type StockItem } from '@/lib/data'
import { cn } from '@/lib/utils'

export const INVENTORY_TABS = [
  { to: '/inventory', label: 'Items' },
  { to: '/inventory/warehouses', label: 'Warehouses' },
  { to: '/inventory/purchase-orders', label: 'Purchase orders' },
  { to: '/inventory/assemblies', label: 'Assemblies' },
  { to: '/inventory/counts', label: 'Counts' },
  { to: '/inventory/planner', label: 'Planner' },
  { to: '/inventory/reports', label: 'Reports' },
  { to: '/inventory/transactions', label: 'Movements' },
  { to: '/inventory/categories', label: 'Categories' },
  { to: '/inventory/vouchers', label: 'Vouchers' },
]
export type Item = StockItem & { category_id: Id; description: string | null; reorder_quantity: Money; category?: { name: string }; barcode?: string | null; selling_price?: Money | null; income_account_id?: Id | null; preferred_supplier_id?: Id | null; lead_time_days?: number; track_lots?: boolean; track_serials?: boolean; costing_method?: 'average' | 'fifo' }
export type Unit = { id: Id; item_id: Id; name: string; factor: number }
export type Category = { id: Id; name: string; description: string | null; inventory_account_id: Id; expense_account_id: Id }
export type Warehouse = { id: Id; name: string; code: string | null; address: string | null; is_default: boolean; is_active: boolean; units: Money; value: Money; items: number }
type MoveType = 'in' | 'out' | 'adjustment' | 'transfer_in' | 'transfer_out'
type Movement = { journal_entry_id?: Id | null; id: Id; item_id: Id; transaction_type: MoveType; quantity: Money; unit_cost: Money | null; total_cost: Money | null; reference: string | null; description: string | null; transaction_date: string; warehouse_id?: Id | null; item?: { name: string; sku: string } }

export const items = (org: string) => q<Item[]>(['stock', org], 'DataService', 'getInventoryItems', [org, false])
export const categories = (org: string) => q<Category[]>(['categories', org], 'DataService', 'getInventoryCategories', [org, false])
export const warehousesQuery = (org: string) => q<Warehouse[]>(['stock', org, 'warehouses'], 'InventoryService', 'listWarehouses', [org])
export const unitsQuery = (org: string) => q<Unit[]>(['stock', org, 'units'], 'InventoryService', 'getAllUnits', [org])
const movements = (org: string) => q<Movement[]>(['movements', org], 'DataService', 'getInventoryTransactions', [org, undefined, 200])
export const STOCK_REFRESH = ['stock', 'low-stock', 'categories', 'movements']
const REFRESH = STOCK_REFRESH

export function useCanWriteStock() {
  const { access } = useApp()
  return access !== 'observer'
}

/** Percent of the selling price left after cost. */
export const marginOf = (i: Pick<Item, 'selling_price' | 'average_unit_cost'>) => (num(i.selling_price) > 0 ? ((num(i.selling_price) - num(i.average_unit_cost)) / num(i.selling_price)) * 100 : null)

export type ItemDraft = { id?: Id; category_id: string; sku: string; name: string; description: string; unit_of_measure: string; reorder_point: string; reorder_quantity: string; barcode: string; selling_price: string; income_account_id: string; preferred_supplier_id: string; lead_time_days: string; track_lots: boolean; track_serials: boolean; costing_method: string }
const blankItem = (): ItemDraft => ({ category_id: '', sku: '', name: '', description: '', unit_of_measure: 'Each', reorder_point: '', reorder_quantity: '', barcode: '', selling_price: '', income_account_id: '', preferred_supplier_id: '', lead_time_days: '14', track_lots: false, track_serials: false, costing_method: '' })
const CSV_COLUMNS = ['sku', 'name', 'category', 'unit', 'barcode', 'selling_price', 'reorder_point', 'reorder_quantity']
const cell = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`

export function Inventory() {
  const { org, pro } = useApp()
  const canWrite = useCanWriteStock()
  const navigate = useNavigate()
  const list = useQuery(items(org.id))
  const cats = useQuery(categories(org.id))
  const [search, setSearch] = useState('')
  const [lowOnly, setLowOnly] = useState(false)
  const [category, setCategory] = useState('all')
  const [draft, setDraft] = useState<ItemDraft | null>(null)
  const [moving, setMoving] = useState<{ itemId: string } | null>(null)
  const file = useRef<HTMLInputElement>(null)
  const isLow = (i: Item) => num(i.reorder_point) > 0 && num(i.quantity_available) <= num(i.reorder_point)
  const rows = useMemo(() => {
    const s = search.trim().toLowerCase()
    return (list.data ?? []).filter((i) => (!lowOnly || isLow(i)) && (category === 'all' || String(i.category_id) === category) && (!s || `${i.sku} ${i.barcode ?? ''} ${i.name}`.toLowerCase().includes(s)))
  }, [list.data, search, lowOnly, category])
  const all = list.data ?? []
  const value = all.reduce((t, i) => t + num(i.total_value), 0)
  const low = all.filter(isLow).length
  const out = all.filter((i) => num(i.quantity_available) <= 0).length
  const catName = new Map((cats.data ?? []).map((c) => [String(c.id), c.name]))
  const open = (id: Id) => navigate({ to: '/inventory/items/$itemId', params: { itemId: String(id) } })
  // A barcode scanner types the code and presses Enter, so an exact match opens the item.
  const onScan = (e: React.KeyboardEvent) => {
    if (e.key !== 'Enter') return
    const s = search.trim().toLowerCase()
    const hit = all.find((i) => i.sku.toLowerCase() === s || (i.barcode ?? '').toLowerCase() === s)
    if (hit) return void open(hit.id)
    if (s) void call<{ item_id: Id }[]>('InventoryService', 'findSerial', [org.id, search.trim()]).then((found) => { if (found[0]) void open(found[0].item_id) })
  }
  const imported = useSave((rowsIn: Record<string, string>[]) => call<{ added: number; updated: number }>('InventoryService', 'importItems', [org.id, rowsIn]), { success: 'Items imported', refresh: REFRESH })
  const exportCsv = () => download('items.csv', [CSV_COLUMNS.join(','), ...all.map((i) => [i.sku, i.name, i.category?.name ?? catName.get(String(i.category_id)), i.unit_of_measure, i.barcode, i.selling_price, num(i.reorder_point), num(i.reorder_quantity)].map(cell).join(','))].join('\n'))

  return (
    <Screen search={<span onKeyDown={onScan}><SearchIcon label="Search items" placeholder="SKU, barcode, serial or name" value={search} onChange={setSearch} /></span>}
      title="Inventory"
      sub={pro ? 'Items, quantities, cost and margin.' : 'What you have in stock and what it is worth.'}
      actions={<>
        {canWrite ? <>
          <input ref={file} aria-label="Items CSV" type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) void f.text().then((t) => imported.mutate(parseCsv(t))); e.target.value = '' }} />
          <button className={btn.plain} title={`Columns: ${CSV_COLUMNS.join(', ')}`} disabled={imported.isPending} onClick={() => file.current?.click()}><Upload className="size-3.5 mr-1.5" />Import</button>
        </> : null}
        <button className={btn.plain} disabled={!all.length} onClick={exportCsv}><Download className="size-3.5 mr-1.5" />Export</button>
        {canWrite ? <>
          <button className={btn.plain} onClick={() => setMoving({ itemId: '' })}>Record movement</button>
          <button className={btn.primary} disabled={!cats.data?.length} onClick={() => setDraft(blankItem())}><Plus className="size-3.5 mr-1.5" />New item</button>
        </> : null}
      </>}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Stats cols={4}>
        <Stat label="Items" value={all.length} />
        <Stat label={pro ? 'Inventory value' : 'Worth'} value={`${org.currency} ${figure(value, 0)}`} />
        <Stat label="Running low" value={low} tone={low ? 'warn' : undefined} />
        <Stat label="Out of stock" value={out} tone={out ? 'warn' : undefined} />
      </Stats>
      <Toolbar>
        <Chip active={lowOnly} count={low} onClick={() => setLowOnly((v) => !v)}>Running low</Chip>
        {(cats.data?.length ?? 0) > 1 ? <Chips label="Category" value={category} onChange={setCategory} options={[{ id: 'all', label: 'All' }, ...(cats.data ?? []).map((c) => ({ id: String(c.id), label: c.name, count: all.filter((i) => String(i.category_id) === String(c.id)).length }))]} /> : null}
        <span className="ml-auto"><AskChip prompt="Look at my stock. What is running low, and what should I reorder first?">What should I reorder?</AskChip></span>
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No items yet" body={cats.data?.length ? 'Add your first stock item, or import a list.' : 'Create a category first, then add items to it.'} /> : null)}>
        {() => rows.length === 0 ? <Empty title="No matches" body="Try a different word, or turn off the filter." /> : (
          <Paged rows={rows}>
            {(page, pager) => (
          <Table min={980} footer={pager}>
            <thead><tr><Head>SKU</Head><Head>Item</Head><Head>Barcode</Head><Head>Category</Head><Head right>On hand</Head><Head right>Reorder at</Head><Head right>{pro ? 'Avg. cost' : 'Cost'}</Head><Head right>Price</Head><Head right>Margin</Head><Head right>Value</Head></tr></thead>
            <tbody>
              {page.map((i) => {
                const margin = marginOf(i)
                return (
                <tr key={i.id} tabIndex={0} className="cursor-pointer hover:bg-accent/50 focus-visible:bg-accent/50 outline-none" onClick={() => open(i.id)} onKeyDown={(e) => { if (e.key === 'Enter') open(i.id) }}>
                  <Cell className="fig text-[12.5px] text-muted-foreground">{i.sku}</Cell>
                  <Cell><span className="flex items-center gap-2">{i.name}{num(i.quantity_available) <= 0 ? <Badge tone="bad" dot>Out of stock</Badge> : isLow(i) ? <Badge tone="warn" dot>Low</Badge> : null}{i.track_lots ? <Badge>Batches</Badge> : null}{i.track_serials ? <Badge>Serials</Badge> : null}{pro && i.costing_method === 'fifo' ? <Badge>FIFO</Badge> : null}</span></Cell>
                  <Cell className="fig text-[12.5px] text-muted-foreground">{i.barcode ?? ''}</Cell>
                  <Cell><Badge>{i.category?.name ?? catName.get(String(i.category_id)) ?? 'None'}</Badge></Cell>
                  <Cell right>{figure(num(i.quantity_available), 0)} {i.unit_of_measure}</Cell>
                  <Cell right>{num(i.reorder_point) ? figure(num(i.reorder_point), 0) : ''}</Cell>
                  <Cell right>{figure(num(i.average_unit_cost), org.decimals)}</Cell>
                  <Cell right>{i.selling_price == null ? '' : figure(num(i.selling_price), org.decimals)}</Cell>
                  <Cell right className={cn(margin !== null && margin < 0 && 'text-destructive')}>{margin === null ? '' : `${figure(margin, 1)}%`}</Cell>
                  <Cell right>{figure(num(i.total_value), org.decimals)}</Cell>
                </tr>
                )
              })}
            </tbody>
          </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {draft ? <ItemForm key={`item-${draft.id ?? 'new'}`} draft={draft} onClose={() => setDraft(null)} onCreated={(id) => open(id)} /> : null}
      <MovementForm key={`move-${moving ? 'open' : 'closed'}`} open={moving !== null} itemList={all} onClose={() => setMoving(null)} />
    </Screen>
  )
}

export function ItemForm({ draft, onClose, onCreated }: { draft: ItemDraft; onClose: () => void; onCreated?: (id: Id) => void }) {
  const { org, userId, canSeeBooks } = useApp()
  const cats = useQuery(categories(org.id))
  const chart = useQuery({ ...accounts(org.id), enabled: canSeeBooks })
  const suppliers = useQuery(q<{ id: Id; name: string }[]>(['supplier-picker', org.id], 'SupplierService', 'getSuppliersForVoucher', [org.id]))
  const [f, setF] = useState<ItemDraft>(draft)
  const set = (k: keyof ItemDraft) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const save = useSave(async () => {
    const details = { barcode: f.barcode.trim() || null, selling_price: f.selling_price === '' ? null : Number(f.selling_price), income_account_id: f.income_account_id ? Number(f.income_account_id) : null, preferred_supplier_id: f.preferred_supplier_id ? Number(f.preferred_supplier_id) : null, lead_time_days: f.lead_time_days === '' ? 14 : Number(f.lead_time_days), track_lots: f.track_lots, track_serials: f.track_serials }
    const fields = { category_id: Number(f.category_id), sku: f.sku.trim(), name: f.name.trim(), description: f.description.trim() || null, unit_of_measure: f.unit_of_measure.trim() || 'Each', reorder_point: Number(f.reorder_point) || 0, reorder_quantity: Number(f.reorder_quantity) || 0 }
    if (f.id != null) {
      await call('InventoryService', 'saveItemDetails', [org.id, f.id, details])
      await call('DataService', 'updateInventoryItem', [f.id, fields])
      if (canSeeBooks && f.costing_method && f.costing_method !== draft.costing_method) await call('InventoryService', 'setItemCosting', [org.id, f.id, f.costing_method])
      return { id: f.id, created: false }
    }
    const made = await call<{ id: Id }>('DataService', 'createInventoryItem', [{ ...fields, ...details, organization_id: org.id, quantity_in: 0, quantity_out: 0, average_unit_cost: 0, is_active: true, created_by: userId }])
    if (canSeeBooks && f.costing_method) await call('InventoryService', 'setItemCosting', [org.id, made.id, f.costing_method])
    return { id: made.id, created: true }
  }, { success: 'Item saved', refresh: REFRESH, onDone: (r) => { onClose(); if (r.created) onCreated?.(r.id) } })
  const navigate = useNavigate()
  const remove = useSave(() => call('DataService', 'deleteInventoryItem', [f.id]), { success: 'Item deleted', refresh: REFRESH, onDone: () => { onClose(); void navigate({ to: '/inventory' }) } })
  const income = (chart.data ?? []).filter((a) => a.is_postable !== false && a.account_type === 'revenue').map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))
  return (
    <Modal wide open onClose={onClose} title={f.id != null ? 'Edit item' : 'New item'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save item" pending={save.isPending} onCancel={onClose} disabled={!f.name.trim() || !f.category_id || (f.id != null && !f.sku.trim())}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Item name" required value={f.name} onChange={set('name')} />
          <Choice label="Category" required placeholder="Select category" value={f.category_id} onChange={set('category_id')} options={(cats.data ?? []).map((c) => ({ value: String(c.id), label: c.name }))} />
          <Text label="SKU" hint={f.id != null ? 'Your code for this item.' : 'Leave blank and one is created for you.'} value={f.sku} onChange={set('sku')} />
          <Text label="Barcode" hint="Type it, or scan into this box." value={f.barcode} onChange={set('barcode')} />
          <Text label="Unit of measure" placeholder="Each, Box, Liter" value={f.unit_of_measure} onChange={set('unit_of_measure')} />
          <Text label="Selling price" inputMode="decimal" hint="Fills in when you add this item to an invoice." value={f.selling_price} onChange={set('selling_price')} />
          <Text label="Reorder point" hint="Alert when stock falls to this" inputMode="decimal" value={f.reorder_point} onChange={set('reorder_point')} />
          <Text label="Reorder quantity" hint="Suggested amount to reorder" inputMode="decimal" value={f.reorder_quantity} onChange={set('reorder_quantity')} />
          <Choice label="Usually bought from" placeholder="No usual supplier" value={f.preferred_supplier_id} onChange={set('preferred_supplier_id')} options={(suppliers.data ?? []).map((s) => ({ value: String(s.id), label: s.name }))} />
          <Text label="Delivery takes (days)" inputMode="numeric" hint="The planner uses this to order in time." value={f.lead_time_days} onChange={set('lead_time_days')} />
          {canSeeBooks ? <Choice label="Income account" placeholder="Choose on each invoice" hint="Where sales of this item are recorded." value={f.income_account_id} onChange={set('income_account_id')} options={income} /> : null}
          {canSeeBooks ? <Choice label="Costing method" placeholder="Your usual method" hint="Switching keeps today's value. It changes how later issues are costed." value={f.costing_method} onChange={set('costing_method')} options={[{ value: 'average', label: 'Moving average' }, { value: 'fifo', label: 'First in, first out' }]} /> : null}
        </div>
        <Text label="Description" value={f.description} onChange={set('description')} />
        <Toggle label="Track batches and expiry dates" hint="For items with lot numbers or use-by dates. The first to expire is used first." checked={f.track_lots} onChange={(v) => setF((x) => ({ ...x, track_lots: v, track_serials: v ? false : x.track_serials }))} />
        <Toggle label="Track serial numbers" hint="For items where each unit has its own number. Numbers you leave out are created from the SKU." checked={f.track_serials} onChange={(v) => setF((x) => ({ ...x, track_serials: v, track_lots: v ? false : x.track_lots }))} />
        {f.id != null ? <ConfirmDelete label="Delete this item" pending={remove.isPending} onConfirm={() => remove.mutate()} /> : null}
      </FormBody>
    </Modal>
  )
}

function MovementForm({ open, itemList, onClose }: { open: boolean; itemList: Item[]; onClose: () => void }) {
  const { org, userId } = useApp()
  const [f, setF] = useState({ item_id: '', type: 'in', quantity: '', unit_cost: '', reference: '', description: '', date: today(), warehouse_id: '', lot_number: '', expiry_date: '', unit_id: '', serial_numbers: '' })
  const units = useQuery({ ...unitsQuery(org.id), enabled: open })
  const warehouses = useQuery({ ...warehousesQuery(org.id), enabled: open })
  const openWarehouses = (warehouses.data ?? []).filter((w) => w.is_active)
  const set = (k: keyof typeof f) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const item = itemList.find((i) => String(i.id) === f.item_id)
  const itemUnits = (units.data ?? []).filter((u) => String(u.item_id) === f.item_id)
  const factor = num(itemUnits.find((u) => String(u.id) === f.unit_id)?.factor) || 1
  // Stock is always kept in the item's own unit, whatever it was counted in here.
  const qty = Number(f.quantity) * factor
  const unitCost = f.unit_cost ? Number(f.unit_cost) / factor : null
  const tooMany = f.type === 'out' && item != null && qty > num(item.quantity_available)
  const { canSeeBooks } = useApp()
  const chart = useQuery({ ...accounts(org.id), enabled: open && canSeeBooks })
  const [offset, setOffset] = useState('')
  const signed = f.type === 'out' ? -Math.abs(qty) : qty
  const where = { warehouse_id: f.warehouse_id ? Number(f.warehouse_id) : null, lot_number: f.lot_number.trim() || null, expiry_date: f.expiry_date || null, serial_numbers: f.serial_numbers.trim() || null }
  // People with access to the books record the stock and its entry together. Others record stock for an accountant to post.
  const save = useSave(() => canSeeBooks
    ? call('BooksService', 'recordStockMovement', [org.id, { item_id: Number(f.item_id), transaction_type: f.type, quantity: f.type === 'adjustment' ? qty : Math.abs(qty), unit_cost: unitCost, reference: f.reference.trim() || null, description: f.description.trim() || null, transaction_date: f.date, offset_account_id: offset ? Number(offset) : null, ...where }])
    : call('DataService', 'createInventoryTransaction', [{
      organization_id: org.id,
      item_id: Number(f.item_id),
      transaction_type: f.type,
      quantity: signed,
      unit_cost: unitCost,
      total_cost: unitCost ? Math.abs(qty) * unitCost : null,
      journal_entry_id: null,
      reference: f.reference.trim() || null,
      description: f.description.trim() || null,
      transaction_date: f.date,
      created_by: userId,
      ...where,
    }]), { success: canSeeBooks ? 'Recorded, with its entry in your books' : 'Recorded. An accountant will post it to the books.', refresh: REFRESH, onDone: () => { refreshBooks(); onClose() } })
  const offsetOptions = (chart.data ?? []).filter((a) => a.is_postable !== false).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))
  const needsOffset = canSeeBooks && f.type === 'in'
  return (
    <Modal open={open} onClose={onClose} title="Record stock movement">
      <FormBody onSubmit={() => save.mutate()} submit="Record" pending={save.isPending} onCancel={onClose} disabled={!f.item_id || !qty || tooMany || (needsOffset && !offset)}>
        <Choice label="Item" required placeholder="Select item" value={f.item_id} onChange={set('item_id')} options={itemList.map((i) => ({ value: String(i.id), label: `${i.sku} · ${i.name} (${figure(num(i.quantity_available), 0)} ${i.unit_of_measure})` }))} />
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label="What happened" value={f.type} onChange={set('type')} options={[{ value: 'in', label: 'Stock came in' }, { value: 'out', label: 'Stock went out' }, { value: 'adjustment', label: 'Count correction' }]} />
          <Text label="Date" type="date" value={f.date} onChange={set('date')} />
          <Text label="Quantity" required hint={f.type === 'adjustment' ? 'Use a negative number to reduce stock.' : undefined} inputMode="decimal" value={f.quantity} onChange={set('quantity')} />
          {f.type === 'in' ? <Text label="Unit cost" inputMode="decimal" value={f.unit_cost} onChange={set('unit_cost')} /> : null}
          <Text label="Reference" placeholder="PO or invoice number" value={f.reference} onChange={set('reference')} />
          {itemUnits.length ? <Choice label="Unit" placeholder={item?.unit_of_measure ?? 'Base unit'} value={f.unit_id} onChange={set('unit_id')} options={itemUnits.map((u) => ({ value: String(u.id), label: `${u.name} (${u.factor} ${item?.unit_of_measure})` }))} /> : null}
          {openWarehouses.length > 1 ? <Choice label="Warehouse" placeholder="Default warehouse" value={f.warehouse_id} onChange={set('warehouse_id')} options={openWarehouses.map((w) => ({ value: String(w.id), label: w.name }))} /> : null}
          {item?.track_lots && f.type === 'in' ? <Text label="Batch number" placeholder="Created from the reference if blank" value={f.lot_number} onChange={set('lot_number')} /> : null}
          {item?.track_lots && f.type === 'in' ? <Text label="Expiry date" type="date" value={f.expiry_date} onChange={set('expiry_date')} /> : null}
        </div>
        {item?.track_lots && f.type === 'out' ? <p className="text-[12.5px] text-muted-foreground">Taken from the batch that expires first.</p> : null}
        {item?.track_serials ? <Text label="Serial numbers" hint={f.type === 'out' ? 'Separate with commas. Leave blank to take the oldest units.' : "Separate with commas. Leave blank and they're created from the SKU."} value={f.serial_numbers} onChange={set('serial_numbers')} /> : null}
        <Text label="Notes" value={f.description} onChange={set('description')} />
        {tooMany ? <p role="alert" className="text-[13px] text-destructive">Only {figure(num(item!.quantity_available), 0)} {item!.unit_of_measure} on hand.</p> : null}
        {canSeeBooks ? <Choice label={f.type === 'in' ? 'Where did it come from?' : 'Where does the cost go?'} required={needsOffset} hint={f.type === 'in' ? 'For example, what you owe a supplier, or the bank.' : "Leave blank to use the category's cost account."} placeholder={f.type === 'in' ? 'Select account' : "Category's cost account"} value={offset} onChange={setOffset} options={offsetOptions} /> : <p className="text-[12.5px] text-muted-foreground">This updates stock. An accountant then posts it to the books.</p>}
      </FormBody>
    </Modal>
  )
}

type CatDraft = { id?: Id; name: string; description: string; inventory_account_id: string; expense_account_id: string }

export function Categories() {
  const { org } = useApp()
  const canWrite = useCanWriteStock()
  const list = useQuery(categories(org.id))
  const chart = useQuery(accounts(org.id))
  const [draft, setDraft] = useState<CatDraft | null>(null)
  const nameOf = new Map((chart.data ?? []).map((a) => [String(a.id), `${a.code} ${a.name}`]))
  return (
    <Screen title="Inventory" sub="Categories decide which accounts stock uses." tabs={<Tabs items={INVENTORY_TABS} />} actions={canWrite ? <button className={btn.primary} onClick={() => setDraft({ name: '', description: '', inventory_account_id: '', expense_account_id: '' })}><Plus className="size-3.5 mr-1.5" />New category</button> : undefined}>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No categories yet" body="Create a category, for example Packaging or Raw materials." /> : null)}>
        {(rows) => (
          <Paged rows={rows}>
            {(page, pager) => (
          <Table min={560} footer={pager}>
            <thead><tr><Head>Category</Head><Head>Stock account</Head><Head>Cost account</Head></tr></thead>
            <tbody>
              {page.map((c) => (
                <tr key={c.id} className={cn('hover:bg-accent/50', canWrite && 'cursor-pointer')} onClick={canWrite ? () => setDraft({ id: c.id, name: c.name, description: c.description ?? '', inventory_account_id: String(c.inventory_account_id), expense_account_id: String(c.expense_account_id) }) : undefined}>
                  <Cell>{c.name}{c.description ? <span className="ml-2 text-[12.5px] text-muted-foreground">{c.description}</span> : null}</Cell>
                  <Cell className="text-muted-foreground">{nameOf.get(String(c.inventory_account_id)) ?? ''}</Cell>
                  <Cell className="text-muted-foreground">{nameOf.get(String(c.expense_account_id)) ?? ''}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
            )}
          </Paged>
        )}
      </Loaded>
      <CategoryForm key={String(draft?.id ?? (draft ? 'new' : 'closed'))} draft={draft} onClose={() => setDraft(null)} />
    </Screen>
  )
}

function CategoryForm({ draft, onClose }: { draft: CatDraft | null; onClose: () => void }) {
  const { org, userId } = useApp()
  const chart = useQuery({ ...accounts(org.id), enabled: draft !== null })
  const [f, setF] = useState<CatDraft>(draft ?? { name: '', description: '', inventory_account_id: '', expense_account_id: '' })
  const set = (k: keyof CatDraft) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const options = (chart.data ?? []).filter((a) => a.is_postable !== false).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))
  const save = useSave(() => {
    const fields = { name: f.name.trim(), description: f.description.trim() || null, inventory_account_id: Number(f.inventory_account_id), expense_account_id: Number(f.expense_account_id) }
    return f.id != null
      ? call('DataService', 'updateInventoryCategory', [f.id, fields])
      : call('DataService', 'createInventoryCategory', [{ ...fields, organization_id: org.id, parent_id: null, is_active: true, created_by: userId }])
  }, { success: 'Category saved', refresh: REFRESH, onDone: onClose })
  const remove = useSave(() => call('DataService', 'deleteInventoryCategory', [f.id]), { success: 'Category deleted', refresh: REFRESH, onDone: onClose })
  return (
    <Modal open={draft !== null} onClose={onClose} title={f.id != null ? 'Edit category' : 'New category'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save category" pending={save.isPending} onCancel={onClose} disabled={!f.name.trim() || !f.inventory_account_id || !f.expense_account_id}>
        <Text label="Category name" required value={f.name} onChange={set('name')} />
        <Choice label="Stock account" hint="Where the value of stock in this category is held." required placeholder="Select account" value={f.inventory_account_id} onChange={set('inventory_account_id')} options={options} />
        <Choice label="Cost account" hint="Where the cost goes when stock is used or sold." required placeholder="Select account" value={f.expense_account_id} onChange={set('expense_account_id')} options={options} />
        <Text label="Description" value={f.description} onChange={set('description')} />
        {f.id != null ? <ConfirmDelete label="Delete this category" pending={remove.isPending} onConfirm={() => remove.mutate()} /> : null}
      </FormBody>
    </Modal>
  )
}

export const MOVE_LABEL = { in: 'In', out: 'Out', adjustment: 'Correction', transfer_in: 'Transfer in', transfer_out: 'Transfer out' }
export const MOVE_TONE: Record<MoveType, Tone> = { in: 'good', out: 'bad', adjustment: 'warn', transfer_in: 'neutral', transfer_out: 'neutral' }
const isTransfer = (t: MoveType) => t === 'transfer_in' || t === 'transfer_out'

export function Movements() {
  const { org, pro, canSeeBooks } = useApp()
  const [posting, setPosting] = useState<Movement | null>(null)
  const list = useQuery(movements(org.id))
  const [search, setSearch] = useState('')
  const [kind, setKind] = useState('all')
  const all = list.data ?? []
  const warehouses = useQuery(warehousesQuery(org.id))
  const whName = new Map((warehouses.data ?? []).map((w) => [String(w.id), w.name]))
  const manyPlaces = (warehouses.data?.length ?? 0) > 1
  const matches = (m: Movement) => kind === 'all' || (kind === 'transfer' ? isTransfer(m.transaction_type) : m.transaction_type === kind)
  const rows = all.filter((m) => matches(m) && (!search.trim() || `${m.item?.sku} ${m.item?.name} ${m.reference} ${m.description}`.toLowerCase().includes(search.trim().toLowerCase())))
  return (
    <Screen search={<SearchIcon label="Search stock movements" placeholder="Search" value={search} onChange={setSearch} />} title="Inventory" sub="Every time stock came in, went out or was corrected." tabs={<Tabs items={INVENTORY_TABS} />}>
      <Toolbar>
        <Chips label="Type" value={kind} onChange={setKind} options={[{ id: 'all', label: 'All', count: all.length }, ...(['in', 'out', 'adjustment'] as const).map((k) => ({ id: k, label: MOVE_LABEL[k], count: all.filter((m) => m.transaction_type === k).length })), { id: 'transfer', label: 'Transfers', count: all.filter((m) => isTransfer(m.transaction_type)).length }]} />
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No stock movements yet" body="They appear here as stock comes in and goes out." /> : null)}>
        {() => (
          <Paged rows={rows}>
            {(page, pager) => (
          <Table min={720} footer={pager}>
            <thead><tr><Head>Date</Head><Head>SKU</Head><Head>Item</Head><Head>Type</Head>{manyPlaces ? <Head>Warehouse</Head> : null}<Head>Notes</Head>{pro ? <Head>Reference</Head> : null}<Head>Books</Head><Head right>Quantity</Head><Head right>Cost</Head></tr></thead>
            <tbody>
              {page.map((m) => (
                <tr key={m.id}>
                  <Cell className="text-muted-foreground whitespace-nowrap">{shortDate(m.transaction_date)}</Cell>
                  <Cell className="fig text-[12.5px] text-muted-foreground">{m.item?.sku ?? ''}</Cell>
                  <Cell className="whitespace-nowrap">{m.item?.name ?? `Item ${m.item_id}`}</Cell>
                  <Cell><Badge dot tone={MOVE_TONE[m.transaction_type]}>{MOVE_LABEL[m.transaction_type]}</Badge></Cell>
                  {manyPlaces ? <Cell className="text-muted-foreground whitespace-nowrap">{whName.get(String(m.warehouse_id)) ?? ''}</Cell> : null}
                  <Cell className="max-w-0 w-full truncate text-muted-foreground">{m.description ?? ''}</Cell>
                  {pro ? <Cell className="text-muted-foreground">{m.reference ?? ''}</Cell> : null}
                  <Cell>{isTransfer(m.transaction_type) ? <Badge>No change</Badge> : m.journal_entry_id ? <Badge dot tone="good">In books</Badge> : !num(m.total_cost) ? <Badge>No value</Badge> : canSeeBooks ? <button onClick={() => setPosting(m)} className="text-[13px] font-medium underline underline-offset-[3px] cursor-pointer">Post</button> : <Badge dot tone="warn">Not yet</Badge>}</Cell>
                  <Cell right>{figure(num(m.quantity), 0)}</Cell>
                  <Cell right>{m.total_cost != null ? figure(num(m.total_cost), org.decimals) : ''}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {posting ? <PostMovement movement={posting} onClose={() => setPosting(null)} /> : null}
    </Screen>
  )
}

function PostMovement({ movement: m, onClose }: { movement: Movement; onClose: () => void }) {
  const { org } = useApp()
  const chart = useQuery(accounts(org.id))
  const [offset, setOffset] = useState('')
  const save = useSave(() => call('BooksService', 'postStockMovement', [org.id, m.id, { offset_account_id: offset ? Number(offset) : null }]), { success: 'Posted to your books', refresh: REFRESH, onDone: () => { refreshBooks(); onClose() } })
  const needsOffset = m.transaction_type === 'in'
  return (
    <Modal open onClose={onClose} title="Post to your books">
      <FormBody onSubmit={() => save.mutate()} submit={`Post ${figure(Math.abs(num(m.total_cost)), org.decimals)}`} pending={save.isPending} onCancel={onClose} disabled={needsOffset && !offset}>
        <p className="text-[13.5px]">{m.item?.name ?? `Item ${m.item_id}`}, {shortDate(m.transaction_date)}.</p>
        <Choice label={needsOffset ? 'Where did it come from?' : 'Where does the cost go?'} placeholder={needsOffset ? 'Select account' : "Category's cost account"} value={offset} onChange={setOffset} options={(chart.data ?? []).filter((a) => a.is_postable !== false).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))} />
      </FormBody>
    </Modal>
  )
}
