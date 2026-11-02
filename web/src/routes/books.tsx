import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Download } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { AskLink } from '@/components/agent-panel'
import { NewEntry } from '@/components/new-entry'
import { Cell, Check, Empty, Head, Loaded, Range, Screen, Table, btn } from '@/components/page'
import { figure, shortDate, useApp } from '@/lib/boot'
import { useAgent } from '@/lib/agent'
import { accountTxns, accounts, balanceSheet, balancesFor, journal, num, periodRange, today, trialBalance, type AccountBalance, type AccountType, type Entry, type Id, type Period } from '@/lib/data'
import { cn } from '@/lib/utils'

const nameMap = (rows: { id: Id; code: string; name: string }[] | undefined) => new Map((rows ?? []).map((a) => [String(a.id), a]))

export function Journal() {
  const { org, pro } = useApp()
  const { ask } = useAgent()
  const entries = useQuery(journal(org.id))
  const chart = useQuery(accounts(org.id))
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState<Id | null>(null)
  const [adding, setAdding] = useState(false)
  const names = useMemo(() => nameMap(chart.data), [chart.data])
  const shown = useMemo(() => {
    const s = search.trim().toLowerCase()
    const list = entries.data ?? []
    return s ? list.filter((e) => `${e.entry_number} ${e.description} ${e.reference ?? ''}`.toLowerCase().includes(s)) : list
  }, [entries.data, search])

  return (
    <Screen
      title="Journal"
      sub={pro ? `${entries.data?.length ?? ''} latest entries` : 'Everything that has happened in your business.'}
      actions={pro ? <><a href="/journal" className={btn.plain}>Bulk entry</a><button className={btn.primary} onClick={() => setAdding(true)}>New entry</button></> : undefined}
    >
      {!pro ? (
        <section className="flex flex-wrap gap-x-4 gap-y-1 text-[13.5px]" aria-label="Examples">
          <span className="text-muted-foreground">Try telling me:</span>
          {['I paid rent of 65,000 from the bank', 'A customer paid 40,000 in cash', 'Bought stock for 120,000 on credit'].map((t) => <button key={t} onClick={() => ask(t)} className="text-primary hover:underline cursor-pointer">{t}</button>)}
        </section>
      ) : null}
      <Input aria-label="Search entries" placeholder={pro ? 'Search number, description or reference' : 'Search'} value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
      <Loaded query={entries} empty={(d) => (d.length === 0 ? <Empty title="Nothing recorded yet" body="Tell me what happened in the box below, and I'll prepare it for your approval." /> : null)}>
        {() => shown.length === 0 ? <Empty title="No matches" body="Try a different word." /> : (
          <div className="sheet overflow-hidden">
            {shown.map((e) => <EntryRow key={e.id} entry={e} open={open === e.id} onToggle={() => setOpen(open === e.id ? null : e.id)} names={names} decimals={org.decimals} pro={pro} />)}
          </div>
        )}
      </Loaded>
      <NewEntry open={adding} onOpenChange={setAdding} />
    </Screen>
  )
}

function EntryRow({ entry: e, open, onToggle, names, decimals, pro }: { entry: Entry; open: boolean; onToggle: () => void; names: Map<string, { code: string; name: string }>; decimals: number; pro: boolean }) {
  const name = (id: Id) => names.get(String(id))?.name ?? `Account ${id}`
  const into = e.lines.filter((l) => num(l.debit_amount) > 0).map((l) => name(l.account_id))
  const outOf = e.lines.filter((l) => num(l.credit_amount) > 0).map((l) => name(l.account_id))
  return (
    <div className="border-b border-border last:border-b-0">
      <button onClick={onToggle} aria-expanded={open} className="w-full grid grid-cols-[14px_minmax(0,1fr)_auto] items-baseline gap-3 px-3.5 py-2.5 text-left cursor-pointer hover:bg-accent">
        <ChevronRight className={cn('size-3.5 self-center text-muted-foreground transition-transform duration-100', open && 'rotate-90')} />
        <span className="min-w-0">
          <span className="block truncate">{e.description || 'No description'}</span>
          <span className="block truncate text-[12.5px] text-muted-foreground">
            {shortDate(e.entry_date)}{pro ? <span className="fig"> · {e.entry_number}</span> : outOf.length && into.length ? ` · ${outOf.join(', ')} → ${into.join(', ')}` : ''}
          </span>
        </span>
        <span className="fig">{figure(num(e.total_amount), decimals)}</span>
      </button>
      {open ? (
        <div className="px-3.5 pb-3 pl-[31px] overflow-x-auto">
          <table className="w-full text-[13px] min-w-[360px]">
            <thead><tr className="text-muted-foreground text-left"><th className="font-medium py-1">Account</th><th className="font-medium text-right">Debit</th><th className="font-medium text-right pl-5">Credit</th></tr></thead>
            <tbody>
              {e.lines.map((l) => (
                <tr key={l.id}>
                  <td className="py-0.5 pr-3"><span className="fig text-muted-foreground mr-1.5">{names.get(String(l.account_id))?.code}</span>{name(l.account_id)}</td>
                  <td className="fig text-right whitespace-nowrap">{num(l.debit_amount) ? figure(num(l.debit_amount), decimals) : ''}</td>
                  <td className="fig text-right whitespace-nowrap pl-5">{num(l.credit_amount) ? figure(num(l.credit_amount), decimals) : ''}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="mt-2 text-[13px]"><AskLink prompt={`Explain journal entry ${e.entry_number} ("${e.description}") to me, and whether it looks right.`}>Explain this entry</AskLink></div>
        </div>
      ) : null}
    </div>
  )
}

const RANGES = [{ id: 'all', label: 'All dates' }, { id: 'month', label: 'This month' }, { id: 'quarter', label: 'This quarter' }, { id: 'year', label: 'This year' }]
const GROUPS: { type: AccountType; simple: string; pro: string }[] = [
  { type: 'asset', simple: 'What you have', pro: 'Assets' },
  { type: 'liability', simple: 'What you owe', pro: 'Liabilities' },
  { type: 'equity', simple: "What's yours", pro: 'Equity' },
  { type: 'revenue', simple: 'Money earned', pro: 'Revenue' },
  { type: 'expense', simple: 'Money spent', pro: 'Expenses' },
]

export function Ledger() {
  const { org, pro } = useApp()
  const [range, setRange] = useState('all')
  const dates = range === 'all' ? null : periodRange(range as Period)
  const list = useQuery(balancesFor(org.id, dates?.from, dates?.to))
  const [search, setSearch] = useState('')
  const [picked, setPicked] = useState<AccountBalance | null>(null)
  const shown = useMemo(() => {
    const s = search.trim().toLowerCase()
    const rows = (list.data ?? []).filter((a) => pro || num(a.transaction_count) > 0 || num(a.balance) !== 0)
    return s ? rows.filter((a) => `${a.code} ${a.name}`.toLowerCase().includes(s)) : rows
  }, [list.data, search, pro])
  const current = picked ?? shown.find((a) => num(a.transaction_count) > 0) ?? null

  return (
    <Screen
      title="Ledger"
      sub={pro ? `${list.data?.length ?? ''} accounts` : 'Where your money is, account by account.'}
      actions={<Range label="Date range" value={range} options={RANGES} onChange={setRange} />}
    >
      <Input aria-label="Search accounts" placeholder="Search accounts" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No accounts yet" body="Accounts appear here once your chart of accounts is set up." /> : null)}>
        {() => (
          <div className="grid lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] gap-5 items-start">
            <div className="sheet overflow-hidden">
              {GROUPS.map((g) => {
                const rows = shown.filter((a) => a.account_type === g.type)
                if (!rows.length) return null
                return (
                  <div key={g.type}>
                    <h2 className="px-3.5 pt-3 pb-1 text-[12.5px] font-semibold text-muted-foreground">{pro ? g.pro : g.simple}</h2>
                    {rows.map((a) => (
                      <button key={a.id} aria-pressed={current?.id === a.id} onClick={() => setPicked(a)} className={cn('w-full flex justify-between gap-3 px-3.5 py-1.5 text-left border-b border-border cursor-pointer hover:bg-accent', current?.id === a.id && 'bg-accent')}>
                        <span className="min-w-0 truncate">{pro ? <span className="fig text-[12.5px] text-muted-foreground mr-2">{a.code}</span> : null}{a.name}</span>
                        <span className={cn('fig shrink-0', num(a.balance) < 0 && 'text-[var(--note)]')}>{figure(num(a.balance), org.decimals)}</span>
                      </button>
                    ))}
                  </div>
                )
              })}
            </div>
            <div className="sheet lg:sticky lg:top-8 min-w-0">
              {current ? <>
                <div className="p-4 pb-2.5 border-b border-border flex flex-wrap items-baseline justify-between gap-2">
                  <div className="min-w-0"><h2 className="font-semibold truncate">{current.name}</h2>{pro ? <p className="fig text-[12.5px] text-muted-foreground">{current.code} · {current.account_type}</p> : null}</div>
                  <AskLink className="text-[13.5px]" prompt={`Explain the recent activity on my ${current.name} account (code ${current.code}).`}>Explain this account</AskLink>
                </div>
                <div className="max-h-[60vh] overflow-auto"><AccountDetail id={current.id} from={dates?.from} to={dates?.to} /></div>
              </> : <p className="p-4 text-[13.5px] text-muted-foreground">Select an account to see what happened on it.</p>}
            </div>
          </div>
        )}
      </Loaded>
    </Screen>
  )
}

function AccountDetail({ id, from, to }: { id: Id; from?: string; to?: string }) {
  const { org, pro } = useApp()
  const txns = useQuery(accountTxns(org.id, id, from, to))
  return (
    <Loaded query={txns} empty={(d) => (d.length === 0 ? <p className="p-4 text-[13.5px] text-muted-foreground">Nothing happened on this account in this range.</p> : null)}>
      {(rows) => pro ? (
        <table className="w-full text-[13px] min-w-[420px]">
          <thead><tr><Head>Entry</Head><Head right>Debit</Head><Head right>Credit</Head><Head right>Balance</Head></tr></thead>
          <tbody>
            {rows.map((t) => (
              <tr key={t.id}>
                <Cell><span className="block truncate max-w-[200px]">{t.description || t.entry_number}</span><span className="text-[12px] text-muted-foreground">{shortDate(t.entry_date)}</span></Cell>
                <Cell right>{num(t.debit_amount) ? figure(num(t.debit_amount), org.decimals) : ''}</Cell>
                <Cell right>{num(t.credit_amount) ? figure(num(t.credit_amount), org.decimals) : ''}</Cell>
                <Cell right>{figure(num(t.balance), org.decimals)}</Cell>
              </tr>
            ))}
          </tbody>
        </table>
      ) : (
        <ul>
          {rows.map((t) => {
            const net = num(t.debit_amount) - num(t.credit_amount)
            return (
              <li key={t.id} className="flex justify-between gap-3 px-4 py-2 border-b border-border last:border-b-0">
                <span className="min-w-0"><span className="block truncate">{t.description || t.entry_number}</span><span className="text-[12.5px] text-muted-foreground">{shortDate(t.entry_date)}</span></span>
                <span className="fig shrink-0">{net >= 0 ? '+' : '−'}{figure(Math.abs(net), org.decimals)}</span>
              </li>
            )
          })}
        </ul>
      )}
    </Loaded>
  )
}

export function TrialBalance() {
  const { org, pro } = useApp()
  const rows = useQuery(trialBalance(org.id))
  const sheet = useQuery(balanceSheet(org.id, today()))
  const list = useQuery(balancesFor(org.id))
  const entries = useQuery(journal(org.id))
  const [search, setSearch] = useState('')
  const data = rows.data ?? []
  const dr = data.reduce((s, r) => s + num(r.debit_balance), 0)
  const cr = data.reduce((s, r) => s + num(r.credit_balance), 0)
  const balanced = Math.abs(dr - cr) < 0.005
  const shown = search.trim() ? data.filter((r) => `${r.account_code} ${r.account_name}`.toLowerCase().includes(search.trim().toLowerCase())) : data
  const unusual = (list.data ?? []).filter((a) => num(a.balance) < 0)
  const future = (entries.data ?? []).filter((e) => e.entry_date.slice(0, 10) > today())
  const dupes = useMemo(() => {
    const seen = new Map<string, number>()
    ;(entries.data ?? []).forEach((e) => { const k = `${e.entry_date}|${e.description}|${num(e.total_amount)}`; seen.set(k, (seen.get(k) ?? 0) + 1) })
    return [...seen.values()].filter((n) => n > 1).length
  }, [entries.data])

  const exportCsv = () => {
    const esc = (v: string) => `"${v.replace(/"/g, '""')}"`
    const lines = [['Code', 'Account', 'Type', 'Debit', 'Credit'].join(','), ...data.map((r) => [esc(r.account_code), esc(r.account_name), r.account_type, num(r.debit_balance).toFixed(org.decimals), num(r.credit_balance).toFixed(org.decimals)].join(','))]
    const a = document.createElement('a')
    a.href = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/csv' }))
    a.download = `trial-balance-${today()}.csv`
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const checks = (
    <section className="sheet" aria-label="Book checks">
      <Check ok={balanced} title={balanced ? (pro ? `Debits equal credits at ${figure(dr, org.decimals)}` : 'Everything adds up') : `Out of balance by ${figure(Math.abs(dr - cr), org.decimals)}`} body={pro ? undefined : 'Every amount going out of one place has gone into another.'}>
        {balanced ? null : <AskLink prompt="My trial balance is out of balance. Find out why.">Find out why</AskLink>}
      </Check>
      <Check ok={sheet.data?.isBalanced !== false} title={sheet.data?.isBalanced === false ? "Balance sheet doesn't balance" : 'Balance sheet balances'} body={pro ? undefined : 'What you own equals what you owe plus what is yours.'} />
      <Check ok={unusual.length === 0} title={unusual.length ? `${unusual.length} ${unusual.length === 1 ? 'account looks' : 'accounts look'} unusual` : 'All account balances look normal'} body={unusual.length ? unusual.slice(0, 3).map((a) => a.name).join(', ') : undefined}>
        {unusual.length ? <AskLink prompt={`These accounts have unusual balances: ${unusual.slice(0, 5).map((a) => a.name).join(', ')}. Why, and what should I do?`}>Look into this</AskLink> : null}
      </Check>
      <Check ok={dupes === 0} title={dupes ? `${dupes} possible ${dupes === 1 ? 'duplicate' : 'duplicates'}` : 'No duplicate entries found'} body={dupes ? 'Same date, description and amount.' : `Checked the latest ${entries.data?.length ?? 0} entries.`}>
        {dupes ? <AskLink prompt="Find journal entries that look like duplicates (same date, description and amount) and tell me which to review.">Show me</AskLink> : null}
      </Check>
      <Check ok={future.length === 0} title={future.length ? `${future.length} future-dated ${future.length === 1 ? 'entry' : 'entries'}` : 'No future-dated entries'} />
    </section>
  )

  return (
    <Screen
      title="Trial Balance"
      sub={pro ? `As of ${shortDate(today())}` : 'A check that your books are right.'}
      actions={pro ? <button className={btn.plain} disabled={!data.length} onClick={exportCsv}><Download className="size-3.5 mr-1.5" />Export CSV</button> : undefined}
    >
      {checks}
      {pro ? <>
        <Input aria-label="Search accounts" placeholder="Search accounts" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
        <Loaded query={rows} empty={(d) => (d.length === 0 ? <Empty title="No accounts with balances" body="Balances appear once entries are recorded." /> : null)}>
          {() => (
            <Table>
              <thead><tr><Head>Account</Head><Head right>Debit</Head><Head right>Credit</Head></tr></thead>
              <tbody>
                {shown.map((r) => (
                  <tr key={r.account_id}>
                    <Cell><span className="fig text-[12.5px] text-muted-foreground mr-2">{r.account_code}</span>{r.account_name}</Cell>
                    <Cell right>{num(r.debit_balance) ? figure(num(r.debit_balance), org.decimals) : ''}</Cell>
                    <Cell right>{num(r.credit_balance) ? figure(num(r.credit_balance), org.decimals) : ''}</Cell>
                  </tr>
                ))}
                <tr className="font-semibold">
                  <Cell className="border-b-0">Total</Cell>
                  <Cell right className="border-t border-t-foreground border-b-[3px] border-double border-b-foreground">{figure(dr, org.decimals)}</Cell>
                  <Cell right className="border-t border-t-foreground border-b-[3px] border-double border-b-foreground">{figure(cr, org.decimals)}</Cell>
                </tr>
              </tbody>
            </Table>
          )}
        </Loaded>
      </> : <p><AskLink prompt="Go through my books and tell me if anything looks wrong or needs fixing.">Ask me to review your books in more depth</AskLink></p>}
    </Screen>
  )
}
