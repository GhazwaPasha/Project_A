import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams, useSearch } from '@tanstack/react-router'
import { ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { AskChip } from '@/components/agent-panel'
import { Badge, Chip, Chips } from '@/components/chips'
import { Stat, Stats } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, PrintLink, Screen, SearchIcon, Table, Toolbar, btn } from '@/components/page'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accountTxns, balancesFor, iso, num, periodRange, today, type AccountBalance, type AccountType, type Period } from '@/lib/data'
import { cn } from '@/lib/utils'

const GROUPS: { type: AccountType; simple: string; pro: string }[] = [
  { type: 'asset', simple: 'What you have', pro: 'Assets' },
  { type: 'liability', simple: 'What you owe', pro: 'Liabilities' },
  { type: 'equity', simple: "What's yours", pro: 'Equity' },
  { type: 'revenue', simple: 'Money earned', pro: 'Revenue' },
  { type: 'expense', simple: 'Money spent', pro: 'Expenses' },
]
const groupOf = (a: AccountBalance) => GROUPS.findIndex((g) => g.type === a.account_type)
const typeLabel = (a: AccountBalance) => a.account_type[0].toUpperCase() + a.account_type.slice(1)
const inOrder = (rows: AccountBalance[]) => [...rows].sort((a, b) => groupOf(a) - groupOf(b) || a.code.localeCompare(b.code))

/** Every account as its own card. Choosing one opens its ledger as a full page. */
export function Ledger() {
  const { org, pro } = useApp()
  const list = useQuery(balancesFor(org.id))
  const [search, setSearch] = useState('')
  const [type, setType] = useState('all')
  const [activeOnly, setActiveOnly] = useState(false)
  const all = useMemo(() => inOrder(list.data ?? []), [list.data])
  const isActive = (a: AccountBalance) => num(a.transaction_count) > 0 || num(a.balance) !== 0
  const shown = useMemo(() => {
    const s = search.trim().toLowerCase()
    return all.filter((a) => (type === 'all' || a.account_type === type) && ((pro && !activeOnly) || isActive(a)) && (!s || `${a.code} ${a.name}`.toLowerCase().includes(s)))
  }, [all, type, pro, activeOnly, search])

  return (
    <Screen search={<SearchIcon label="Search accounts" placeholder="Search accounts" value={search} onChange={setSearch} />} title="Ledger" sub={pro ? `${all.length} accounts. Choose one to open its ledger.` : 'Choose an account to see everything that happened on it.'}>
      <Toolbar>
        <Chips label="Account type" value={type} onChange={setType} options={[{ id: 'all', label: 'All', count: all.length }, ...GROUPS.map((g) => ({ id: g.type, label: pro ? g.pro : g.simple, count: all.filter((a) => a.account_type === g.type).length }))]} />
        {pro ? <Chip active={activeOnly} count={all.filter(isActive).length} onClick={() => setActiveOnly((v) => !v)}>With activity</Chip> : null}
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No accounts yet" body="Accounts appear here once your chart of accounts is set up." /> : null)}>
        {() => shown.length === 0 ? <Empty title="No accounts match" body="Try a different word, or another filter." /> : (
          <Paged rows={shown} size={24}>
            {(page, pager) => (
              <>
                {GROUPS.map((g) => {
                  const rows = page.filter((a) => a.account_type === g.type)
                  if (!rows.length) return null
                  return (
                    <section key={g.type} aria-label={pro ? g.pro : g.simple} className="flex flex-col gap-2">
                      <h2 className="text-[12.5px] font-semibold text-muted-foreground">{pro ? g.pro : g.simple}</h2>
                      <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
                        {rows.map((a) => <AccountCard key={a.id} account={a} />)}
                      </div>
                    </section>
                  )
                })}
                {pager ? <div className="sheet overflow-hidden [&>nav]:border-t-0">{pager}</div> : null}
              </>
            )}
          </Paged>
        )}
      </Loaded>
    </Screen>
  )
}

function AccountCard({ account: a }: { account: AccountBalance }) {
  const { org, pro } = useApp()
  const count = num(a.transaction_count)
  return (
    <Link to="/ledger/$accountId" params={{ accountId: String(a.id) }} search={{ range: 'all' }} className="sheet px-3.5 py-2.5 flex flex-col gap-1 hover:bg-accent focus-visible:bg-accent outline-none">
      <span className="flex items-baseline gap-2 min-w-0">
        {pro ? <span className="fig text-[12px] text-muted-foreground shrink-0">{a.code}</span> : null}
        <span className="font-medium truncate">{a.name}</span>
      </span>
      <span className={cn('fig text-[16px] font-medium', num(a.balance) < 0 && 'text-[var(--note)]')}>{figure(num(a.balance), org.decimals)}</span>
      <span className="flex items-center justify-between gap-2 min-h-5">
        <Badge>{count ? `${count} ${count === 1 ? 'entry' : 'entries'}` : 'No activity'}</Badge>
        {a.last_transaction_date ? <span className="text-[12px] text-muted-foreground">{shortDate(a.last_transaction_date)}</span> : null}
      </span>
    </Link>
  )
}

export type LedgerSearch = { range: string; from?: string; to?: string }
const RANGES = [{ id: 'all', label: 'All time' }, { id: 'month', label: 'This month' }, { id: 'quarter', label: 'This quarter' }, { id: 'year', label: 'This year' }, { id: 'custom', label: 'Custom dates' }]

/** One account's figures for a period. Shared by its page and its printable document. */
export function useLedger(accountId: string, search: LedgerSearch) {
  const { org } = useApp()
  const accounts = useQuery(balancesFor(org.id))
  // Always the account's whole history: the opening balance of a period comes from what's before it.
  const txns = useQuery(accountTxns(org.id, accountId))
  const account = accounts.data?.find((a) => String(a.id) === accountId)
  const ordered = useMemo(() => inOrder(accounts.data ?? []), [accounts.data])
  const at = ordered.findIndex((a) => String(a.id) === accountId)
  const { from, to } = search.range === 'custom' ? { from: search.from, to: search.to } : search.range === 'all' ? { from: undefined, to: undefined } : periodRange(search.range as Period)

  // Balances run in the account's natural direction, so the closing figure matches its card.
  const debitNormal = account?.account_type === 'asset' || account?.account_type === 'expense'
  const signed = (debit: number, credit: number) => (debitNormal ? debit - credit : credit - debit)
  const figures = useMemo(() => {
    let running = 0
    let opening = 0
    let debits = 0
    let credits = 0
    const rows = []
    for (const t of txns.data ?? []) {
      const date = t.entry_date.slice(0, 10)
      if (to && date > to) break
      const debit = num(t.debit_amount)
      const credit = num(t.credit_amount)
      running += debitNormal ? debit - credit : credit - debit
      if (from && date < from) { opening = running; continue }
      debits += debit
      credits += credit
      rows.push({ ...t, date, debit, credit, running })
    }
    return { opening, rows, debits, credits, closing: running }
  }, [txns.data, from, to, debitNormal])
  const period = from || to ? `${from ? shortDate(from) : 'Start'} to ${to ? shortDate(to) : shortDate(today())}` : `All time to ${shortDate(today())}`
  return { accounts, account, ordered, at, txns, from, to, signed, debitNormal, period, ...figures }
}

/** One account's ledger on its own page. Printing and exporting start from its document. */
export function LedgerAccount() {
  const { org, pro } = useApp()
  const { accountId } = useParams({ from: '/ledger/$accountId' })
  const search = useSearch({ from: '/ledger/$accountId' })
  const navigate = useNavigate()
  const { accounts, account, ordered, at, txns, from, to, opening, rows, debits, credits, closing, signed, debitNormal, period } = useLedger(accountId, search)
  const [find, setFind] = useState('')

  const term = find.trim().toLowerCase()
  const visible = term ? rows.filter((r) => `${r.entry_number} ${r.description} ${r.reference ?? ''}`.toLowerCase().includes(term)) : rows
  const d = org.decimals
  const setRange = (range: string) => void navigate({ to: '/ledger/$accountId', params: { accountId }, search: range === 'custom' ? { range, from: from ?? iso(new Date(new Date().getFullYear(), 0, 1)), to: to ?? today() } : { range }, replace: true })
  const setDate = (k: 'from' | 'to', v: string) => void navigate({ to: '/ledger/$accountId', params: { accountId }, search: { range: 'custom', from, to, [k]: v || undefined }, replace: true })

  if (accounts.isSuccess && !account) {
    return <Screen title="Ledger"><Empty title="Account not found" body="It may have been removed, or it belongs to another organization." action={<Link to="/ledger" className={cn(btn.plain, 'mt-2')}>All accounts</Link>} /></Screen>
  }
  const step = (other: AccountBalance | undefined, label: string, Icon: typeof ChevronLeft) => (
    other
      ? <Link to="/ledger/$accountId" params={{ accountId: String(other.id) }} search={search} aria-label={`${label}: ${other.name}`} title={other.name} className={cn(btn.plain, 'w-8 px-0')}><Icon className="size-4" /></Link>
      : <span aria-hidden className={cn(btn.plain, 'w-8 px-0 opacity-40 pointer-events-none')}><Icon className="size-4" /></span>
  )

  return (
    <div className="flex flex-col gap-2">
      <Link to="/ledger" className="print:hidden inline-flex items-center gap-1 self-start text-[13px] text-muted-foreground hover:text-foreground"><ArrowLeft className="size-3.5" />All accounts</Link>
      <Screen search={<SearchIcon label="Search this ledger" placeholder="Search this ledger" value={find} onChange={setFind} />}
        title={account?.name ?? 'Ledger'}
        sub={account ? <span className="inline-flex flex-wrap items-center gap-x-2 gap-y-0.5">{pro ? <span className="fig">{account.code}</span> : null}<Badge>{typeLabel(account)}</Badge><span>{period}</span></span> : null}
        actions={<>
          {step(ordered[at - 1], 'Previous account', ChevronLeft)}
          {step(ordered[at + 1], 'Next account', ChevronRight)}
          <PrintLink to={`/print/ledger/${accountId}`} search={search} />
        </>}
      >
        <Toolbar>
          <Chips label="Period" value={search.range} onChange={setRange} options={RANGES} />
          {search.range === 'custom' ? <span className="flex items-center gap-1.5 text-[13px] text-muted-foreground">
            <Input aria-label="From date" type="date" value={from ?? ''} onChange={(e) => setDate('from', e.target.value)} className="h-7 w-[140px]" />
            to
            <Input aria-label="To date" type="date" value={to ?? ''} onChange={(e) => setDate('to', e.target.value)} className="h-7 w-[140px]" />
          </span> : null}
          {account ? <span className="ml-auto"><AskChip prompt={`Explain the activity on my ${account.name} account (code ${account.code}) for ${period}.`}>Explain this account</AskChip></span> : null}
        </Toolbar>
        <Stats cols={2}>
          <Stat label={pro ? 'Opening balance' : 'At the start'} value={figure(opening, d)} />
          <Stat label={pro ? 'Closing balance' : 'At the end'} value={figure(closing, d)} />
          <Stat label={pro ? 'Total debits' : 'Added'} value={figure(pro || debitNormal ? debits : credits, d)} />
          <Stat label={pro ? 'Total credits' : 'Taken out'} value={figure(pro || debitNormal ? credits : debits, d)} />
        </Stats>
        <Loaded query={txns}>
          {() => (
            <Paged rows={visible} size={50}>
              {(page, pager) => {
                const lastPage = !page.length || page[page.length - 1] === visible[visible.length - 1]
                const firstPage = !page.length || page[0] === visible[0]
                const span = pro ? 4 : 2
                return (
                  <Table min={pro ? 760 : 480} footer={pager}>
                    <thead><tr><Head>Date</Head>{pro ? <Head>Entry</Head> : null}<Head>{pro ? 'Description' : 'What happened'}</Head>{pro ? <Head>Reference</Head> : null}{pro ? <><Head right>Debit</Head><Head right>Credit</Head></> : <Head right>Amount</Head>}<Head right>Balance</Head></tr></thead>
                    <tbody>
                      {term || !firstPage ? null : (
                        <tr className="font-medium bg-muted/50">
                          <Cell>{from ? shortDate(from) : ''}</Cell>
                          <td colSpan={pro ? span + 1 : 2} className="px-3.5 py-1.5 border-b border-border">{pro ? 'Opening balance' : 'At the start'}</td>
                          <Cell right>{figure(opening, d)}</Cell>
                        </tr>
                      )}
                      {page.map((r) => {
                        const net = signed(r.debit, r.credit)
                        return (
                          <tr key={r.id} className="hover:bg-accent/50">
                            <Cell className="text-muted-foreground">{shortDate(r.date)}</Cell>
                            {pro ? <Cell className="fig text-[12.5px] text-muted-foreground">{r.entry_number}</Cell> : null}
                            <Cell className="max-w-0 w-full truncate">{r.description || r.entry_number}</Cell>
                            {pro ? <Cell className="text-muted-foreground">{r.reference ?? ''}</Cell> : null}
                            {pro ? <>
                              <Cell right>{r.debit ? figure(r.debit, d) : ''}</Cell>
                              <Cell right>{r.credit ? figure(r.credit, d) : ''}</Cell>
                            </> : <Cell right>{net >= 0 ? '+' : '−'}{figure(Math.abs(net), d)}</Cell>}
                            <Cell right className={r.running < 0 ? 'text-[var(--note)]' : undefined}>{figure(r.running, d)}</Cell>
                          </tr>
                        )
                      })}
                      {term || !lastPage ? null : (
                        <tr className="rule-total">
                          <td colSpan={span} className="px-3.5 py-1.5">{pro ? 'Totals and closing balance' : 'At the end'}</td>
                          {pro ? <>
                            <Cell right className="border-b-0">{figure(debits, d)}</Cell>
                            <Cell right className="border-b-0">{figure(credits, d)}</Cell>
                          </> : <Cell right className="border-b-0">{' '}</Cell>}
                          <Cell right className="border-b-0">{figure(closing, d)}</Cell>
                        </tr>
                      )}
                    </tbody>
                  </Table>
                )
              }}
            </Paged>
          )}
        </Loaded>
        {!rows.length && txns.isSuccess ? <p className="text-[13px] text-muted-foreground">Nothing happened on this account in this period.</p> : null}
      </Screen>
    </div>
  )
}
