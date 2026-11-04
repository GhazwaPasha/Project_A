import { useEffect, useRef, useState, type ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import NumberFlow from '@number-flow/react'
import { AlertTriangle, BarChart3, Bell, BookOpen, CheckCircle2, ClipboardCheck, CreditCard, FileText, Landmark, PackageOpen, Percent, PieChart, Receipt, TrendingUp, Wallet, type LucideIcon } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { AskLink, ProposalCard } from '@/components/agent-panel'
import { NewEntry } from '@/components/new-entry'
import { btn } from '@/components/page'
import { Chips, Count } from '@/components/chips'
import { figure, shortDate, useApp } from '@/lib/boot'
import { ApiError } from '@/lib/api'
import { balanceSheet, dashboard, incomeStatement, journal, lowStock, monthly, num, periodRange, proposals, q, today, voucherStats, type MonthRow, type Period } from '@/lib/data'

type Hue = 'indigo' | 'blue' | 'emerald' | 'violet' | 'amber' | 'rose'
const BAR_HUES: Hue[] = ['rose', 'amber', 'violet', 'blue', 'emerald']

const PERIODS = [{ id: 'month', label: 'This month' }, { id: 'quarter', label: 'This quarter' }, { id: 'year', label: 'This year' }]

export function Home() {
  const { org, pro } = useApp()
  const [period, setPeriod] = useState<Period>('month')
  const [entry, setEntry] = useState(false)
  const { from, to } = periodRange(period)
  const dash = useQuery(dashboard(org.id, from, to))
  const income = useQuery({ ...incomeStatement(org.id, from, to), enabled: pro })
  const sheet = useQuery(balanceSheet(org.id, today()))
  const months = useQuery(monthly(org.id))
  const entries = useQuery(journal(org.id))
  const low = useQuery(lowStock(org.id))
  const work = useQuery({ ...q<{ overdue_invoices: number; overdue_bills: number; unmatched_bank_lines: number }>(['work-summary', org.id], 'BooksService', 'getWorkSummary', [org.id]), retry: false }).data
  const vouchers = useQuery(voucherStats(org.id))
  const waiting = useQuery(proposals(org.id))

  const revenue = num(dash.data?.financialMetrics.totalRevenue)
  const expenses = num(dash.data?.financialMetrics.totalExpenses)
  const assets = num(sheet.data?.totalAssets)
  const liabilities = num(sheet.data?.totalLiabilities)
  const top = (dash.data?.accountBalances ?? []).filter((a) => a.account_type === 'expense' && num(a.balance) > 0).sort((a, b) => num(b.balance) - num(a.balance)).slice(0, 5)
  const pending = num(vouchers.data?.pending_approval)
  const lowItems = low.data ?? []
  const proposalList = waiting.data ?? []
  const notMigrated = waiting.error instanceof ApiError && waiting.error.status === 503
  const needCount = proposalList.length + (pending > 0 ? 1 : 0) + lowItems.length + (work?.overdue_invoices ? 1 : 0) + (work?.overdue_bills ? 1 : 0)

  return (
    <div className="page-in flex flex-col gap-3.5">
      <header className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <h1 className="text-[20px] leading-tight font-semibold tracking-[-0.018em]">Home</h1>
        <div className="flex flex-wrap items-center gap-2">
          <Chips label="Period" value={period} options={PERIODS} onChange={(p) => setPeriod(p as Period)} />
          {pro ? <button className={btn.primary} onClick={() => setEntry(true)}>New entry</button> : null}
        </div>
      </header>


      <section aria-label="Key figures" className="sheet grid grid-cols-2 lg:grid-cols-4 overflow-hidden divide-border [&>*]:border-border max-lg:[&>*:nth-child(odd)]:border-r max-lg:[&>*:nth-child(-n+2)]:border-b lg:[&>*:not(:last-child)]:border-r">
        <Stat hue="emerald" icon={TrendingUp} label={pro ? 'Net income' : 'Profit'} value={revenue - expenses} loading={dash.isPending} to="/reports/income-statement" search={{ period }} />
        <Stat hue="indigo" icon={Landmark} label={pro ? 'Revenue' : 'Sales'} value={revenue} loading={dash.isPending} to="/reports/income-statement" search={{ period }} />
        <Stat hue="violet" icon={Wallet} label={pro ? 'Total assets' : 'You own'} value={assets} loading={sheet.isPending} to="/reports/balance-sheet" />
        <Stat hue="rose" icon={CreditCard} label={pro ? 'Total liabilities' : 'You owe'} value={liabilities} loading={sheet.isPending} to="/reports/balance-sheet" />
      </section>

      <div className="grid gap-3.5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] items-start">
          <section className="sheet">
            <SectionHead hue="indigo" icon={BarChart3} title={pro ? 'Revenue and expenses' : 'Money in and out'} right={<span className="flex gap-3 text-[12px] text-muted-foreground"><Key color="var(--chart-in)" label={pro ? 'Revenue' : 'In'} /><Key color="var(--chart-out)" label={pro ? 'Expenses' : 'Out'} /></span>} />
            <div className="px-3.5 pb-2">
              {months.isPending ? <Skeleton className="h-44 w-full" /> : months.isError ? <p className="text-[13.5px] text-muted-foreground">Monthly figures didn't load.</p> : <Trend rows={months.data} />}
            </div>
          </section>
          <section className="sheet overflow-y-auto lg:max-h-[266px]" aria-label="Needs your attention">
            <SectionHead hue="amber" icon={Bell} title="Needs your attention" right={<Count n={needCount} tone="warn" label="items need attention" />} />
            {proposalList.map((p) => <div key={p.id} className="px-3.5 py-2.5 border-t border-border"><ProposalCard proposal={p} /></div>)}
            {pending > 0 ? <Row hue="violet" icon={ClipboardCheck} title={`${pending} ${pending === 1 ? 'voucher needs' : 'vouchers need'} approval`} body="Stock can't move until these are decided." action={<Link to="/approvals" className={btn.plain}>Review</Link>} /> : null}
            {work?.overdue_invoices ? <Row hue="blue" icon={FileText} title={`${work.overdue_invoices} overdue ${work.overdue_invoices === 1 ? 'invoice' : 'invoices'}`} body="Customers who haven't paid on time." action={<Link to="/invoices" className={btn.plain}>Review</Link>} /> : null}
            {work?.overdue_bills ? <Row hue="rose" icon={Receipt} title={`${work.overdue_bills} overdue ${work.overdue_bills === 1 ? 'bill' : 'bills'}`} body="Suppliers waiting to be paid." action={<Link to="/bills" className={btn.plain}>Review</Link>} /> : null}
            {lowItems.slice(0, 3).map((i) => <Row key={i.id} hue="amber" icon={PackageOpen} title={`${i.name} is running low`} body={`${figure(num(i.quantity_available), 0)} ${i.unit_of_measure} on hand. Reorder point is ${figure(num(i.reorder_point), 0)}.`} action={<Link to="/inventory" className={btn.plain}>Open</Link>} />)}
            {sheet.data?.isBalanced === false ? <Row hue="amber" icon={AlertTriangle} title="Your books don't balance" body="Assets don't equal liabilities plus equity." action={<AskLink prompt="My books don't balance. Find out why and tell me how to fix it." className="text-[13px]">Find out why</AskLink>} /> : null}
            {needCount === 0 && sheet.data?.isBalanced !== false ? <p className="px-3.5 py-2.5 border-t border-border flex items-center gap-2 text-muted-foreground"><CheckCircle2 className="size-4 text-[var(--tick)]" />You're all caught up.</p> : null}
            {notMigrated ? <p className="px-4 pb-3 text-[12.5px] text-muted-foreground">Agent proposals aren't set up on this database yet.</p> : null}
          </section>
      </div>

      <div className={`grid gap-3.5 md:grid-cols-2 ${pro ? 'xl:grid-cols-3' : ''} items-start`}>
          <section className="sheet">
            <SectionHead hue="blue" icon={BookOpen} title="Latest entries" right={<Link to="/journal" className="text-primary text-[13px] font-medium underline decoration-border underline-offset-[3px] hover:decoration-primary">View all</Link>} />
            {(entries.data ?? []).slice(0, 5).map((e) => (
              <div key={e.id} className="flex items-baseline gap-3 px-3.5 py-1.5 border-t border-border">
                <span className="w-[84px] shrink-0 text-[12px] text-muted-foreground">{shortDate(e.entry_date)}</span>
                <span className="flex-1 min-w-0 truncate text-[13.5px]">{e.description || e.entry_number}</span>
                <span className="fig text-[13px] shrink-0">{figure(num(e.total_amount), org.decimals)}</span>
              </div>
            ))}
            {entries.isPending ? <div className="px-4 pb-3"><Skeleton className="h-24 w-full" /></div> : null}
            {entries.data?.length === 0 ? <p className="px-4 py-3 border-t border-border text-[13.5px] text-muted-foreground">Nothing recorded yet. Tell the agent what happened to get started.</p> : null}
          </section>
          <section className="sheet">
            <SectionHead hue="rose" icon={PieChart} title={pro ? 'Top expenses' : 'Where money went'} />
            {top.length === 0 && !dash.isPending ? <p className="px-4 py-3 border-t border-border text-[13.5px] text-muted-foreground">No expenses in this period.</p> : null}
            {top.map((a, i) => (
              <div key={a.id} data-hue={BAR_HUES[i % BAR_HUES.length]} className="px-3.5 py-1.5 border-t border-border text-[13.5px]">
                <div className="flex justify-between gap-3"><span className="truncate">{a.name}</span><span className="fig text-[13px] shrink-0">{figure(num(a.balance), org.decimals)}</span></div>
                <div className="h-1.5 mt-1 rounded-full bg-muted overflow-hidden"><div className="meter h-full rounded-full" style={{ width: `${(num(a.balance) / (num(top[0].balance) || 1)) * 100}%`, ['--i' as string]: i }} /></div>
              </div>
            ))}
          </section>
          {pro ? (
            <section className="sheet">
              <SectionHead hue="violet" icon={Percent} title="Ratios" />
              <dl className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1.5 px-3.5 py-2.5 border-t border-border text-[13.5px]">
                <Ratio label="Gross margin" value={revenue && income.data ? `${figure((num(income.data.grossProfit) / revenue) * 100, 1)}%` : 'n/a'} />
                <Ratio label="Net margin" value={revenue ? `${figure(((revenue - expenses) / revenue) * 100, 1)}%` : 'n/a'} />
                <Ratio label="Assets to liabilities" value={liabilities ? `${figure(assets / liabilities, 2)} : 1` : 'n/a'} />
              </dl>
            </section>
          ) : null}
      </div>
      <NewEntry open={entry} onOpenChange={setEntry} />
    </div>
  )
}

function SectionHead({ title, right, icon: Icon, hue }: { title: string; right?: ReactNode; icon: LucideIcon; hue: Hue }) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 px-3.5 py-2">
      <h2 data-hue={hue} className="flex items-center gap-2 font-semibold text-[13.5px]"><span className="tile size-[22px] rounded-[6px]"><Icon aria-hidden className="size-3.5" /></span>{title}</h2>
      {right}
    </div>
  )
}
const Key = ({ color, label }: { color: string; label: string }) => <span className="flex items-center gap-1.5"><i className="size-2 rounded-[2px]" style={{ background: color }} />{label}</span>

function Row({ icon: Icon, hue, title, body, action }: { icon: LucideIcon; hue: Hue; title: string; body: string; action: ReactNode }) {
  return (
    <div className="flex items-center gap-3 px-3.5 py-2 border-t border-border">
      <span data-hue={hue} className="tile size-7 shrink-0 rounded-[7px]"><Icon aria-hidden className="size-4" /></span>
      <div className="min-w-0 flex-1"><p className="font-medium text-[13.5px]">{title}</p><p className="text-[12.5px] text-muted-foreground">{body}</p></div>
      <div className="shrink-0">{action}</div>
    </div>
  )
}

function Stat({ label, value, loading, to, search, icon: Icon, hue }: { label: string; value: number; loading: boolean; to: string; search?: Record<string, string>; icon: LucideIcon; hue: Hue }) {
  const { org } = useApp()
  // Rolls up from zero when the figure arrives, and from the old figure when the period changes.
  const [shown, setShown] = useState(0)
  useEffect(() => { if (!loading) setShown(value) }, [loading, value])
  const format = Math.abs(value) >= 1e9 ? { notation: 'compact', maximumFractionDigits: 2 } as const : { maximumFractionDigits: 0 }
  return (
    <Link to={to} search={search} data-hue={hue} className="stat-card group relative overflow-hidden block px-3.5 py-2.5 min-w-0">
      <p className="text-[12.5px] text-muted-foreground pr-6">{label}</p>
      <span className="tile stat-tile absolute top-2 right-2 size-6 rounded-[7px]"><Icon aria-hidden className="size-3.5" /></span>
      <Icon aria-hidden className="stat-prop" />
      {loading ? <Skeleton className="h-7 w-28 mt-1.5" /> : (
        <p className="relative flex flex-wrap items-baseline gap-x-1.5 text-[20px] leading-tight font-semibold tracking-[-0.02em]">
          <span className="text-[12px] font-medium text-muted-foreground tracking-normal">{org.currency}</span>
          <NumberFlow value={shown} format={format} transformTiming={{ duration: 520, easing: 'cubic-bezier(0.23, 1, 0.32, 1)' }} spinTiming={{ duration: 620, easing: 'cubic-bezier(0.23, 1, 0.32, 1)' }} />
        </p>
      )}
    </Link>
  )
}

const Ratio = ({ label, value }: { label: string; value: string }) => <><dt className="text-muted-foreground truncate">{label}</dt><dd className="fig text-right">{value}</dd></>

/** Twelve real months from the database. Nothing here is estimated. */
export function Trend({ rows }: { rows: MonthRow[] }) {
  // Drawn at the width it's given, so the chart stays the same height on any screen.
  const box = useRef<HTMLDivElement>(null)
  const [W, setW] = useState(640)
  useEffect(() => {
    const el = box.current
    if (!el) return
    const watch = new ResizeObserver(([e]) => setW(Math.max(280, e.contentRect.width)))
    watch.observe(el)
    return () => watch.disconnect()
  }, [])
  const H = 196, L = 44, R = 8, T = 8, B = 22
  const vals = rows.flatMap((r) => [num(r.revenue), num(r.expenses)])
  const max = Math.max(1, ...vals)
  if (!vals.some(Boolean)) return <p className="text-[13.5px] text-muted-foreground py-6">No activity in the last 12 months.</p>
  const step = (W - L - R) / Math.max(rows.length, 1)
  const y = (v: number) => T + (H - T - B) * (1 - Math.max(0, v) / max)
  const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 })
  return (
    <div ref={box}><svg className="trend" viewBox={`0 0 ${W} ${H}`} width="100%" height={H} role="img" aria-label="Revenue and expenses for the last 12 months">
      {[0, 0.5, 1].map((f) => <g key={f}><line x1={L} x2={W - R} y1={y(max * f)} y2={y(max * f)} stroke="var(--border)" /><text x={L - 8} y={y(max * f) + 3.5} textAnchor="end" fontSize="10.5" fill="var(--muted-foreground)">{compact.format(max * f)}</text></g>)}
      {rows.map((r, i) => {
        const w = Math.min(step * 0.3, 18)
        const cx = L + step * i + step / 2
        const label = new Date(`${r.month}-01T00:00:00`).toLocaleDateString('en', { month: 'short' })
        return (
          <g key={r.month} className="trend-col" style={{ ['--i' as string]: i }}>
            <rect x={L + step * i} y={T} width={step} height={H - T - B} fill="transparent" />
            <rect className="trend-bar" x={cx - w - 1} y={y(num(r.revenue))} width={w} height={H - B - y(num(r.revenue))} rx="2" fill="var(--chart-in)"><title>{`${label}: ${figure(num(r.revenue))}`}</title></rect>
            <rect className="trend-bar" x={cx + 1} y={y(num(r.expenses))} width={w} height={H - B - y(num(r.expenses))} rx="2" fill="var(--chart-out)"><title>{`${label}: ${figure(num(r.expenses))}`}</title></rect>
            <text x={cx} y={H - 6} textAnchor="middle" fontSize="10.5" fill="var(--muted-foreground)">{label}</text>
          </g>
        )
      })}
    </svg></div>
  )
}
