import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Plus, X } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { AskChip } from '@/components/agent-panel'
import { Badge, Chips } from '@/components/chips'
import { Choice, ConfirmDelete, FormBody, Modal, Stat, Stats, Text, selectClass, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, Table, Tabs, Toolbar, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, num, q, refreshBooks, today, type Id } from '@/lib/data'
import { INVENTORY_TABS, STOCK_REFRESH, items, useCanWriteStock, warehousesQuery } from '@/routes/inventory'

type BomLine = { id: Id; item_id: Id; quantity: number; sku: string; name: string; unit_of_measure: string; on_hand: number; cost: number }
type Bom = { id: Id; item_id: Id; output_quantity: number; notes: string | null; sku: string; name: string; unit_of_measure: string; on_hand: number; lines: BomLine[]; cost_each: number; can_build: number }
type Build = { id: Id; number: string; status: string; item_id: Id; quantity: number; build_date: string; components_cost: number; extra_cost: number; sku: string; name: string; unit_of_measure: string; warehouse_name: string }

const bomsQuery = (org: string) => q<Bom[]>(['stock', org, 'boms'], 'InventoryService', 'listBoms', [org])

/** What's made from what, and building it. */
export function Assemblies() {
  const { org, pro, canSeeBooks } = useApp()
  const canWrite = useCanWriteStock()
  const boms = useQuery(bomsQuery(org.id))
  const builds = useQuery(q<Build[]>(['stock', org.id, 'builds'], 'InventoryService', 'listAssemblies', [org.id]))
  const [view, setView] = useState('made')
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<Bom | 'new' | null>(null)
  const [building, setBuilding] = useState<Bom | 'pick' | null>(null)
  const [undoing, setUndoing] = useState<Build | null>(null)
  const all = boms.data ?? []
  const history = builds.data ?? []
  const s = search.trim().toLowerCase()
  const shown = all.filter((b) => !s || `${b.sku} ${b.name}`.toLowerCase().includes(s))
  const shownBuilds = history.filter((b) => !s || `${b.number} ${b.sku} ${b.name}`.toLowerCase().includes(s))
  const month = today().slice(0, 7)
  return (
    <Screen
      title="Inventory"
      sub={pro ? 'Bills of materials and assembly builds.' : 'What you make from other items, and building it.'}
      search={<SearchIcon label="Search assemblies" value={search} onChange={setSearch} />}
      actions={canWrite ? <>
        <button className={btn.plain} onClick={() => setEditing('new')}><Plus className="size-3.5 mr-1.5" />{pro ? 'New bill of materials' : 'New list of parts'}</button>
        <button className={btn.primary} disabled={!all.length} onClick={() => setBuilding('pick')}>Build</button>
      </> : undefined}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Stats cols={3}>
        <Stat label="Items you make" value={all.length} />
        <Stat label="Can't build right now" value={all.filter((b) => b.can_build < 1).length} tone={all.some((b) => b.can_build < 1) ? 'warn' : undefined} />
        <Stat label="Builds this month" value={history.filter((b) => b.status === 'built' && b.build_date.slice(0, 7) === month).length} />
      </Stats>
      <Toolbar>
        <Chips label="View" value={view} onChange={setView} options={[{ id: 'made', label: pro ? 'Bills of materials' : 'What you make', count: all.length }, { id: 'builds', label: 'Builds', count: history.length }]} />
        <span className="ml-auto"><AskChip prompt="Look at what I make and what parts I have. What can I build, and which parts are holding me back?">What's holding me back?</AskChip></span>
      </Toolbar>
      {view === 'made' ? (
        <Loaded query={boms} empty={(d) => (d.length === 0 ? <Empty title="Nothing here yet" body="List the parts an item is made from, then build it. Parts go out of stock and the finished item comes in at what they cost." /> : null)}>
          {() => shown.length === 0 ? <Empty title="No matches" body="Try another word." /> : (
            <Paged rows={shown}>
              {(page, pager) => (
                <Table min={780} footer={pager}>
                  <thead><tr><Head>SKU</Head><Head>Item</Head><Head>Parts</Head><Head right>On hand</Head><Head right>Cost each</Head><Head right>Can build</Head>{canWrite ? <Head /> : null}</tr></thead>
                  <tbody>
                    {page.map((b) => (
                      <tr key={b.id} className={canWrite ? 'cursor-pointer hover:bg-accent/50' : undefined} onClick={canWrite ? () => setEditing(b) : undefined}>
                        <Cell className="fig text-[12.5px] text-muted-foreground">{b.sku}</Cell>
                        <Cell>{b.name}</Cell>
                        <Cell className="max-w-0 w-full truncate text-muted-foreground">{b.lines.map((l) => `${figure(num(l.quantity), 0)} ${l.name}`).join(', ')}</Cell>
                        <Cell right>{figure(num(b.on_hand), 0)} {b.unit_of_measure}</Cell>
                        <Cell right>{figure(num(b.cost_each), org.decimals)}</Cell>
                        <Cell right>{b.can_build < 1 ? <Badge dot tone="bad">None</Badge> : figure(b.can_build, 0)}</Cell>
                        {canWrite ? <Cell right><button className="text-[13px] font-medium underline underline-offset-[3px] cursor-pointer" onClick={(e) => { e.stopPropagation(); setBuilding(b) }}>Build</button></Cell> : null}
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Paged>
          )}
        </Loaded>
      ) : (
        <Loaded query={builds} empty={(d) => (d.length === 0 ? <Empty title="No builds yet" body="Every build appears here, with what it cost." /> : null)}>
          {() => shownBuilds.length === 0 ? <Empty title="No matches" body="Try another word." /> : (
            <Paged rows={shownBuilds}>
              {(page, pager) => (
                <Table min={780} footer={pager}>
                  <thead><tr><Head>Number</Head><Head>Item</Head><Head>Warehouse</Head><Head>Date</Head><Head right>Built</Head><Head right>Parts</Head><Head right>Extra</Head>{canSeeBooks ? <Head /> : null}</tr></thead>
                  <tbody>
                    {page.map((b) => (
                      <tr key={b.id}>
                        <Cell className="fig text-[12.5px]">{b.number}</Cell>
                        <Cell className="max-w-0 w-full truncate"><span className="flex items-center gap-2"><Link to="/inventory/items/$itemId" params={{ itemId: String(b.item_id) }} className="hover:underline underline-offset-[3px]">{b.name}</Link>{b.status === 'reversed' ? <Badge>Undone</Badge> : null}</span></Cell>
                        <Cell className="text-muted-foreground">{b.warehouse_name}</Cell>
                        <Cell className="text-muted-foreground">{shortDate(b.build_date)}</Cell>
                        <Cell right>{figure(num(b.quantity), 0)} {b.unit_of_measure}</Cell>
                        <Cell right>{figure(num(b.components_cost), org.decimals)}</Cell>
                        <Cell right>{num(b.extra_cost) ? figure(num(b.extra_cost), org.decimals) : ''}</Cell>
                        {canSeeBooks ? <Cell right>{b.status === 'built' ? <button className="text-[13px] font-medium underline underline-offset-[3px] cursor-pointer" onClick={() => setUndoing(b)}>Undo</button> : ''}</Cell> : null}
                      </tr>
                    ))}
                  </tbody>
                </Table>
              )}
            </Paged>
          )}
        </Loaded>
      )}
      {editing ? <BomForm bom={editing === 'new' ? null : editing} onClose={() => setEditing(null)} /> : null}
      {building ? <BuildForm boms={all} initial={building === 'pick' ? null : building} onClose={() => setBuilding(null)} /> : null}
      {undoing ? <UndoBuild build={undoing} onClose={() => setUndoing(null)} /> : null}
    </Screen>
  )
}

function BomForm({ bom, onClose }: { bom: Bom | null; onClose: () => void }) {
  const { org, pro } = useApp()
  const list = useQuery(items(org.id))
  const [item, setItem] = useState(bom ? String(bom.item_id) : '')
  const [makes, setMakes] = useState(bom ? String(num(bom.output_quantity)) : '1')
  const [notes, setNotes] = useState(bom?.notes ?? '')
  const [lines, setLines] = useState(bom?.lines.map((l, i) => ({ key: i + 1, item_id: String(l.item_id), quantity: String(num(l.quantity)) })) ?? [{ key: 1, item_id: '', quantity: '' }])
  const [next, setNext] = useState((bom?.lines.length ?? 1) + 1)
  const update = (key: number, patch: Partial<(typeof lines)[number]>) => setLines((ls) => ls.map((l) => (l.key === key ? { ...l, ...patch } : l)))
  const save = useSave(() => call('InventoryService', 'saveBom', [org.id, { item_id: Number(item), output_quantity: Number(makes), notes: notes.trim() || null, lines: lines.map((l) => ({ item_id: Number(l.item_id), quantity: Number(l.quantity) })) }]), { success: 'Saved', refresh: STOCK_REFRESH, onDone: onClose })
  const remove = useSave(() => call('InventoryService', 'deleteBom', [org.id, bom?.id]), { success: 'Deleted', refresh: STOCK_REFRESH, onDone: onClose })
  const chosen = list.data?.find((i) => String(i.id) === item)
  return (
    <Modal wide open onClose={onClose} title={bom ? `Parts of ${bom.name}` : pro ? 'New bill of materials' : 'New list of parts'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save" pending={save.isPending} onCancel={onClose} disabled={!item || !(Number(makes) > 0) || lines.some((l) => !l.item_id || !(Number(l.quantity) > 0))}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label="Item you make" placeholder="Select item" value={item} onChange={setItem} options={(list.data ?? []).map((i) => ({ value: String(i.id), label: `${i.sku} · ${i.name}` }))} />
          <Text label={`These parts make${chosen ? ` (${chosen.unit_of_measure})` : ''}`} inputMode="decimal" value={makes} onChange={setMakes} />
        </div>
        <div className="flex flex-col gap-1.5">
          <div className="grid grid-cols-[minmax(0,1fr)_88px_24px] gap-1.5 text-[12px] text-muted-foreground"><span>Part</span><span className="text-right">Qty</span><span /></div>
          {lines.map((l) => (
            <div key={l.key} className="grid grid-cols-[minmax(0,1fr)_88px_24px] gap-1.5 items-center">
              <select aria-label="Part" value={l.item_id} onChange={(e) => update(l.key, { item_id: e.target.value })} className={selectClass}>
                <option value="">Select part</option>
                {(list.data ?? []).filter((i) => String(i.id) !== item).map((i) => <option key={i.id} value={String(i.id)}>{i.sku} · {i.name} ({i.unit_of_measure})</option>)}
              </select>
              <Input aria-label="Quantity" inputMode="decimal" value={l.quantity} onChange={(e) => update(l.key, { quantity: e.target.value })} className="h-8 text-right fig" />
              <button type="button" aria-label="Remove part" disabled={lines.length < 2} onClick={() => setLines((ls) => ls.filter((x) => x.key !== l.key))} className="grid place-items-center text-muted-foreground cursor-pointer disabled:opacity-30"><X className="size-3.5" /></button>
            </div>
          ))}
          <div><button type="button" onClick={() => { setLines((ls) => [...ls, { key: next, item_id: '', quantity: '' }]); setNext((k) => k + 1) }} className="inline-flex items-center gap-1 text-[13px] font-medium cursor-pointer"><Plus className="size-3.5" />Add part</button></div>
        </div>
        <Text label="Notes" value={notes} onChange={setNotes} />
        {bom ? <ConfirmDelete label="Delete this list" pending={remove.isPending} onConfirm={() => remove.mutate()} /> : null}
      </FormBody>
    </Modal>
  )
}

function BuildForm({ boms, initial, onClose }: { boms: Bom[]; initial: Bom | null; onClose: () => void }) {
  const { org, canSeeBooks } = useApp()
  const warehouses = useQuery(warehousesQuery(org.id))
  const stock = useQuery(items(org.id))
  const chart = useQuery({ ...accounts(org.id), enabled: canSeeBooks })
  const openWarehouses = (warehouses.data ?? []).filter((w) => w.is_active)
  const [id, setId] = useState(initial ? String(initial.id) : '')
  const [quantity, setQuantity] = useState('1')
  const [warehouse, setWarehouse] = useState('')
  const [date, setDate] = useState(today())
  const [extra, setExtra] = useState('')
  const [account, setAccount] = useState('')
  const [lot, setLot] = useState('')
  const [expiry, setExpiry] = useState('')
  const [serials, setSerials] = useState('')
  const bom = boms.find((b) => String(b.id) === id)
  const output = stock.data?.find((i) => String(i.id) === String(bom?.item_id))
  const made = Number(quantity) || 0
  const parts = (bom?.lines ?? []).map((l) => ({ ...l, needed: (num(l.quantity) * made) / num(bom?.output_quantity) }))
  const short = parts.some((p) => p.needed > num(p.on_hand) + 1e-9)
  const estimate = parts.reduce((t, p) => t + p.needed * num(p.cost), 0) + (Number(extra) || 0)
  const save = useSave(() => call<{ number: string }>('InventoryService', 'buildAssembly', [org.id, { item_id: Number(bom?.item_id), quantity: made, warehouse_id: warehouse ? Number(warehouse) : null, date, extra_cost: Number(extra) || 0, extra_account_id: account ? Number(account) : null, lot_number: lot.trim() || null, expiry_date: expiry || null, serial_numbers: serials.trim() ? serials : null }]), { success: 'Built. Stock and your books are updated.', refresh: STOCK_REFRESH, onDone: () => { refreshBooks(); onClose() } })
  return (
    <Modal wide open onClose={onClose} title={bom ? `Build ${bom.name}` : 'Build'}>
      <FormBody onSubmit={() => save.mutate()} submit={`Build for ${figure(estimate, org.decimals)}`} pending={save.isPending} onCancel={onClose} disabled={!bom || !(made > 0) || short || (Number(extra) > 0 && !account)}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label="What to build" placeholder="Select item" value={id} onChange={setId} options={boms.map((b) => ({ value: String(b.id), label: `${b.sku} · ${b.name}` }))} />
          <Text label="How many" inputMode="decimal" value={quantity} onChange={setQuantity} />
          <Text label="Date" type="date" value={date} onChange={setDate} />
          {openWarehouses.length > 1 ? <Choice label="Warehouse" placeholder="Default warehouse" value={warehouse} onChange={setWarehouse} options={openWarehouses.map((w) => ({ value: String(w.id), label: w.name }))} /> : null}
          {output?.track_lots ? <Text label="Batch number" value={lot} onChange={setLot} /> : null}
          {output?.track_lots ? <Text label="Expiry date" type="date" value={expiry} onChange={setExpiry} /> : null}
          {output?.track_serials ? <Text label="Serial numbers" hint="Separate with commas. Leave blank and they're created for you." value={serials} onChange={setSerials} /> : null}
        </div>
        {parts.length ? (
          <div className="border border-border rounded-[8px] overflow-x-auto">
            <table className="w-full text-[13px] min-w-[440px]">
              <thead><tr><Head>Part</Head><Head right>Needed</Head><Head right>On hand</Head></tr></thead>
              <tbody>{parts.map((p) => <tr key={p.id}><Cell><span className="fig text-[12.5px] text-muted-foreground mr-1.5">{p.sku}</span>{p.name}</Cell><Cell right>{figure(p.needed, 2)} {p.unit_of_measure}</Cell><Cell right className={p.needed > num(p.on_hand) + 1e-9 ? 'text-destructive' : undefined}>{figure(num(p.on_hand), 2)}</Cell></tr>)}</tbody>
            </table>
          </div>
        ) : null}
        {canSeeBooks ? (
          <div className="grid sm:grid-cols-2 gap-3">
            <Text label="Extra cost" hint="Labour or other costs added to the finished item." inputMode="decimal" value={extra} onChange={setExtra} />
            {Number(extra) > 0 ? <Choice label="Comes from" placeholder="Select account" value={account} onChange={setAccount} options={(chart.data ?? []).filter((a) => a.is_postable !== false).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))} /> : null}
          </div>
        ) : null}
        <p className="text-[12.5px] text-muted-foreground">The cost shown is an estimate from today's costs. The exact figure comes from your costing method when it's built.</p>
      </FormBody>
    </Modal>
  )
}

function UndoBuild({ build: b, onClose }: { build: Build; onClose: () => void }) {
  const { org } = useApp()
  const [date, setDate] = useState(today())
  const save = useSave(() => call('InventoryService', 'reverseAssembly', [org.id, b.id, { date }]), { success: 'Build undone', refresh: STOCK_REFRESH, onDone: () => { refreshBooks(); onClose() } })
  return (
    <Modal open onClose={onClose} title={`Undo ${b.number}`}>
      <FormBody onSubmit={() => save.mutate()} submit="Undo build" pending={save.isPending} onCancel={onClose}>
        <p className="text-[13.5px]">Takes {figure(num(b.quantity), 0)} {b.name} out of stock, puts its parts back at the cost they left at, and adds an opposite entry to your books.</p>
        <Text label="Date" type="date" value={date} onChange={setDate} />
      </FormBody>
    </Modal>
  )
}
