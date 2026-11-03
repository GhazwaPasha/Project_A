import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from '@tanstack/react-router'
import { ArrowLeft, Plus } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Badge, Chip, type Tone } from '@/components/chips'
import { Choice, FormBody, Modal, Stat, Stats, Text, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, Table, Tabs, Toolbar, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { num, q, refreshBooks, today, type Id } from '@/lib/data'
import { cn } from '@/lib/utils'
import { INVENTORY_TABS, STOCK_REFRESH, categories, useCanWriteStock, warehousesQuery } from '@/routes/inventory'

type Row = { id: Id; number: string; status: string; count_date: string; warehouse_name: string; lines: number; counted: number; differences: number }
type Line = { id: Id; item_id: Id; expected: number; counted: number | null; item_name: string; sku: string; barcode: string | null; unit_of_measure: string; average_unit_cost: number; current: number }
type Count = { id: Id; number: string; status: string; count_date: string; warehouse_name: string; notes: string | null; lines: Line[] }
const STATUS: Record<string, { label: string; tone: Tone }> = { open: { label: 'In progress', tone: 'warn' }, posted: { label: 'Finished', tone: 'good' }, cancelled: { label: 'Cancelled', tone: 'neutral' } }

export function Counts() {
  const { org, pro } = useApp()
  const canWrite = useCanWriteStock()
  const list = useQuery(q<Row[]>(['stock', org.id, 'counts'], 'InventoryService', 'listStockCounts', [org.id]))
  const [starting, setStarting] = useState(false)
  return (
    <Screen
      title="Inventory"
      sub={pro ? 'Physical counts, with variances posted to the ledger.' : 'Count what is really on the shelf, and correct the difference.'}
      actions={canWrite ? <button className={btn.primary} onClick={() => setStarting(true)}><Plus className="size-3.5 mr-1.5" />New count</button> : undefined}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No counts yet" body="Start a count for a warehouse, or one category at a time." /> : null)}>
        {(rows) => (
          <Paged rows={rows}>
            {(page, pager) => (
              <Table min={620} footer={pager}>
                <thead><tr><Head>Number</Head><Head>Warehouse</Head><Head>Status</Head><Head>Date</Head><Head right>Counted</Head><Head right>Differences</Head></tr></thead>
                <tbody>
                  {page.map((c) => (
                    <tr key={c.id} className="hover:bg-accent/50">
                      <Cell className="fig text-[12.5px]"><Link to="/inventory/counts/$countId" params={{ countId: String(c.id) }} className="underline underline-offset-[3px]">{c.number}</Link></Cell>
                      <Cell className="max-w-0 w-full truncate">{c.warehouse_name}</Cell>
                      <Cell><Badge dot tone={STATUS[c.status]?.tone}>{STATUS[c.status]?.label ?? c.status}</Badge></Cell>
                      <Cell className="text-muted-foreground">{shortDate(c.count_date)}</Cell>
                      <Cell right>{figure(num(c.counted), 0)} of {figure(num(c.lines), 0)}</Cell>
                      <Cell right>{figure(num(c.differences), 0)}</Cell>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {starting ? <NewCount onClose={() => setStarting(false)} /> : null}
    </Screen>
  )
}

function NewCount({ onClose }: { onClose: () => void }) {
  const { org } = useApp()
  const navigate = useNavigate()
  const warehouses = useQuery(warehousesQuery(org.id))
  const cats = useQuery(categories(org.id))
  const [warehouse, setWarehouse] = useState('')
  const [category, setCategory] = useState('')
  const [date, setDate] = useState(today())
  const save = useSave(() => call<{ id: Id }>('InventoryService', 'createStockCount', [org.id, { warehouse_id: warehouse ? Number(warehouse) : null, category_id: category ? Number(category) : null, count_date: date }]), { success: 'Count started', refresh: STOCK_REFRESH, onDone: (r) => navigate({ to: '/inventory/counts/$countId', params: { countId: String(r.id) } }) })
  return (
    <Modal open onClose={onClose} title="New stock count">
      <FormBody onSubmit={() => save.mutate()} submit="Start count" pending={save.isPending} onCancel={onClose}>
        <Choice label="Warehouse" placeholder="Default warehouse" value={warehouse} onChange={setWarehouse} options={(warehouses.data ?? []).filter((w) => w.is_active).map((w) => ({ value: String(w.id), label: w.name }))} />
        <Choice label="Category" hint="Counting one category at a time is easier than everything at once." placeholder="All categories" value={category} onChange={setCategory} options={(cats.data ?? []).map((c) => ({ value: String(c.id), label: c.name }))} />
        <Text label="Date" type="date" value={date} onChange={setDate} />
      </FormBody>
    </Modal>
  )
}

export function CountPage() {
  const { countId } = useParams({ strict: false }) as { countId: string }
  const { org, pro, canSeeBooks } = useApp()
  const canWrite = useCanWriteStock()
  const id = Number(countId)
  const query = useQuery(q<Count>(['stock', org.id, 'count', id], 'InventoryService', 'getStockCount', [org.id, id]))
  const [typed, setTyped] = useState<Record<string, string>>({})
  const [search, setSearch] = useState('')
  const [onlyDifferent, setOnlyDifferent] = useState(false)
  const c = query.data
  const open = c?.status === 'open' && canWrite
  const valueOf = (l: Line) => {
    const raw = typed[String(l.id)]
    if (raw !== undefined) return raw === '' ? null : Number(raw)
    return l.counted === null ? null : num(l.counted)
  }
  const lines = useMemo(() => c?.lines ?? [], [c])
  const counted = lines.filter((l) => valueOf(l) !== null)
  const differ = (l: Line) => { const v = valueOf(l); return v !== null && Number.isFinite(v) && v !== num(l.current) }
  const different = lines.filter(differ)
  const worth = different.reduce((t, l) => t + ((valueOf(l) as number) - num(l.current)) * num(l.average_unit_cost), 0)
  const s = search.trim().toLowerCase()
  const shown = lines.filter((l) => (!onlyDifferent || differ(l)) && (!s || `${l.sku} ${l.barcode ?? ''} ${l.item_name}`.toLowerCase().includes(s)))
  const changes = () => Object.keys(typed).map((k) => ({ line_id: Number(k), counted: typed[k] === '' ? null : Number(typed[k]) }))
  const save = useSave(() => call('InventoryService', 'saveStockCountLines', [org.id, id, changes()]), { success: 'Saved', refresh: STOCK_REFRESH, onDone: () => setTyped({}) })
  const post = useSave(async () => {
    if (Object.keys(typed).length) await call('InventoryService', 'saveStockCountLines', [org.id, id, changes()])
    return call('InventoryService', 'postStockCount', [org.id, id])
  }, { success: 'Finished. Stock and your books are corrected.', refresh: STOCK_REFRESH, onDone: () => { setTyped({}); refreshBooks() } })
  const cancel = useSave(() => call('InventoryService', 'cancelStockCount', [org.id, id]), { success: 'Count cancelled', refresh: STOCK_REFRESH })
  return (
    <Screen
      title={c ? `Count ${c.number}` : 'Stock count'}
      sub={c ? `${c.warehouse_name}, ${shortDate(c.count_date)}` : undefined}
      search={<SearchIcon label="Search count" placeholder="SKU, barcode or name" value={search} onChange={setSearch} />}
      actions={<>
        <Link to="/inventory/counts" className={btn.plain}><ArrowLeft className="size-3.5 mr-1.5" />All counts</Link>
        {open ? <button className={btn.plain} disabled={cancel.isPending} onClick={() => cancel.mutate()}>Cancel count</button> : null}
        {open ? <button className={btn.plain} disabled={!Object.keys(typed).length || save.isPending} onClick={() => save.mutate()}>Save progress</button> : null}
        {open && canSeeBooks ? <button className={btn.primary} disabled={!counted.length || post.isPending} onClick={() => post.mutate()}>{post.isPending ? 'Finishing…' : pro ? 'Post variances' : 'Finish and correct stock'}</button> : null}
      </>}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Stats cols={3}>
        <Stat label="Counted" value={`${counted.length} of ${lines.length}`} />
        <Stat label="Differences" value={different.length} tone={different.length ? 'warn' : undefined} />
        <Stat label={pro ? 'Net variance' : 'Worth of differences'} value={`${org.currency} ${figure(worth, 0)}`} />
      </Stats>
      {open && !canSeeBooks ? <p className="text-[13px] text-muted-foreground">An accountant finishes the count, because correcting stock changes your books.</p> : null}
      <Toolbar>
        <Chip active={onlyDifferent} count={different.length} onClick={() => setOnlyDifferent((v) => !v)}>Differences only</Chip>
      </Toolbar>
      <Loaded query={query}>
        {() => shown.length === 0 ? <Empty title="Nothing to show" body="Try another word, or turn off the filter." /> : (
          <Paged rows={shown} size={50}>
            {(page, pager) => (
              <Table min={680} footer={pager}>
                <thead><tr><Head>SKU</Head><Head>Item</Head><Head right>Expected</Head><Head right>Counted</Head><Head right>Difference</Head><Head right>Value</Head></tr></thead>
                <tbody>
                  {page.map((l) => {
                    const v = valueOf(l)
                    const diff = v === null ? null : v - num(l.current)
                    return (
                      <tr key={l.id}>
                        <Cell className="fig text-[12.5px] text-muted-foreground">{l.sku}</Cell>
                        <Cell className="max-w-0 w-full truncate">{l.item_name}</Cell>
                        <Cell right>{figure(num(c?.status === 'open' ? l.current : l.expected), 0)} {l.unit_of_measure}</Cell>
                        <Cell right>{open ? <Input aria-label={`Counted ${l.item_name}`} inputMode="decimal" value={typed[String(l.id)] ?? (l.counted === null ? '' : String(num(l.counted)))} onChange={(e) => setTyped((t) => ({ ...t, [String(l.id)]: e.target.value }))} className="h-7 w-20 ml-auto text-right fig" /> : l.counted === null ? '' : figure(num(l.counted), 0)}</Cell>
                        <Cell right className={cn(diff ? 'text-destructive' : 'text-muted-foreground')}>{diff === null || !Number.isFinite(diff) ? '' : `${diff > 0 ? '+' : ''}${figure(diff, 0)}`}</Cell>
                        <Cell right>{diff ? figure(diff * num(l.average_unit_cost), org.decimals) : ''}</Cell>
                      </tr>
                    )
                  })}
                </tbody>
              </Table>
            )}
          </Paged>
        )}
      </Loaded>
    </Screen>
  )
}
