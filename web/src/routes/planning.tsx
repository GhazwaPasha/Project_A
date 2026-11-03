import { useEffect, useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { AskChip } from '@/components/agent-panel'
import { Badge, Chips } from '@/components/chips'
import { Choice, ConfirmDelete, FormBody, Modal, Stat, Stats, Text, useSave } from '@/components/form'
import { Cell, Check, Empty, Head, Loaded, Screen, Table, Toolbar, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, iso, num, periodRange, q, refreshBooks, today, type Account, type Id } from '@/lib/data'
import { Trend } from '@/routes/home'
import { ratesQuery } from '@/routes/documents'
import { cn } from '@/lib/utils'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

// ---- Budgets ----

type Budget = { id: Id; name: string; year: number; total: number }
type BudgetAccount = { account_id: number; code: string; name: string; account_type: string; budget: number[]; actual: number[]; budget_total: number; actual_total: number; variance: number }
type Report = { id: Id; name: string; year: number; accounts: BudgetAccount[]; revenue: { budget: number; actual: number }; expense: { budget: number; actual: number } }

export function Budgets() {
  const { org, pro } = useApp()
  const list = useQuery(q<Budget[]>(['budgets', org.id], 'BooksService', 'listBudgets', [org.id]))
  const [picked, setPicked] = useState<string>('')
  const id = picked || (list.data?.[0] ? String(list.data[0].id) : '')
  const report = useQuery({ ...q<Report>(['budgets', org.id, id], 'BooksService', 'getBudgetReport', [org.id, Number(id)]), enabled: !!id })
  const [editing, setEditing] = useState<Report | 'new' | null>(null)
  const d = org.decimals
  const pct = (a: number, b: number) => (b ? `${Math.round((a / b) * 100)}%` : '')
  return (
    <Screen title="Budgets" sub={pro ? 'Budget against actual, by account.' : "What you planned to earn and spend, and how it's going."} actions={<>
      {report.data ? <button className={btn.plain} onClick={() => setEditing(report.data)}>Edit</button> : null}
      <button className={btn.primary} onClick={() => setEditing('new')}><Plus className="size-3.5 mr-1.5" />New budget</button>
    </>}>
      <Loaded query={list} empty={(b) => (b.length === 0 ? <Empty title="No budgets yet" body="Set a monthly plan for your income and costs, then see how each month compares." /> : null)}>
        {(rows) => <>
          <Toolbar>
            <Chips label="Budget" value={id} onChange={setPicked} options={rows.map((b) => ({ id: String(b.id), label: `${b.name} ${b.year}` }))} />
            <span className="ml-auto"><AskChip prompt="How am I doing against my budget? What stands out, and what should I do about it?">How am I doing against budget?</AskChip></span>
          </Toolbar>
          {report.data ? <>
            <Stats>
              <Stat label={pro ? 'Revenue budget' : 'Planned to earn'} value={figure(report.data.revenue.budget, 0)} />
              <Stat label={pro ? 'Revenue actual' : 'Earned so far'} value={figure(report.data.revenue.actual, 0)} />
              <Stat label={pro ? 'Expense budget' : 'Planned to spend'} value={figure(report.data.expense.budget, 0)} />
              <Stat label={pro ? 'Expense actual' : 'Spent so far'} value={figure(report.data.expense.actual, 0)} tone={report.data.expense.actual > report.data.expense.budget && report.data.expense.budget > 0 ? 'warn' : undefined} />
            </Stats>
            <Table min={620}>
              <thead><tr><Head>Account</Head><Head right>Budget</Head><Head right>Actual</Head><Head right>Variance</Head><Head right>Used</Head></tr></thead>
              <tbody>
                {report.data.accounts.map((a) => {
                  const bad = a.account_type === 'revenue' ? a.variance < 0 : a.variance > 0
                  return (
                    <tr key={a.account_id}>
                      <Cell>{pro ? <span className="fig text-[12.5px] text-muted-foreground mr-2">{a.code}</span> : null}{a.name}</Cell>
                      <Cell right>{figure(a.budget_total, d)}</Cell>
                      <Cell right>{figure(a.actual_total, d)}</Cell>
                      <Cell right className={a.budget_total && bad ? 'text-[var(--note)]' : undefined}>{figure(a.variance, d)}</Cell>
                      <Cell right>{pct(a.actual_total, a.budget_total)}</Cell>
                    </tr>
                  )
                })}
              </tbody>
            </Table>
          </> : null}
        </>}
      </Loaded>
      {editing ? <BudgetForm report={editing === 'new' ? null : editing} onClose={() => setEditing(null)} onSaved={(saved) => { setPicked(String(saved)); setEditing(null) }} /> : null}
    </Screen>
  )
}

function BudgetForm({ report, onClose, onSaved }: { report: Report | null; onClose: () => void; onSaved: (id: Id) => void }) {
  const { org } = useApp()
  const chart = useQuery(accounts(org.id))
  const [name, setName] = useState(report?.name ?? 'Budget')
  const [year, setYear] = useState(String(report?.year ?? new Date().getFullYear()))
  const [cells, setCells] = useState<Record<string, string>>(() => {
    const out: Record<string, string> = {}
    report?.accounts.forEach((a) => a.budget.forEach((v, m) => { if (v) out[`${a.account_id}:${m + 1}`] = String(v) }))
    return out
  })
  const rows: Account[] = (chart.data ?? []).filter((a) => a.is_postable !== false && (a.account_type === 'revenue' || a.account_type === 'expense')).sort((a, b) => (a.account_type === b.account_type ? a.code.localeCompare(b.code) : a.account_type === 'revenue' ? -1 : 1))
  const set = (acct: Id, month: number, v: string) => setCells((c) => ({ ...c, [`${acct}:${month}`]: v }))
  const fill = (acct: Id, v: string) => setCells((c) => { const n = { ...c }; for (let m = 1; m <= 12; m++) n[`${acct}:${m}`] = v; return n })
  const save = useSave(() => call<{ id: Id }>('BooksService', 'saveBudget', [org.id, {
    id: report?.id, name: name.trim(), year: Number(year),
    lines: Object.entries(cells).filter(([, v]) => Number(v) > 0).map(([k, v]) => { const [account_id, month] = k.split(':').map(Number); return { account_id, month, amount: Number(v) } }),
  }]), { success: 'Budget saved', refresh: ['budgets'], onDone: (r) => onSaved(r.id) })
  const remove = useSave(() => call('BooksService', 'deleteBudget', [org.id, report?.id]), { success: 'Budget deleted', refresh: ['budgets'], onDone: onClose })
  return (
    <Modal wide open onClose={onClose} title={report ? 'Edit budget' : 'New budget'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save budget" pending={save.isPending} onCancel={onClose} disabled={!name.trim() || !year}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Name" required value={name} onChange={setName} />
          <Text label="Year" hint="Calendar months, January to December." inputMode="numeric" value={year} onChange={setYear} />
        </div>
        {rows.length === 0 ? <p className="text-[13px] text-muted-foreground">Add income and expense accounts first.</p> : (
          <div className="border border-border rounded-[8px] overflow-auto max-h-[52dvh]">
            <table className="text-[13px] border-separate border-spacing-0">
              <thead className="sticky top-0 z-[1]"><tr><Head>Account</Head><Head right>Every month</Head>{MONTHS.map((m) => <Head key={m} right>{m}</Head>)}</tr></thead>
              <tbody>
                {rows.map((a) => (
                  <tr key={a.id}>
                    <Cell className="whitespace-nowrap"><span className="fig text-[12px] text-muted-foreground mr-1.5">{a.code}</span>{a.name}</Cell>
                    <Cell><Input aria-label={`Every month for ${a.name}`} inputMode="decimal" onChange={(e) => fill(a.id, e.target.value)} className="h-7 w-20 text-right fig" /></Cell>
                    {MONTHS.map((m, i) => <Cell key={m}><Input aria-label={`${m} for ${a.name}`} inputMode="decimal" value={cells[`${a.id}:${i + 1}`] ?? ''} onChange={(e) => set(a.id, i + 1, e.target.value)} className="h-7 w-20 text-right fig" /></Cell>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {report ? <ConfirmDelete label="Delete this budget" pending={remove.isPending} onConfirm={() => remove.mutate()} /> : null}
      </FormBody>
    </Modal>
  )
}

// ---- Forecast ----

type Forecast = { months_of_history: number; confidence: string; cash_today: number; history: { month: string; revenue: number; expenses: number }[]; rows: { month: string; revenue: number; expenses: number; net: number; receivable_due: number; payable_due: number; cash: number }[] }
const monthName = (m: string) => new Date(`${m}-01T00:00:00`).toLocaleDateString('en', { month: 'short', year: 'numeric' })

export function ForecastPage() {
  const { org, pro } = useApp()
  const [months, setMonths] = useState('6')
  const query = useQuery(q<Forecast>(['forecast', org.id, months], 'BooksService', 'getForecast', [org.id, Number(months)]))
  const d = org.decimals
  return (
    <Screen title="Forecast" sub="An estimate from your past months, plus what is already due in and out.">
      <Toolbar>
        <Chips label="Months ahead" value={months} onChange={setMonths} options={[{ id: '3', label: '3 months' }, { id: '6', label: '6 months' }, { id: '12', label: '12 months' }]} />
        <span className="ml-auto"><AskChip prompt="Look at my forecast. Will I have enough cash, and what should I watch?">Will I have enough cash?</AskChip></span>
      </Toolbar>
      <Loaded query={query} empty={(f) => (f.months_of_history === 0 ? <Empty title="Nothing to forecast from yet" body="A forecast needs past income and costs. It starts working once you have a few months in your books." /> : null)}>
        {(f) => (
          <>
            <div className="sheet px-3.5 py-2.5 flex flex-wrap items-center gap-2 text-[13.5px]">
              <Badge dot tone={f.confidence === 'reasonable' ? 'good' : 'warn'}>{f.confidence === 'reasonable' ? 'Reasonable estimate' : f.confidence === 'low' ? 'Rough estimate' : 'Very rough estimate'}</Badge>
              <span className="text-muted-foreground">Based on {f.months_of_history} of the last 12 months. It carries your recent average and trend forward, so it won't see one-off events or seasons coming.</span>
            </div>
            <Stats cols={3}>
              <Stat label={pro ? 'Cash today' : 'In the bank today'} value={figure(f.cash_today, 0)} />
              <Stat label={`Estimated cash, ${monthName(f.rows[f.rows.length - 1].month)}`} value={figure(f.rows[f.rows.length - 1].cash, 0)} tone={f.rows[f.rows.length - 1].cash < 0 ? 'warn' : undefined} />
              <Stat label="Estimated net, all months" value={figure(f.rows.reduce((s, r) => s + r.net, 0), 0)} />
            </Stats>
            <section className="sheet px-3.5 py-2.5"><h2 className="font-semibold text-[13.5px] mb-1">{pro ? 'Forecast revenue and expenses' : 'Estimated money in and out'}</h2><Trend rows={f.rows} /></section>
            <Table min={680}>
              <thead><tr><Head>Month</Head><Head right>{pro ? 'Revenue' : 'Money in'}</Head><Head right>{pro ? 'Expenses' : 'Money out'}</Head><Head right>Net</Head><Head right>Invoices due</Head><Head right>Bills due</Head><Head right>Estimated cash</Head></tr></thead>
              <tbody>{f.rows.map((r) => <tr key={r.month}><Cell>{monthName(r.month)}</Cell><Cell right>{figure(r.revenue, d)}</Cell><Cell right>{figure(r.expenses, d)}</Cell><Cell right className={r.net < 0 ? 'text-[var(--note)]' : undefined}>{figure(r.net, d)}</Cell><Cell right>{r.receivable_due ? figure(r.receivable_due, d) : ''}</Cell><Cell right>{r.payable_due ? figure(r.payable_due, d) : ''}</Cell><Cell right className={r.cash < 0 ? 'text-[var(--note)]' : undefined}>{figure(r.cash, d)}</Cell></tr>)}</tbody>
            </Table>
          </>
        )}
      </Loaded>
    </Screen>
  )
}

// ---- Tax ----

type TaxSummary = { from: string; to: string; output_tax: number; input_tax: number; net_tax: number; rates: { rate_name: string; rate: number; sales: number; output_tax: number; purchases: number; input_tax: number }[] }
type TaxReturn = { id: Id; period_from: string; period_to: string; output_tax: number; input_tax: number; net_tax: number; reference: string | null; filed_at: string }

export function Tax() {
  const { org, pro } = useApp()
  const quarter = periodRange('quarter')
  const [from, setFrom] = useState(quarter.from)
  const [to, setTo] = useState(quarter.to)
  const summary = useQuery(q<TaxSummary>(['tax', org.id, from, to], 'BooksService', 'getTaxSummary', [org.id, from, to]))
  const rates = useQuery(ratesQuery(org.id))
  const returns = useQuery(q<TaxReturn[]>(['tax', org.id, 'returns'], 'BooksService', 'listTaxReturns', [org.id]))
  const [editing, setEditing] = useState<{ id?: Id; name?: string; rate?: number } | null>(null)
  const [reference, setReference] = useState('')
  const record = useSave(() => call('BooksService', 'recordTaxReturn', [org.id, { from, to, reference: reference.trim() || null }]), { success: 'Recorded as filed', refresh: ['tax'], onDone: () => setReference('') })
  const s = summary.data
  const d = org.decimals
  return (
    <Screen title="Tax" sub="Tax on your invoices and bills, ready to check against your return." actions={<button className={btn.plain} onClick={() => setEditing({})}><Plus className="size-3.5 mr-1.5" />New tax rate</button>}>
      <Toolbar>
        <label className="flex items-center gap-2 text-[13px]"><span className="text-muted-foreground">From</span><Input aria-label="From date" type="date" value={from} onChange={(e) => setFrom(e.target.value)} className="h-8 w-[150px]" /></label>
        <label className="flex items-center gap-2 text-[13px]"><span className="text-muted-foreground">To</span><Input aria-label="To date" type="date" value={to} onChange={(e) => setTo(e.target.value)} className="h-8 w-[150px]" /></label>
        <span className="ml-auto"><AskChip prompt={`Explain my tax position from ${from} to ${to} in simple words.`}>Explain my tax position</AskChip></span>
      </Toolbar>
      <Loaded query={summary}>
        {() => s ? <>
          <Stats cols={3}>
            <Stat label={pro ? 'Output tax' : 'Tax you charged'} value={figure(s.output_tax, d)} />
            <Stat label={pro ? 'Input tax' : 'Tax you paid'} value={figure(s.input_tax, d)} />
            <Stat label={s.net_tax >= 0 ? (pro ? 'Net payable' : 'You owe') : (pro ? 'Net reclaimable' : 'You can reclaim')} value={figure(Math.abs(s.net_tax), d)} />
          </Stats>
          {s.rates.length ? (
            <Table min={600}>
              <thead><tr><Head>Rate</Head><Head right>Sales</Head><Head right>Tax charged</Head><Head right>Purchases</Head><Head right>Tax paid</Head></tr></thead>
              <tbody>{s.rates.map((r) => <tr key={r.rate_name}><Cell>{r.rate_name}</Cell><Cell right>{figure(r.sales, d)}</Cell><Cell right>{figure(r.output_tax, d)}</Cell><Cell right>{figure(r.purchases, d)}</Cell><Cell right>{figure(r.input_tax, d)}</Cell></tr>)}</tbody>
            </Table>
          ) : <Empty title="No tax in this period" body="Tax shows here once posted invoices or bills in these dates have a tax rate." />}
          <div className="sheet px-3.5 py-3 flex flex-wrap items-end gap-3">
            <div className="flex-1 min-w-[240px]">
              <h2 className="font-semibold text-[13.5px]">Record this return as filed</h2>
              <p className="text-[12.5px] text-muted-foreground">This only keeps a record here. You still file with your tax authority yourself, and your accountant should confirm the figures. Tax counts from each document's date.</p>
            </div>
            <Text label="Filing reference" value={reference} onChange={setReference} />
            <button className={btn.primary} disabled={record.isPending} onClick={() => record.mutate()}>Record as filed</button>
          </div>
        </> : null}
      </Loaded>
      <section className="grid gap-3.5 lg:grid-cols-2 items-start">
        <div className="flex flex-col gap-2">
          <h2 className="font-semibold text-[13.5px]">Tax rates</h2>
          <Loaded query={rates} empty={(r) => (r.length === 0 ? <Empty title="No tax rates yet" body="Add the rates you charge and pay, then use them on invoices and bills." /> : null)}>
            {(r) => <Table min={280}><thead><tr><Head>Name</Head><Head right>Rate</Head><Head>Status</Head></tr></thead><tbody>{r.map((x) => <tr key={x.id} tabIndex={0} className="cursor-pointer hover:bg-accent/50" onClick={() => setEditing(x)} onKeyDown={(e) => { if (e.key === 'Enter') setEditing(x) }}><Cell>{x.name}</Cell><Cell right>{x.rate}%</Cell><Cell><Badge dot tone={x.is_active ? 'good' : 'neutral'}>{x.is_active ? 'In use' : 'Off'}</Badge></Cell></tr>)}</tbody></Table>}
          </Loaded>
        </div>
        <div className="flex flex-col gap-2">
          <h2 className="font-semibold text-[13.5px]">Recorded returns</h2>
          <Loaded query={returns} empty={(r) => (r.length === 0 ? <Empty title="None recorded yet" body="Returns you record as filed are kept here." /> : null)}>
            {(r) => <Table min={360}><thead><tr><Head>Period</Head><Head>Reference</Head><Head right>Net</Head></tr></thead><tbody>{r.map((x) => <tr key={x.id}><Cell className="text-muted-foreground">{shortDate(x.period_from)} to {shortDate(x.period_to)}</Cell><Cell>{x.reference ?? ''}</Cell><Cell right>{figure(num(x.net_tax), d)}</Cell></tr>)}</tbody></Table>}
          </Loaded>
        </div>
      </section>
      {editing ? <RateForm rate={editing as RateDraft} onClose={() => setEditing(null)} /> : null}
    </Screen>
  )
}

type RateDraft = { id?: Id; name?: string; rate?: number; sales_account_id?: Id; purchase_account_id?: Id; is_active?: boolean }
function RateForm({ rate, onClose }: { rate: RateDraft; onClose: () => void }) {
  const { org } = useApp()
  const chart = useQuery(accounts(org.id))
  const [f, setF] = useState({ name: rate.name ?? '', rate: rate.rate != null ? String(rate.rate) : '', sales: rate.sales_account_id ? String(rate.sales_account_id) : '', purchase: rate.purchase_account_id ? String(rate.purchase_account_id) : '', active: rate.is_active ?? true })
  const options = useMemo(() => (chart.data ?? []).filter((a) => a.is_postable !== false && (a.account_type === 'liability' || a.account_type === 'asset')).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` })), [chart.data])
  const save = useSave(() => call('BooksService', 'saveTaxRate', [org.id, { id: rate.id, name: f.name, rate: Number(f.rate), sales_account_id: Number(f.sales), purchase_account_id: Number(f.purchase), is_active: f.active }]), { success: 'Tax rate saved', refresh: ['tax'], onDone: onClose })
  return (
    <Modal open onClose={onClose} title={rate.id ? 'Edit tax rate' : 'New tax rate'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save rate" pending={save.isPending} onCancel={onClose} disabled={!f.name.trim() || f.rate === '' || !f.sales || !f.purchase}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Name" required placeholder="For example, GST" value={f.name} onChange={(v) => setF((x) => ({ ...x, name: v }))} />
          <Text label="Rate (%)" required inputMode="decimal" value={f.rate} onChange={(v) => setF((x) => ({ ...x, rate: v }))} />
        </div>
        <Choice label="Tax you charge goes to" hint="Usually a liability, since you owe it to the tax authority." placeholder="Select account" value={f.sales} onChange={(v) => setF((x) => ({ ...x, sales: v }))} options={options} />
        <Choice label="Tax you pay goes to" hint="Usually an asset, or the same account, if you can reclaim it." placeholder="Select account" value={f.purchase} onChange={(v) => setF((x) => ({ ...x, purchase: v }))} options={options} />
        {rate.id ? <label className="flex items-center gap-2 text-[13px] cursor-pointer"><input type="checkbox" checked={f.active} onChange={(e) => setF((x) => ({ ...x, active: e.target.checked }))} />Available on new documents</label> : null}
      </FormBody>
    </Modal>
  )
}

// ---- Closing the books ----

type Lock = { closed_through: string | null; history: { id: Id; through_date: string; notes: string | null; closed_at: string; reopened_at: string | null; reopen_reason: string | null }[] }
type Checklist = { balanced: boolean; draft_documents: number; unmatched_bank_lines: number; pending_proposals: number; unposted_stock: number; unposted_vouchers: number }

const lastMonthEnd = () => { const d = new Date(); return iso(new Date(d.getFullYear(), d.getMonth(), 0)) }

export function CloseBooks() {
  const { org, access, pro } = useApp()
  const lock = useQuery(q<Lock>(['close', org.id], 'BooksService', 'getBooksLock', [org.id]))
  const [through, setThrough] = useState(lastMonthEnd())
  const [notes, setNotes] = useState('')
  const [reopening, setReopening] = useState(false)
  const [reason, setReason] = useState('')
  const check = useQuery(q<Checklist>(['close', org.id, 'check', through], 'BooksService', 'getCloseChecklist', [org.id, through]))
  const close = useSave(() => call('BooksService', 'closeBooks', [org.id, { through, notes }]), { success: 'Books closed', refresh: ['close'], onDone: () => { setNotes(''); refreshBooks() } })
  const reopen = useSave(() => call('BooksService', 'reopenBooks', [org.id, { reason }]), { success: 'Period reopened', refresh: ['close'], onDone: () => { setReason(''); setReopening(false); refreshBooks() } })
  const closed = lock.data?.closed_through
  const c = check.data
  useEffect(() => { if (closed && through <= closed) setThrough(lastMonthEnd() > closed ? lastMonthEnd() : today()) }, [closed]) // eslint-disable-line react-hooks/exhaustive-deps
  const warn = (n: number | undefined, one: string, many: string) => <Check ok={!n} title={n ? `${n} ${n === 1 ? one : many}` : `No ${many}`} />
  return (
    <Screen title="Close books" sub={pro ? 'Lock finished periods against new entries.' : "When a month is finished, lock it so nothing changes by accident."}>
      <Stats cols={2}>
        <Stat label="Closed through" value={closed ? shortDate(closed) : 'Nothing closed yet'} />
        <Stat label="Entries allowed from" value={closed ? 'The day after' : 'Any date'} />
      </Stats>
      <section className="sheet px-3.5 py-3 flex flex-col gap-3">
        <h2 className="font-semibold text-[13.5px]">Close a period</h2>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Close through" type="date" max={today()} value={through} onChange={setThrough} />
          <Text label="Notes" value={notes} onChange={setNotes} />
        </div>
        {c ? (
          <div className="border border-border rounded-[8px] overflow-hidden grid gap-px bg-border sm:grid-cols-2">
            <Check ok={c.balanced} title={c.balanced ? 'Debits equal credits' : "The books don't balance, so this can't be closed"} />
            {warn(c.draft_documents, 'draft invoice or bill in this period', 'draft invoices or bills')}
            {warn(c.unmatched_bank_lines, 'bank line still to sort', 'bank lines to sort')}
            {warn(c.pending_proposals, 'agent proposal waiting', 'agent proposals waiting')}
            {warn(c.unposted_stock, 'stock movement not in the books', 'stock movements outside the books')}
            {warn(c.unposted_vouchers, 'voucher waiting to be posted', 'vouchers waiting to be posted')}
          </div>
        ) : null}
        <p className="text-[12.5px] text-muted-foreground">Amber items are worth sorting first, but they won't stop you. After closing, no entry can be dated on or before this date. Reversals and corrections then go in an open period. This locks dates; it doesn't move profit into retained earnings, so check that with your accountant at year end.</p>
        <div><button className={cn(btn.primary)} disabled={!c?.balanced || close.isPending} onClick={() => close.mutate()}>{close.isPending ? 'Closing…' : `Close through ${shortDate(through)}`}</button></div>
      </section>
      {closed ? (
        <section className="sheet px-3.5 py-3 flex flex-col gap-2.5">
          <h2 className="font-semibold text-[13.5px]">Reopen the latest period</h2>
          {access !== 'owner' ? <p className="text-[13px] text-muted-foreground">Only an organization owner can reopen a period.</p> : reopening ? (
            <FormBody onSubmit={() => reopen.mutate()} submit="Reopen" pending={reopen.isPending} onCancel={() => setReopening(false)} disabled={!reason.trim()}>
              <Text label="Why is it being reopened?" required value={reason} onChange={setReason} />
            </FormBody>
          ) : <div><button className={btn.plain} onClick={() => setReopening(true)}>Reopen</button></div>}
        </section>
      ) : null}
      <Loaded query={lock}>
        {(l) => l.history.length ? (
          <Table min={520}>
            <thead><tr><Head>Closed through</Head><Head>Status</Head><Head>Notes</Head><Head>When</Head></tr></thead>
            <tbody>{l.history.map((h) => <tr key={h.id}><Cell>{shortDate(h.through_date)}</Cell><Cell><Badge dot tone={h.reopened_at ? 'neutral' : 'good'}>{h.reopened_at ? 'Reopened' : 'Closed'}</Badge></Cell><Cell className="max-w-0 w-full truncate text-muted-foreground">{h.reopen_reason ?? h.notes ?? ''}</Cell><Cell className="text-muted-foreground">{shortDate(h.reopened_at ?? h.closed_at)}</Cell></tr>)}</tbody>
          </Table>
        ) : null}
      </Loaded>
    </Screen>
  )
}
