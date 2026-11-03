import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useSearch } from '@tanstack/react-router'
import { Skeleton } from '@/components/ui/skeleton'
import { AskLink } from '@/components/agent-panel'
import { Cell, Head, Loaded, PrintButton, Range, Screen, Table, Tabs } from '@/components/page'
import { figure, shortDate, useApp } from '@/lib/boot'
import { balanceSheet, incomeStatement, num, periodRange, today, type Money, type Period, type Section } from '@/lib/data'

const PERIODS = [{ id: 'month', label: 'This month' }, { id: 'quarter', label: 'This quarter' }, { id: 'year', label: 'This year' }]

function useTabs() {
  const { pro } = useApp()
  return [
    { to: '/reports/income-statement', label: pro ? 'Income Statement' : 'Profit' },
    { to: '/reports/balance-sheet', label: pro ? 'Balance Sheet' : 'What you own and owe' },
  ]
}

export function ReportsIndex() {
  const { org, pro, money } = useApp()
  const { from, to } = periodRange('month')
  const income = useQuery(incomeStatement(org.id, from, to))
  const sheet = useQuery(balanceSheet(org.id, today()))
  return (
    <Screen title="Reports" sub={pro ? 'Financial statements from your books.' : 'Ask for any report below, or open one of these.'}>
      <div className="grid gap-3.5 md:grid-cols-2 xl:grid-cols-3">
        <ReportRow to="/reports/income-statement" name={pro ? 'Income Statement' : 'Profit'} desc={pro ? 'Revenue, expenses and net income for a period.' : 'What you earned, what you spent, and what you kept.'} value={income.data ? money(num(income.data.netIncome)) : ''} label={pro ? 'Net income this month' : 'Profit this month'} />
        <ReportRow to="/reports/balance-sheet" name={pro ? 'Balance Sheet' : 'What you own and owe'} desc={pro ? 'Assets, liabilities and equity as of today.' : 'A snapshot of your business today.'} value={sheet.data ? money(num(sheet.data.totalAssets)) : ''} label={pro ? 'Total assets' : 'You own'} />
        <ReportRow to="/trial-balance" name="Trial Balance" desc={pro ? 'Debits and credits by account, with book checks.' : 'A check that your books are right.'} value={sheet.data ? (sheet.data.isBalanced ? 'Balanced' : 'Out of balance') : ''} label="Books" />
      </div>
      <div className="grid gap-3.5 lg:grid-cols-2 items-start">
        <Summary title={pro ? 'Income Statement, this month' : 'Profit, this month'} to="/reports/income-statement" rows={income.data ? [
          [pro ? 'Revenue' : 'Sales', income.data.revenue.total],
          [pro ? 'Cost of sales' : 'Cost of what you sold', -num(income.data.costOfSales.total)],
          [pro ? 'Gross profit' : 'Left after that', income.data.grossProfit, true],
          [pro ? 'Operating expenses' : 'Running costs', -num(income.data.operatingExpenses.total)],
          [pro ? 'Other expenses' : 'Other costs', -num(income.data.otherExpenses.total)],
          [pro ? 'Net income' : 'Profit', income.data.netIncome, true],
        ] : null} />
        <Summary title={pro ? 'Balance Sheet, today' : 'What you own and owe, today'} to="/reports/balance-sheet" rows={sheet.data ? [
          [pro ? 'Total assets' : 'You own', sheet.data.totalAssets, true],
          ...sheet.data.liabilitySections.map((x): SummaryRow => [x.name, x.total]),
          [pro ? 'Total liabilities' : 'You owe', sheet.data.totalLiabilities, true],
          ...sheet.data.equitySections.map((x): SummaryRow => [x.name, x.total]),
          [pro ? 'Total equity' : "What's yours", sheet.data.totalEquity, true],
        ] : null} />
      </div>
      <section className="sheet px-3.5 py-2.5 flex flex-wrap gap-x-5 gap-y-1 items-center text-[13.5px]" aria-label="Ask for a report">
        <h2 className="font-semibold">Or ask me</h2>
        <AskLink prompt="Compare my sales and costs this year against last year.">Compare this year with last year</AskLink>
        <AskLink prompt="What were my top five costs this year?">Show my top five costs this year</AskLink>
        <AskLink prompt="Which months were my most and least profitable this year, and why?">Which months were best and worst?</AskLink>
      </section>
    </Screen>
  )
}

type SummaryRow = [label: string, value: Money, strong?: boolean]

function Summary({ title, to, rows }: { title: string; to: '/reports/income-statement' | '/reports/balance-sheet'; rows: SummaryRow[] | null }) {
  const { org } = useApp()
  return (
    <section className="sheet overflow-hidden">
      <div className="flex items-center justify-between gap-3 px-3.5 py-2">
        <h2 className="font-semibold text-[13.5px]">{title}</h2>
        <Link to={to} {...(to === '/reports/income-statement' ? { search: { period: 'month' as const } } : {})} className="text-[13px] font-medium underline decoration-border underline-offset-[3px]">Open</Link>
      </div>
      {rows ? rows.map(([label, value, strong]) => (
        <div key={label} className={`flex justify-between gap-3 px-3.5 py-1.5 border-t border-border text-[13.5px] ${strong ? 'font-medium bg-muted/50' : ''}`}>
          <span className="truncate">{label}</span><span className="fig text-[13px] shrink-0">{figure(num(value), org.decimals)}</span>
        </div>
      )) : <div className="px-3.5 pb-3"><Skeleton className="h-32 w-full" /></div>}
    </section>
  )
}

function ReportRow({ to, name, desc, value, label }: { to: string; name: string; desc: string; value: string; label: string }) {
  return (
    <Link to={to} {...(to === '/reports/income-statement' ? { search: { period: 'month' as const } } : {})} className="sheet flex flex-col gap-2 px-3.5 py-3 hover:bg-accent">
      <span><span className="block font-medium">{name}</span><span className="block text-[13px] text-muted-foreground">{desc}</span></span>
      <span className="mt-auto flex items-baseline justify-between gap-3"><span className="text-[12px] text-muted-foreground">{label}</span><span className="fig font-medium">{value || ' '}</span></span>
    </Link>
  )
}

export function IncomeStatementPage() {
  const { org, pro, money } = useApp()
  const { period } = useSearch({ from: '/reports/income-statement' })
  const navigate = useNavigate()
  const tabs = useTabs()
  const { from, to } = periodRange(period)
  const q = useQuery(incomeStatement(org.id, from, to))
  const d = org.decimals
  const revenue = num(q.data?.revenue.total)
  const net = num(q.data?.netIncome)
  return (
    <Screen
      title={pro ? 'Income Statement' : 'Profit'}
      sub={`${shortDate(from)} to ${shortDate(to)}, ${org.currency}`}
      actions={<><Range label="Period" value={period} options={PERIODS} onChange={(p) => void navigate({ to: '/reports/income-statement', search: { period: p as Period } })} /><PrintButton /></>}
      tabs={<Tabs items={tabs} />}
    >
      <Loaded query={q}>
        {(r) => (
          <div className="grid gap-3.5 xl:grid-cols-[minmax(0,1fr)_320px] items-start print:block">
          <Table wrap min={340}>
            <thead><tr><Head>{pro ? 'Account' : 'Item'}</Head><Head right>{org.currency}</Head></tr></thead>
            <tbody>
              <Lines rows={r.revenue.breakdown} decimals={d} />
              <Sub label={pro ? 'Total revenue' : 'Total sales'} value={r.revenue.total} decimals={d} />
              <Lines rows={r.costOfSales.breakdown} decimals={d} negative />
              <Sub label={pro ? 'Gross profit' : 'Left after the cost of what you sold'} value={r.grossProfit} decimals={d} />
              <Lines rows={r.operatingExpenses.breakdown} decimals={d} negative />
              <Lines rows={r.otherExpenses.breakdown} decimals={d} negative />
              <tr className="rule-total"><Cell className="border-b-0">{pro ? 'Net income' : 'Profit'}</Cell><Cell right>{figure(num(r.netIncome), d)}</Cell></tr>
            </tbody>
          </Table>
          <aside className="sheet px-3.5 py-3 flex flex-col gap-2.5 print:hidden">
            <p className="font-medium leading-snug">
              {revenue === 0 && net === 0 ? 'Nothing recorded for this period yet.' : net >= 0 ? <>You kept <span className="font-semibold">{money(net)}</span> of <span className="font-semibold">{money(revenue)}</span> in sales.</> : <>You spent <span className="font-semibold text-[var(--note)]">{money(-net)}</span> more than you earned.</>}
            </p>
            <dl className="grid grid-cols-[minmax(0,1fr)_auto] gap-x-4 gap-y-1 text-[13.5px]">
              <dt className="text-muted-foreground">{pro ? 'Gross margin' : 'Left after stock costs'}</dt><dd className="fig text-right">{revenue ? `${figure((num(r.grossProfit) / revenue) * 100, 1)}%` : 'n/a'}</dd>
              <dt className="text-muted-foreground">{pro ? 'Net margin' : 'Kept from each sale'}</dt><dd className="fig text-right">{revenue ? `${figure((net / revenue) * 100, 1)}%` : 'n/a'}</dd>
              <dt className="text-muted-foreground">{pro ? 'Operating expenses' : 'Running costs'}</dt><dd className="fig text-right">{figure(num(r.operatingExpenses.total), d)}</dd>
            </dl>
            <AskLink className="text-[13.5px]" prompt={`Explain my profit from ${from} to ${to} in simple words. What changed and what should I do?`}>Explain this to me</AskLink>
          </aside>
          </div>
        )}
      </Loaded>
    </Screen>
  )
}

function Lines({ rows, decimals, negative }: { rows: { account: string; amount: Money }[]; decimals: number; negative?: boolean }) {
  return rows.map((l) => <tr key={l.account}><Cell>{l.account}</Cell><Cell right>{figure(negative ? -Math.abs(num(l.amount)) : num(l.amount), decimals)}</Cell></tr>)
}
function Sub({ label, value, decimals }: { label: string; value: Money; decimals: number }) {
  return <tr className="font-medium bg-muted/50"><Cell>{label}</Cell><Cell right>{figure(num(value), decimals)}</Cell></tr>
}

export function BalanceSheetPage() {
  const { org, pro, money } = useApp()
  const tabs = useTabs()
  const asOf = today()
  const q = useQuery(balanceSheet(org.id, asOf))
  const d = org.decimals
  return (
    <Screen title={pro ? 'Balance Sheet' : 'What you own and owe'} sub={`As of ${shortDate(asOf)}, ${org.currency}`} actions={<PrintButton />} tabs={<Tabs items={tabs} />}>
      <Loaded query={q}>
        {(r) => (
          <>
            {r.isBalanced ? null : <p className="font-medium text-[var(--note)]">This doesn't balance yet. <AskLink prompt="My balance sheet doesn't balance. Find out why and tell me how to fix it.">Find out why</AskLink></p>}
            {!pro ? (
              <p className="flex flex-wrap items-baseline gap-x-3 font-medium print:hidden"><span>You own <span className="font-semibold">{money(num(r.totalAssets))}</span> and owe <span className="font-semibold">{money(num(r.totalLiabilities))}</span>, which leaves <span className="font-semibold">{money(num(r.totalAssets) - num(r.totalLiabilities))}</span> that is yours.</span> <AskLink className="text-[13.5px]" prompt="Explain my balance sheet in simple words. Is my business in a healthy position?">Explain this to me</AskLink></p>
            ) : null}
            <div className="grid gap-3.5 lg:grid-cols-2 items-start print:block">
            <Table wrap min={300}>
              <thead><tr><Head>{pro ? 'Account' : 'Item'}</Head><Head right>{org.currency}</Head></tr></thead>
              <tbody>
                <Group title={pro ? 'Assets' : 'What you own'} sections={r.assetSections} total={r.totalAssets} decimals={d} />
              </tbody>
            </Table>
            <Table wrap min={300}>
              <thead><tr><Head>{pro ? 'Account' : 'Item'}</Head><Head right>{org.currency}</Head></tr></thead>
              <tbody>
                <Group title={pro ? 'Liabilities' : 'What you owe'} sections={r.liabilitySections} total={r.totalLiabilities} decimals={d} />
                <Group title={pro ? 'Equity' : "What's yours"} sections={r.equitySections} total={r.totalEquity} decimals={d} />
                <tr className="rule-total"><Cell className="border-b-0">{pro ? 'Total liabilities and equity' : 'Owed plus yours'}</Cell><Cell right>{figure(num(r.totalLiabilities) + num(r.totalEquity), d)}</Cell></tr>
              </tbody>
            </Table>
            </div>
          </>
        )}
      </Loaded>
    </Screen>
  )
}

function Group({ title, sections, total, decimals }: { title: string; sections: Section[]; total: Money; decimals: number }) {
  return (
    <>
      <tr><td colSpan={2} className="px-3.5 py-1.5 text-[12.5px] font-semibold border-b border-border">{title}</td></tr>
      {sections.flatMap((s) => s.accounts).map((a) => <tr key={a.id}><Cell>{a.name}</Cell><Cell right>{figure(num(a.balance), decimals)}</Cell></tr>)}
      <Sub label={`Total ${title.toLowerCase()}`} value={total} decimals={decimals} />
    </>
  )
}
