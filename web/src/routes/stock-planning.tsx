import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import { Input } from '@/components/ui/input'
import { AskChip } from '@/components/agent-panel'
import { Badge, Chip, Chips, type Tone } from '@/components/chips'
import { Choice, Stat, Stats, Toggle, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, Table, Tabs, Toolbar, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, num, q, type Id } from '@/lib/data'
import { INVENTORY_TABS, STOCK_REFRESH, useCanWriteStock } from '@/routes/inventory'
import { settingsQuery } from '@/routes/purchasing'
import { EXPIRY } from '@/routes/stock'

type PlanRow = { item_id: Id; sku: string; name: string; unit_of_measure: string; unit_cost: number; on_hand: number; on_order: number; used_90_days: number; lead_time_days: number; supplier_name: string | null; daily_usage: number; days_of_cover: number | null; suggested: number; stockout_risk: boolean }

/** What to order, worked out from what's actually being used. A person drafts and approves every order. */
export function Planner() {
  const { org, pro } = useApp()
  const canWrite = useCanWriteStock()
  const navigate = useNavigate()
  const plan = useQuery(q<PlanRow[]>(['stock', org.id, 'plan'], 'InventoryService', 'getReorderPlan', [org.id]))
  const [showAll, setShowAll] = useState(false)
  const [search, setSearch] = useState('')
  const [chosen, setChosen] = useState<Record<string, boolean>>({})
  const [amount, setAmount] = useState<Record<string, string>>({})
  const all = plan.data ?? []
  const needed = all.filter((p) => num(p.suggested) > 0)
  const s = search.trim().toLowerCase()
  const rows = (showAll ? all : needed).filter((p) => !s || `${p.sku} ${p.name} ${p.supplier_name ?? ''}`.toLowerCase().includes(s))
  const quantityOf = (p: PlanRow) => (amount[String(p.item_id)] !== undefined ? Number(amount[String(p.item_id)]) : num(p.suggested))
  const isChosen = (p: PlanRow) => chosen[String(p.item_id)] ?? num(p.suggested) > 0
  const picked = rows.filter((p) => isChosen(p) && quantityOf(p) > 0)
  const cost = picked.reduce((t, p) => t + quantityOf(p) * num(p.unit_cost), 0)
  const draft = useSave(() => call<{ orders: Id[] }>('InventoryService', 'createOrdersFromPlan', [org.id, { lines: picked.map((p) => ({ item_id: Number(p.item_id), quantity: quantityOf(p) })) }]), { success: 'Draft orders created. Nothing is sent or approved yet.', refresh: STOCK_REFRESH, onDone: () => navigate({ to: '/inventory/purchase-orders' }) })
  return (
    <Screen
      title="Inventory"
      sub={pro ? 'Reorder suggestions from 90-day usage, lead time and on-order quantities.' : 'What to order next, based on what you have been using.'}
      search={<SearchIcon label="Search planner" placeholder="SKU, name or supplier" value={search} onChange={setSearch} />}
      actions={canWrite ? <button className={btn.primary} disabled={!picked.length || draft.isPending} onClick={() => draft.mutate()}>Draft {picked.length || ''} order lines</button> : undefined}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Stats cols={3}>
        <Stat label="Need ordering" value={needed.length} tone={needed.length ? 'warn' : undefined} />
        <Stat label="Could run out first" value={needed.filter((p) => p.stockout_risk).length} tone={needed.some((p) => p.stockout_risk) ? 'warn' : undefined} />
        <Stat label="Selected would cost" value={`${org.currency} ${figure(cost, 0)}`} />
      </Stats>
      <Toolbar>
        <Chip active={showAll} count={all.length} onClick={() => setShowAll((v) => !v)}>Show all items</Chip>
        <span className="ml-auto"><AskChip prompt="Look at my reorder plan. What should I order first, and why?">What matters most?</AskChip></span>
      </Toolbar>
      <Loaded query={plan} empty={(d) => (d.length === 0 ? <Empty title="No items yet" body="Add items and the planner starts working as stock moves." /> : null)}>
        {() => rows.length === 0 ? <Empty title={showAll ? 'No matches' : 'Nothing needs ordering'} body={showAll ? 'Try another word.' : 'Everything has enough stock for its delivery time.'} /> : (
          <Paged rows={rows}>
            {(page, pager) => (
              <Table min={980} footer={pager}>
                <thead><tr>{canWrite ? <Head /> : null}<Head>SKU</Head><Head>Item</Head><Head>Supplier</Head><Head right>On hand</Head><Head right>On order</Head><Head right>Used a day</Head><Head right>Lasts</Head><Head right>Delivery</Head><Head right>Order</Head></tr></thead>
                <tbody>
                  {page.map((p) => (
                    <tr key={p.item_id}>
                      {canWrite ? <Cell><input type="checkbox" aria-label={`Order ${p.name}`} checked={isChosen(p)} onChange={(e) => setChosen((c) => ({ ...c, [String(p.item_id)]: e.target.checked }))} className="size-3.5 cursor-pointer accent-[var(--primary)]" /></Cell> : null}
                      <Cell className="fig text-[12.5px] text-muted-foreground">{p.sku}</Cell>
                      <Cell><span className="flex items-center gap-2"><Link to="/inventory/items/$itemId" params={{ itemId: String(p.item_id) }} className="hover:underline underline-offset-[3px]">{p.name}</Link>{p.stockout_risk ? <Badge dot tone="bad">May run out</Badge> : null}</span></Cell>
                      <Cell className="text-muted-foreground">{p.supplier_name ?? 'Not set'}</Cell>
                      <Cell right>{figure(num(p.on_hand), 0)}</Cell>
                      <Cell right>{figure(num(p.on_order), 0)}</Cell>
                      <Cell right>{figure(num(p.daily_usage), 1)}</Cell>
                      <Cell right>{p.days_of_cover === null ? 'No use yet' : `${p.days_of_cover} days`}</Cell>
                      <Cell right>{p.lead_time_days} days</Cell>
                      <Cell right>{canWrite ? <Input aria-label={`Quantity of ${p.name}`} inputMode="decimal" value={amount[String(p.item_id)] ?? String(num(p.suggested))} onChange={(e) => setAmount((a) => ({ ...a, [String(p.item_id)]: e.target.value }))} className="h-7 w-20 ml-auto text-right fig" /> : figure(num(p.suggested), 0)}</Cell>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Paged>
        )}
      </Loaded>
    </Screen>
  )
}

type Analysis = {
  total_value: number; usage_12_months: number; turnover: number | null
  by_category: { category_name: string; value: number; items: number }[]
  slow_moving: { item_id: Id; sku: string; name: string; on_hand: number; unit_of_measure: string; value: number; last_used: string | null; days_idle: number | null }[]
  abc: { item_id: Id; sku: string; name: string; usage_value: number; share: number; class: 'A' | 'B' | 'C' }[]
  expiring: { id: Id; lot_number: string; expiry_date: string; quantity: number; item_name: string; item_id: Id; warehouse_name: string; value: number; status: 'expired' | 'soon' | 'ok' }[]
}
type BooksCheck = { agrees: boolean; rows: { account_id: Id; code: string; name: string; stock_value: number; book_value: number; difference: number }[] }
const ABC_TONE: Record<string, Tone> = { A: 'good', B: 'warn', C: 'neutral' }

export function StockReports() {
  const { org, pro, canSeeBooks } = useApp()
  const report = useQuery(q<Analysis>(['stock', org.id, 'analysis'], 'InventoryService', 'getAnalysis', [org.id]))
  const check = useQuery({ ...q<BooksCheck>(['stock', org.id, 'books-check'], 'InventoryService', 'getBooksCheck', [org.id]), enabled: canSeeBooks })
  const [view, setView] = useState('value')
  const r = report.data
  const views = [
    { id: 'value', label: pro ? 'Value by category' : 'Where the money is' },
    { id: 'abc', label: pro ? 'ABC analysis' : 'What matters most' },
    { id: 'slow', label: pro ? 'Slow moving' : 'Not moving', count: r?.slow_moving.length },
    { id: 'expiring', label: 'Expiring', count: r?.expiring.length },
    ...(canSeeBooks ? [{ id: 'books', label: pro ? 'Reconciliation' : 'Against your books' }] : []),
  ]
  return (
    <Screen title="Inventory" sub={pro ? 'Valuation, turnover and exceptions.' : 'What your stock is worth, and what deserves a look.'} tabs={<Tabs items={INVENTORY_TABS} />}>
      <Stats cols={3}>
        <Stat label={pro ? 'Inventory value' : 'Worth today'} value={`${org.currency} ${figure(num(r?.total_value), 0)}`} />
        <Stat label={pro ? 'Issued, 12 months' : 'Used in 12 months'} value={`${org.currency} ${figure(num(r?.usage_12_months), 0)}`} />
        <Stat label={pro ? 'Turnover' : 'Times stock turned over'} value={r?.turnover == null ? 'Not enough data' : `${figure(r.turnover, 1)} times`} />
      </Stats>
      <Toolbar>
        <Chips label="Report" value={view} onChange={setView} options={views} />
        <span className="ml-auto"><AskChip prompt="Look at my stock reports. Where is money tied up, and what should I do about it?">Where is money stuck?</AskChip></span>
      </Toolbar>
      <Loaded query={report}>
        {(a) => {
          if (view === 'value') return (
            <Table min={460}>
              <thead><tr><Head>Category</Head><Head right>Items</Head><Head right>Value</Head><Head right>Share</Head></tr></thead>
              <tbody>{a.by_category.map((c) => <tr key={c.category_name}><Cell>{c.category_name}</Cell><Cell right>{c.items}</Cell><Cell right>{figure(num(c.value), org.decimals)}</Cell><Cell right>{num(a.total_value) ? `${figure((num(c.value) / num(a.total_value)) * 100, 1)}%` : ''}</Cell></tr>)}</tbody>
            </Table>
          )
          if (view === 'abc') return (
            <Paged rows={a.abc}>
              {(page, pager) => (
                <Table min={560} footer={pager}>
                  <thead><tr><Head>Class</Head><Head>SKU</Head><Head>Item</Head><Head right>Used, 12 months</Head><Head right>Share</Head></tr></thead>
                  <tbody>{page.map((i) => <tr key={i.item_id}><Cell><Badge tone={ABC_TONE[i.class]}>{i.class}</Badge></Cell><Cell className="fig text-[12.5px] text-muted-foreground">{i.sku}</Cell><Cell className="max-w-0 w-full truncate"><ItemLink id={i.item_id} name={i.name} /></Cell><Cell right>{figure(num(i.usage_value), org.decimals)}</Cell><Cell right>{figure(num(i.share), 1)}%</Cell></tr>)}</tbody>
                </Table>
              )}
            </Paged>
          )
          if (view === 'slow') return a.slow_moving.length === 0 ? <Empty title="Everything is moving" body="Items with stock that hasn't been used for 90 days appear here." /> : (
            <Paged rows={a.slow_moving}>
              {(page, pager) => (
                <Table min={620} footer={pager}>
                  <thead><tr><Head>SKU</Head><Head>Item</Head><Head>Last used</Head><Head right>Idle</Head><Head right>On hand</Head><Head right>Value</Head></tr></thead>
                  <tbody>{page.map((i) => <tr key={i.item_id}><Cell className="fig text-[12.5px] text-muted-foreground">{i.sku}</Cell><Cell className="max-w-0 w-full truncate"><ItemLink id={i.item_id} name={i.name} /></Cell><Cell className="text-muted-foreground">{i.last_used ? shortDate(i.last_used) : 'Never'}</Cell><Cell right>{i.days_idle === null ? '' : `${i.days_idle} days`}</Cell><Cell right>{figure(num(i.on_hand), 0)} {i.unit_of_measure}</Cell><Cell right>{figure(num(i.value), org.decimals)}</Cell></tr>)}</tbody>
                </Table>
              )}
            </Paged>
          )
          if (view === 'expiring') return a.expiring.length === 0 ? <Empty title="Nothing expiring soon" body="Batches expiring within 90 days appear here. Turn on batch tracking for an item to use this." /> : (
            <Table min={640}>
              <thead><tr><Head>Item</Head><Head>Batch</Head><Head>Warehouse</Head><Head>Expiry</Head><Head right>Quantity</Head><Head right>Value</Head></tr></thead>
              <tbody>{a.expiring.map((l) => <tr key={l.id}><Cell><ItemLink id={l.item_id} name={l.item_name} /></Cell><Cell className="fig text-[12.5px]">{l.lot_number}</Cell><Cell className="text-muted-foreground">{l.warehouse_name}</Cell><Cell><span className="flex items-center gap-2">{shortDate(l.expiry_date)}{l.status !== 'ok' ? <Badge dot tone={EXPIRY[l.status].tone}>{EXPIRY[l.status].label}</Badge> : null}</span></Cell><Cell right>{figure(num(l.quantity), 0)}</Cell><Cell right>{figure(num(l.value), org.decimals)}</Cell></tr>)}</tbody>
            </Table>
          )
          return (
            <div className="flex flex-col gap-3.5">
              <Loaded query={check}>
                {(c) => (
                  <>
                    <p className="text-[13.5px] flex items-center gap-2">{c.agrees ? <Badge dot tone="good">Agrees</Badge> : <Badge dot tone="bad">Doesn't agree</Badge>}{c.agrees ? 'Your stock value matches your books.' : 'Stock and your books differ. Check for movements that have not been posted, or entries made directly to these accounts.'}</p>
                    <Table min={560}>
                      <thead><tr><Head>Account</Head><Head right>Stock says</Head><Head right>Books say</Head><Head right>Difference</Head></tr></thead>
                      <tbody>{c.rows.map((x) => <tr key={x.account_id}><Cell><span className="fig text-muted-foreground mr-1.5">{x.code}</span>{x.name}</Cell><Cell right>{figure(num(x.stock_value), org.decimals)}</Cell><Cell right>{figure(num(x.book_value), org.decimals)}</Cell><Cell right>{figure(num(x.difference), org.decimals)}</Cell></tr>)}</tbody>
                    </Table>
                  </>
                )}
              </Loaded>
              <GrniSetting />
            </div>
          )
        }}
      </Loaded>
    </Screen>
  )
}

const ItemLink = ({ id, name }: { id: Id; name: string }) => <Link to="/inventory/items/$itemId" params={{ itemId: String(id) }} className="hover:underline underline-offset-[3px]">{name}</Link>

/** Goods that have arrived before their bill wait in this account. */
function GrniSetting() {
  const { org, pro } = useApp()
  const settings = useQuery(settingsQuery(org.id))
  const chart = useQuery(accounts(org.id))
  const [picked, setPicked] = useState<string | null>(null)
  const value = picked ?? (settings.data?.grni_account_id ? String(settings.data.grni_account_id) : '')
  const save = useSave(() => call('InventoryService', 'saveSettings', [org.id, { grni_account_id: value ? Number(value) : null }]), { success: 'Saved', refresh: STOCK_REFRESH, onDone: () => setPicked(null) })
  const create = useSave(() => call('InventoryService', 'createGrniAccount', [org.id]), { success: 'Account created', refresh: [...STOCK_REFRESH, 'accounts'] })
  const options = (chart.data ?? []).filter((a) => a.is_postable !== false && a.account_type === 'liability').map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))
  return (
    <section className="sheet p-3 flex flex-col gap-2.5 max-w-[560px]" aria-label="Receiving account">
      <Choice label={pro ? 'Goods received, not invoiced (GRNI)' : 'Where goods wait for their bill'} hint="Goods received from a purchase order are owed here until the supplier's bill is posted." placeholder="Select account" value={value} onChange={setPicked} options={options} />
      <div className="flex flex-wrap gap-2">
        <button className={btn.plain} disabled={picked === null || save.isPending} onClick={() => save.mutate()}>Save</button>
        {!settings.data?.grni_account_id ? <button className={btn.plain} disabled={create.isPending} onClick={() => create.mutate()}>Create one for me</button> : null}
      </div>
      <CostingSetting current={settings.data?.default_costing_method ?? 'average'} />
    </section>
  )
}

function CostingSetting({ current }: { current: 'average' | 'fifo' }) {
  const { org } = useApp()
  const [picked, setPicked] = useState<string | null>(null)
  const [all, setAll] = useState(false)
  const value = picked ?? current
  const save = useSave(() => call('InventoryService', 'setDefaultCosting', [org.id, { method: value, apply_to_all: all }]), { success: 'Saved', refresh: STOCK_REFRESH, onDone: () => { setPicked(null); setAll(false) } })
  return (
    <div className="flex flex-col gap-2.5 border-t border-border pt-2.5">
      <Choice label="Costing method for new items" hint="Each item can also have its own, on its edit form." value={value} onChange={setPicked} options={[{ value: 'average', label: 'Moving average' }, { value: 'fifo', label: 'First in, first out' }]} />
      <Toggle label="Switch every existing item now" hint="Today's stock value stays the same. Only later issues are costed differently." checked={all} onChange={setAll} />
      <div><button className={btn.plain} disabled={(value === current && !all) || save.isPending} onClick={() => save.mutate()}>Save</button></div>
    </div>
  )
}
