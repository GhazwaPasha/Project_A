import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { AskLink } from '@/components/agent-panel'
import { Choice, ConfirmDelete, FormBody, Modal, Pill, Stat, Stats, Text, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Screen, Table, Tabs, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, num, q, today, type Id, type Money, type StockItem } from '@/lib/data'
import { cn } from '@/lib/utils'

export const INVENTORY_TABS = [
  { to: '/inventory', label: 'Items' },
  { to: '/inventory/categories', label: 'Categories' },
  { to: '/inventory/transactions', label: 'Stock movements' },
  { to: '/inventory/vouchers', label: 'Vouchers' },
]
export type Item = StockItem & { category_id: Id; description: string | null; reorder_quantity: Money; category?: { name: string } }
export type Category = { id: Id; name: string; description: string | null; inventory_account_id: Id; expense_account_id: Id }
type Movement = { id: Id; item_id: Id; transaction_type: 'in' | 'out' | 'adjustment'; quantity: Money; unit_cost: Money | null; total_cost: Money | null; reference: string | null; description: string | null; transaction_date: string; item?: { name: string; sku: string } }

export const items = (org: string) => q<Item[]>(['stock', org], 'DataService', 'getInventoryItems', [org, false])
export const categories = (org: string) => q<Category[]>(['categories', org], 'DataService', 'getInventoryCategories', [org, false])
const movements = (org: string) => q<Movement[]>(['movements', org], 'DataService', 'getInventoryTransactions', [org, undefined, 200])
const REFRESH = ['stock', 'low-stock', 'categories', 'movements']

export function useCanWriteStock() {
  const { access } = useApp()
  return access !== 'observer'
}

type ItemDraft = { id?: Id; category_id: string; sku: string; name: string; description: string; unit_of_measure: string; reorder_point: string; reorder_quantity: string }

export function Inventory() {
  const { org, pro } = useApp()
  const canWrite = useCanWriteStock()
  const list = useQuery(items(org.id))
  const cats = useQuery(categories(org.id))
  const [search, setSearch] = useState('')
  const [lowOnly, setLowOnly] = useState(false)
  const [draft, setDraft] = useState<ItemDraft | null>(null)
  const [moving, setMoving] = useState<{ itemId: string } | null>(null)
  const isLow = (i: Item) => num(i.reorder_point) > 0 && num(i.quantity_available) <= num(i.reorder_point)
  const rows = useMemo(() => {
    const s = search.trim().toLowerCase()
    return (list.data ?? []).filter((i) => (!lowOnly || isLow(i)) && (!s || `${i.sku} ${i.name}`.toLowerCase().includes(s)))
  }, [list.data, search, lowOnly])
  const all = list.data ?? []
  const value = all.reduce((t, i) => t + num(i.total_value), 0)
  const low = all.filter(isLow).length
  const catName = new Map((cats.data ?? []).map((c) => [String(c.id), c.name]))

  return (
    <Screen
      title="Inventory"
      sub={pro ? 'Items, quantities and average cost.' : 'What you have in stock and what it is worth.'}
      actions={canWrite ? <>
        <button className={btn.plain} onClick={() => setMoving({ itemId: '' })}>Record movement</button>
        <button className={btn.primary} disabled={!cats.data?.length} onClick={() => setDraft({ category_id: '', sku: '', name: '', description: '', unit_of_measure: 'Each', reorder_point: '', reorder_quantity: '' })}><Plus className="size-3.5 mr-1.5" />New item</button>
      </> : undefined}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Stats cols={3}>
        <Stat label="Items" value={all.length} />
        <Stat label={pro ? 'Inventory value' : 'Worth'} value={`${org.currency} ${figure(value, 0)}`} />
        <Stat label="Running low" value={low} tone={low ? 'warn' : undefined} />
      </Stats>
      <div className="flex flex-wrap items-center gap-3">
        <Input aria-label="Search items" placeholder="Search items" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
        <label className="flex items-center gap-2 text-[13px] cursor-pointer"><input type="checkbox" checked={lowOnly} onChange={(e) => setLowOnly(e.target.checked)} />Only running low</label>
        <AskLink className="text-[13px] ml-auto" prompt="Look at my stock. What is running low, and what should I reorder first?">What should I reorder?</AskLink>
      </div>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No items yet" body={cats.data?.length ? 'Add your first stock item.' : 'Create a category first, then add items to it.'} /> : null)}>
        {() => (
          <Table min={640}>
            <thead><tr>{pro ? <Head>SKU</Head> : null}<Head>Item</Head>{pro ? <Head>Category</Head> : null}<Head right>On hand</Head>{pro ? <Head right>Avg. cost</Head> : null}<Head right>Value</Head></tr></thead>
            <tbody>
              {rows.map((i) => (
                <tr key={i.id} className={cn('hover:bg-accent/50', canWrite && 'cursor-pointer')} onClick={canWrite ? () => setDraft({ id: i.id, category_id: String(i.category_id), sku: i.sku, name: i.name, description: i.description ?? '', unit_of_measure: i.unit_of_measure, reorder_point: String(num(i.reorder_point)), reorder_quantity: String(num(i.reorder_quantity)) }) : undefined}>
                  {pro ? <Cell className="fig text-[12.5px] text-muted-foreground">{i.sku}</Cell> : null}
                  <Cell><span className="flex items-center gap-2">{i.name}{isLow(i) ? <Pill tone="warn">Low</Pill> : null}</span></Cell>
                  {pro ? <Cell className="text-muted-foreground">{i.category?.name ?? catName.get(String(i.category_id)) ?? ''}</Cell> : null}
                  <Cell right>{figure(num(i.quantity_available), 0)} {i.unit_of_measure}</Cell>
                  {pro ? <Cell right>{figure(num(i.average_unit_cost), org.decimals)}</Cell> : null}
                  <Cell right>{figure(num(i.total_value), org.decimals)}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Loaded>
      <ItemForm key={`item-${draft?.id ?? (draft ? 'new' : 'closed')}`} draft={draft} cats={cats.data ?? []} onClose={() => setDraft(null)} />
      <MovementForm key={`move-${moving ? 'open' : 'closed'}`} open={moving !== null} itemList={all} onClose={() => setMoving(null)} />
    </Screen>
  )
}

function ItemForm({ draft, cats, onClose }: { draft: ItemDraft | null; cats: Category[]; onClose: () => void }) {
  const { org, userId } = useApp()
  const [f, setF] = useState<ItemDraft>(draft ?? { category_id: '', sku: '', name: '', description: '', unit_of_measure: 'Each', reorder_point: '', reorder_quantity: '' })
  const set = (k: keyof ItemDraft) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const save = useSave(() => {
    const fields = { category_id: Number(f.category_id), sku: f.sku.trim(), name: f.name.trim(), description: f.description.trim() || null, unit_of_measure: f.unit_of_measure.trim() || 'Each', reorder_point: Number(f.reorder_point) || 0, reorder_quantity: Number(f.reorder_quantity) || 0 }
    return f.id != null
      ? call('DataService', 'updateInventoryItem', [f.id, fields])
      : call('DataService', 'createInventoryItem', [{ ...fields, organization_id: org.id, quantity_in: 0, quantity_out: 0, average_unit_cost: 0, is_active: true, created_by: userId }])
  }, { success: 'Item saved', refresh: REFRESH, onDone: onClose })
  const remove = useSave(() => call('DataService', 'deleteInventoryItem', [f.id]), { success: 'Item deleted', refresh: REFRESH, onDone: onClose })
  return (
    <Modal open={draft !== null} onClose={onClose} title={f.id != null ? 'Edit item' : 'New item'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save item" pending={save.isPending} onCancel={onClose} disabled={!f.name.trim() || !f.sku.trim() || !f.category_id}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Item name" required value={f.name} onChange={set('name')} />
          <Text label="SKU" required value={f.sku} onChange={set('sku')} />
          <Choice label="Category" required placeholder="Select category" value={f.category_id} onChange={set('category_id')} options={cats.map((c) => ({ value: String(c.id), label: c.name }))} />
          <Text label="Unit of measure" placeholder="Each, Box, Liter" value={f.unit_of_measure} onChange={set('unit_of_measure')} />
          <Text label="Reorder point" hint="Alert when stock falls to this" inputMode="decimal" value={f.reorder_point} onChange={set('reorder_point')} />
          <Text label="Reorder quantity" hint="Suggested amount to reorder" inputMode="decimal" value={f.reorder_quantity} onChange={set('reorder_quantity')} />
        </div>
        <Text label="Description" value={f.description} onChange={set('description')} />
        {f.id != null ? <ConfirmDelete label="Delete this item" pending={remove.isPending} onConfirm={() => remove.mutate()} /> : null}
      </FormBody>
    </Modal>
  )
}

function MovementForm({ open, itemList, onClose }: { open: boolean; itemList: Item[]; onClose: () => void }) {
  const { org, userId } = useApp()
  const [f, setF] = useState({ item_id: '', type: 'in', quantity: '', unit_cost: '', reference: '', description: '', date: today() })
  const set = (k: keyof typeof f) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const item = itemList.find((i) => String(i.id) === f.item_id)
  const qty = Number(f.quantity)
  const tooMany = f.type === 'out' && item != null && qty > num(item.quantity_available)
  const save = useSave(() => call('DataService', 'createInventoryTransaction', [{
    organization_id: org.id,
    item_id: Number(f.item_id),
    transaction_type: f.type,
    quantity: f.type === 'out' ? -Math.abs(qty) : qty,
    unit_cost: f.unit_cost ? Number(f.unit_cost) : null,
    total_cost: f.unit_cost ? Math.abs(qty) * Number(f.unit_cost) : null,
    journal_entry_id: null,
    reference: f.reference.trim() || null,
    description: f.description.trim() || null,
    transaction_date: f.date,
    created_by: userId,
  }]), { success: 'Stock movement recorded', refresh: REFRESH, onDone: onClose })
  return (
    <Modal open={open} onClose={onClose} title="Record stock movement">
      <FormBody onSubmit={() => save.mutate()} submit="Record" pending={save.isPending} onCancel={onClose} disabled={!f.item_id || !qty || tooMany}>
        <Choice label="Item" required placeholder="Select item" value={f.item_id} onChange={set('item_id')} options={itemList.map((i) => ({ value: String(i.id), label: `${i.name} (${figure(num(i.quantity_available), 0)} ${i.unit_of_measure})` }))} />
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label="What happened" value={f.type} onChange={set('type')} options={[{ value: 'in', label: 'Stock came in' }, { value: 'out', label: 'Stock went out' }, { value: 'adjustment', label: 'Count correction' }]} />
          <Text label="Date" type="date" value={f.date} onChange={set('date')} />
          <Text label="Quantity" required hint={f.type === 'adjustment' ? 'Use a negative number to reduce stock.' : undefined} inputMode="decimal" value={f.quantity} onChange={set('quantity')} />
          {f.type === 'in' ? <Text label="Unit cost" inputMode="decimal" value={f.unit_cost} onChange={set('unit_cost')} /> : null}
          <Text label="Reference" placeholder="PO or invoice number" value={f.reference} onChange={set('reference')} />
        </div>
        <Text label="Notes" value={f.description} onChange={set('description')} />
        {tooMany ? <p role="alert" className="text-[13px] text-destructive">Only {figure(num(item!.quantity_available), 0)} {item!.unit_of_measure} on hand.</p> : null}
        <p className="text-[12.5px] text-muted-foreground">This updates stock only. It does not post an entry to your books yet.</p>
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
          <Table min={560}>
            <thead><tr><Head>Category</Head><Head>Stock account</Head><Head>Cost account</Head></tr></thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id} className={cn('hover:bg-accent/50', canWrite && 'cursor-pointer')} onClick={canWrite ? () => setDraft({ id: c.id, name: c.name, description: c.description ?? '', inventory_account_id: String(c.inventory_account_id), expense_account_id: String(c.expense_account_id) }) : undefined}>
                  <Cell>{c.name}{c.description ? <span className="block text-[12.5px] text-muted-foreground">{c.description}</span> : null}</Cell>
                  <Cell className="text-muted-foreground">{nameOf.get(String(c.inventory_account_id)) ?? ''}</Cell>
                  <Cell className="text-muted-foreground">{nameOf.get(String(c.expense_account_id)) ?? ''}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
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

const MOVE_LABEL = { in: 'In', out: 'Out', adjustment: 'Correction' }

export function Movements() {
  const { org, pro } = useApp()
  const list = useQuery(movements(org.id))
  const [search, setSearch] = useState('')
  const rows = (list.data ?? []).filter((m) => !search.trim() || `${m.item?.name} ${m.reference} ${m.description}`.toLowerCase().includes(search.trim().toLowerCase()))
  return (
    <Screen title="Inventory" sub="Every time stock came in, went out or was corrected." tabs={<Tabs items={INVENTORY_TABS} />}>
      <Input aria-label="Search stock movements" placeholder="Search" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No stock movements yet" body="They appear here as stock comes in and goes out." /> : null)}>
        {() => (
          <Table min={640}>
            <thead><tr><Head>Date</Head><Head>Item</Head><Head>Type</Head>{pro ? <Head>Reference</Head> : null}<Head right>Quantity</Head><Head right>Cost</Head></tr></thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.id}>
                  <Cell className="text-muted-foreground whitespace-nowrap">{shortDate(m.transaction_date)}</Cell>
                  <Cell>{m.item?.name ?? `Item ${m.item_id}`}{m.description ? <span className="block text-[12.5px] text-muted-foreground">{m.description}</span> : null}</Cell>
                  <Cell><Pill tone={m.transaction_type === 'in' ? 'good' : 'neutral'}>{MOVE_LABEL[m.transaction_type]}</Pill></Cell>
                  {pro ? <Cell className="text-muted-foreground">{m.reference ?? ''}</Cell> : null}
                  <Cell right>{figure(num(m.quantity), 0)}</Cell>
                  <Cell right>{m.total_cost != null ? figure(num(m.total_cost), org.decimals) : ''}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Loaded>
    </Screen>
  )
}
