import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { AlertTriangle, CheckCircle2, ClipboardCheck, PackageOpen } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { AskChip, AskLink, Composer, ProposalCard } from '@/components/agent-panel'
import { NewEntry } from '@/components/new-entry'
import { PageIcons } from '@/components/page-icons'
import { btn } from '@/components/page'
import { Chips, Count } from '@/components/chips'
import { figure, shortDate, useApp } from '@/lib/boot'
import { ApiError } from '@/lib/api'
import { balanceSheet, dashboard, incomeStatement, journal, lowStock, monthly, num, periodRange, proposals, today, voucherStats, type MonthRow, type Period } from '@/lib/data'

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
  const needCount = proposalList.length + (pending > 0 ? 1 : 0) + lowItems.length

  return (
    <div className="flex flex-col gap-3.5">
      <header className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <div>
          <h1 className="text-[20px] leading-tight font-semibold tracking-[-0.018em]">Home</h1>
          <p className="text-[13px] text-muted-foreground">{needCount ? `${needCount} ${needCount === 1 ? 'item needs' : 'items need'} your attention.` : 'Nothing needs your attention right now.'}</p>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <Chips label="Period" value={period} options={PERIODS} onChange={(p) => setPeriod(p as Period)} />
          {pro ? <button className={btn.primary} onClick={() => setEntry(true)}>New entry</button> : null}
          <PageIcons className="hidden lg:flex" />
        </div>
      </header>

      <Composer placeholder="Tell the agent what happened, or ask about your books" />
      <div className="flex flex-wrap gap-1.5 -mt-1.5" aria-label="Suggestions">
        <AskChip prompt="How is my business doing this month?">How am I doing this month?</AskChip>
        <AskChip prompt="What are my biggest costs this year, and where could I save?">Where can I save?</AskChip>
        <AskChip prompt="Do my books look right? Check for anything that needs fixing.">Check my books</AskChip>
      </div>

      <section aria-label="Key figures" className="sheet grid grid-cols-2 lg:grid-cols-4 overflow-hidden divide-border [&>*]:border-border max-lg:[&>*:nth-child(odd)]:border-r max-lg:[&>*:nth-child(-n+2)]:border-b lg:[&>*:not(:last-child)]:border-r">
        <Stat label={pro ? 'Net income' : 'Profit'} value={revenue - expenses} loading={dash.isPending} to="/reports/income-statement" search={{ period }} />
        <Stat label={pro ? 'Revenue' : 'Sales'} value={revenue} loading={dash.isPending} to="/reports/income-statement" search={{ period }} />
        <Stat label={pro ? 'Total assets' : 'You own'} value={assets} loading={sheet.isPending} to="/reports/balance-sheet" />
        <Stat label={pro ? 'Total liabilities' : 'You owe'} value={liabilities} loading={sheet.isPending} to="/reports/balance-sheet" />
      </section>

      <div className="grid gap-3.5 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)] items-start">
          <section className="sheet">
            <SectionHead title={pro ? 'Revenue and expenses' : 'Money in and out'} right={<span className="flex gap-3 text-[12px] text-muted-foreground"><Key className="bg-primary" label={pro ? 'Revenue' : 'In'} /><Key className="bg-muted-foreground" label={pro ? 'Expenses' : 'Out'} /></span>} />
            <div className="px-3.5 pb-2">
              {months.isPending ? <Skeleton className="h-44 w-full" /> : months.isError ? <p className="text-[13.5px] text-muted-foreground">Monthly figures didn't load.</p> : <Trend rows={months.data} />}
            </div>
          </section>
          <section className="sheet overflow-y-auto lg:max-h-[266px]" aria-label="Needs your attention">
            <SectionHead title="Needs your attention" right={<Count n={needCount} tone="warn" label="items need attention" />} />
            {proposalList.map((p) => <div key={p.id} className="px-3.5 py-2.5 border-t border-border"><ProposalCard proposal={p} /></div>)}
            {pending > 0 ? <Row icon={<ClipboardCheck className="size-4" />} title={`${pending} ${pending === 1 ? 'voucher needs' : 'vouchers need'} approval`} body="Stock can't move until these are decided." action={<Link to="/approvals" className={btn.plain}>Review</Link>} /> : null}
            {lowItems.slice(0, 3).map((i) => <Row key={i.id} icon={<PackageOpen className="size-4" />} title={`${i.name} is running low`} body={`${figure(num(i.quantity_available), 0)} ${i.unit_of_measure} on hand. Reorder point is ${figure(num(i.reorder_point), 0)}.`} action={<Link to="/inventory" className={btn.plain}>Open</Link>} />)}
            {sheet.data?.isBalanced === false ? <Row icon={<AlertTriangle className="size-4 text-[var(--note)]" />} title="Your books don't balance" body="Assets don't equal liabilities plus equity." action={<AskLink prompt="My books don't balance. Find out why and tell me how to fix it." className="text-[13px]">Find out why</AskLink>} /> : null}
            {needCount === 0 && sheet.data?.isBalanced !== false ? <p className="px-3.5 py-2.5 border-t border-border flex items-center gap-2 text-muted-foreground"><CheckCircle2 className="size-4 text-[var(--tick)]" />You're all caught up.</p> : null}
            {notMigrated ? <p className="px-4 pb-3 text-[12.5px] text-muted-foreground">Agent proposals aren't set up on this database yet.</p> : null}
          </section>
      </div>

      <div className={`grid gap-3.5 md:grid-cols-2 ${pro ? 'xl:grid-cols-3' : ''} items-start`}>
          <section className="sheet">
            <SectionHead title="Latest entries" right={<Link to="/journal" className="text-primary text-[13px] font-medium underline decoration-border underline-offset-[3px] hover:decoration-primary">View all</Link>} />
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
            <SectionHead title={pro ? 'Top expenses' : 'Where money went'} />
            {top.length === 0 && !dash.isPending ? <p className="px-4 py-3 border-t border-border text-[13.5px] text-muted-foreground">No expenses in this period.</p> : null}
            {top.map((a) => (
              <div key={a.id} className="px-3.5 py-1.5 border-t border-border text-[13.5px]">
                <div className="flex justify-between gap-3"><span className="truncate">{a.name}</span><span className="fig text-[13px] shrink-0">{figure(num(a.balance), org.decimals)}</span></div>
                <div className="h-1 mt-1 rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${(num(a.balance) / (num(top[0].balance) || 1)) * 100}%` }} /></div>
              </div>
            ))}
          </section>
          {pro ? (
            <section className="sheet">
              <SectionHead title="Ratios" />
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

function SectionHead({ title, right }: { title: string; right?: React.ReactNode }) {
  return <div className="flex items-center justify-between gap-3 px-3.5 py-2"><h2 className="font-semibold text-[13.5px]">{title}</h2>{right}</div>
}
const Key = ({ className, label }: { className: string; label: string }) => <span className="flex items-center gap-1.5"><i className={`size-2 rounded-[2px] ${className}`} />{label}</span>

function Row({ icon, title, body, action }: { icon: React.ReactNode; title: string; body: string; action: React.ReactNode }) {
  return (
    <div className="flex items-center gap-3 px-3.5 py-2 border-t border-border">
      <span className="text-muted-foreground shrink-0">{icon}</span>
      <div className="min-w-0 flex-1"><p className="font-medium text-[13.5px]">{title}</p><p className="text-[12.5px] text-muted-foreground">{body}</p></div>
      <div className="shrink-0">{action}</div>
    </div>
  )
}

function Stat({ label, value, loading, to, search }: { label: string; value: number; loading: boolean; to: string; search?: Record<string, string> }) {
  const { org } = useApp()
  const shown = Math.abs(value) >= 1e9
    ? new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 2 }).format(value)
    : value.toLocaleString('en', { maximumFractionDigits: 0 })
  return (
    <Link to={to} search={search} className="block px-3.5 py-2.5 min-w-0 hover:bg-accent/60 transition-colors">
      <p className="text-[12.5px] text-muted-foreground truncate">{label}</p>
      {loading ? <Skeleton className="h-7 w-28 mt-1.5" /> : (
        <p className="text-[20px] leading-tight font-semibold tracking-[-0.02em] truncate">
          <span className="text-[12px] font-medium text-muted-foreground tracking-normal mr-1.5">{org.currency}</span>{shown}
        </p>
      )}
    </Link>
  )
}

const Ratio = ({ label, value }: { label: string; value: string }) => <><dt className="text-muted-foreground truncate">{label}</dt><dd className="fig text-right">{value}</dd></>

/** Twelve real months from the database. Nothing here is estimated. */
function Trend({ rows }: { rows: MonthRow[] }) {
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
    <div ref={box}><svg viewBox={`0 0 ${W} ${H}`} width="100%" height={H} role="img" aria-label="Revenue and expenses for the last 12 months">
      {[0, 0.5, 1].map((f) => <g key={f}><line x1={L} x2={W - R} y1={y(max * f)} y2={y(max * f)} stroke="var(--border)" /><text x={L - 8} y={y(max * f) + 3.5} textAnchor="end" fontSize="10.5" fill="var(--muted-foreground)">{compact.format(max * f)}</text></g>)}
      {rows.map((r, i) => {
        const w = Math.min(step * 0.3, 18)
        const cx = L + step * i + step / 2
        const label = new Date(`${r.month}-01T00:00:00`).toLocaleDateString('en', { month: 'short' })
        return (
          <g key={r.month}>
            <rect x={cx - w - 1} y={y(num(r.revenue))} width={w} height={H - B - y(num(r.revenue))} rx="1.5" fill="var(--primary)"><title>{`${label}: ${figure(num(r.revenue))}`}</title></rect>
            <rect x={cx + 1} y={y(num(r.expenses))} width={w} height={H - B - y(num(r.expenses))} rx="1.5" fill="var(--muted-foreground)" opacity="0.55"><title>{`${label}: ${figure(num(r.expenses))}`}</title></rect>
            <text x={cx} y={H - 6} textAnchor="middle" fontSize="10.5" fill="var(--muted-foreground)">{label}</text>
          </g>
        )
      })}
    </svg></div>
  )
}
