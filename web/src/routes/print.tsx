import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link, useParams, useSearch } from '@tanstack/react-router'
import { ArrowLeft, Download, Printer } from 'lucide-react'
import { download } from '@/components/form'
import { Empty, btn } from '@/components/page'
import { figure, shortDate, useApp } from '@/lib/boot'
import { balanceSheet, incomeStatement, num, periodRange, q, today, trialBalance, type Money, type Section } from '@/lib/data'
import { useLedger } from '@/routes/ledger'
import { statusBadge, type Doc } from '@/routes/documents'
import { AGE_COLUMNS, type Aged } from '@/routes/reports'

type Csv = (string | number)[][]

const cell = (v: string | number) => {
  const s = String(v)
  // A leading = or + would run as a formula in a spreadsheet.
  return `"${(typeof v === 'string' && /^[=+\-@]/.test(s) ? `'${s}` : s).replace(/"/g, '""')}"`
}

/** A report on its own page, laid out like the paper it prints to. Printing and exporting both start here. */
function PrintDoc({ title, heading, period, back, file, csv, children }: { title: string; heading?: string; period: string; back: { to: string; search?: Record<string, unknown>; label: string }; file: string; csv: Csv | null; children: ReactNode }) {
  const { org, email, canSeeBooks } = useApp()
  const company = org.settings?.companyInfo
  const address = company ? [company.address.street, company.address.city, company.address.state, company.address.country].filter(Boolean).join(', ') : ''
  const print = () => {
    // A browser names a saved PDF after the page title.
    const before = document.title
    document.title = file
    window.print()
    document.title = before
  }
  const exportCsv = () => {
    const rows: Csv = [['Organization', org.name], ['Report', heading ? `${title}: ${heading}` : title], ['Period', period], ['Currency', org.currency], [], ...(csv ?? [])]
    download(`${file}.csv`, rows.map((r) => r.map(cell).join(',')).join('\n'))
  }
  if (!canSeeBooks) return <main className="p-6"><Empty title="Your role does not include this" body="Ask the organization owner for access." /></main>

  return (
    <div className="min-h-dvh print:min-h-0">
      <header className="print:hidden sticky top-0 z-10 flex flex-wrap items-center gap-2 px-4 py-2 border-b border-border bg-card">
        <Link to={back.to} search={back.search as never} className={btn.plain}><ArrowLeft className="size-3.5 mr-1.5" />{back.label}</Link>
        <p className="min-w-0 truncate font-medium text-[13.5px] mx-1">{heading ?? title}</p>
        <span className="ml-auto flex gap-2">
          <button className={btn.plain} disabled={!csv} onClick={exportCsv}><Download className="size-3.5 mr-1.5" />Export CSV</button>
          <button className={btn.primary} disabled={!csv} onClick={print}><Printer className="size-3.5 mr-1.5" />Print or save PDF</button>
        </span>
      </header>
      <div className="px-3 py-5 overflow-x-auto print:p-0 print:overflow-visible">
        <main className="doc mx-auto w-[210mm] min-h-[297mm] p-[13mm] shadow-[0_2px_16px_rgb(0_0_0/0.18)] print:w-full print:min-h-0 print:p-0 print:shadow-none">
          <div className="flex justify-between gap-6 pb-3 mb-4 border-b-2 border-black">
            <div className="min-w-0">
              <p className="text-[15px] font-bold">{org.name}</p>
              {company?.legalName && company.legalName !== org.name ? <p className="doc-muted">{company.legalName}</p> : null}
              {address ? <p className="doc-muted">{address}</p> : null}
              {company?.taxId ? <p className="doc-muted">Tax ID {company.taxId}</p> : null}
            </div>
            <div className="text-right shrink-0">
              <p className="text-[15px] font-bold">{title}</p>
              {heading ? <p className="font-semibold">{heading}</p> : null}
              <p className="doc-muted">{period}</p>
              <p className="doc-muted">{org.currency}</p>
            </div>
          </div>
          {csv ? children : <p className="doc-muted py-8 text-center">Preparing the report…</p>}
          <p className="doc-muted mt-5 pt-2 border-t border-[#c8ccd2] text-[10.5px]">Printed {shortDate(today())} by {email}</p>
        </main>
      </div>
    </div>
  )
}

const Num = ({ v, d, strong }: { v: Money; d: number; strong?: boolean }) => <td className={strong ? 'num font-semibold' : 'num'}>{figure(num(v), d)}</td>

export function LedgerDoc() {
  const { org, pro } = useApp()
  const { accountId } = useParams({ from: '/print/ledger/$accountId' })
  const search = useSearch({ from: '/print/ledger/$accountId' })
  const { account, txns, opening, rows, debits, credits, closing, signed, debitNormal, period } = useLedger(accountId, search)
  const d = org.decimals
  const n = (v: number) => v.toFixed(d)
  const ready = account && txns.isSuccess
  const csv: Csv | null = ready ? [
    ['Date', 'Entry', 'Description', 'Reference', 'Debit', 'Credit', 'Balance'],
    ['', '', 'Opening balance', '', '', '', n(opening)],
    ...rows.map((r) => [r.date, r.entry_number, r.description ?? '', r.reference ?? '', r.debit ? n(r.debit) : '', r.credit ? n(r.credit) : '', n(r.running)]),
    ['', '', 'Totals and closing balance', '', n(debits), n(credits), n(closing)],
  ] : null
  return (
    <PrintDoc title="General Ledger" heading={account ? `${account.code} ${account.name}` : undefined} period={period} file={`Ledger ${account?.code ?? ''} ${account?.name ?? ''}`.trim()} back={{ to: `/ledger/${accountId}`, search, label: 'Back to ledger' }} csv={csv}>
      <dl className="grid grid-cols-2 border border-[#c8ccd2] mb-4 [&>div]:px-3 [&>div]:py-2 [&>div:nth-child(odd)]:border-r [&>div:nth-child(-n+2)]:border-b [&>div]:border-[#c8ccd2]">
        <div><dt className="doc-muted">{pro ? 'Opening balance' : 'At the start'}</dt><dd className="fig text-[13px] font-semibold">{figure(opening, d)}</dd></div>
        <div><dt className="doc-muted">{pro ? 'Closing balance' : 'At the end'}</dt><dd className="fig text-[13px] font-semibold">{figure(closing, d)}</dd></div>
        <div><dt className="doc-muted">{pro ? 'Total debits' : 'Added'}</dt><dd className="fig text-[13px] font-semibold">{figure(pro || debitNormal ? debits : credits, d)}</dd></div>
        <div><dt className="doc-muted">{pro ? 'Total credits' : 'Taken out'}</dt><dd className="fig text-[13px] font-semibold">{figure(pro || debitNormal ? credits : debits, d)}</dd></div>
      </dl>
      <table className="doc-table">
        <thead><tr><th>Date</th>{pro ? <th>Entry</th> : null}<th>{pro ? 'Description' : 'What happened'}</th>{pro ? <><th>Reference</th><th className="num">Debit</th><th className="num">Credit</th></> : <th className="num">Amount</th>}<th className="num">Balance</th></tr></thead>
        <tbody>
          <tr className="sub"><td colSpan={pro ? 6 : 3}>{pro ? 'Opening balance' : 'At the start'}</td><Num v={opening} d={d} /></tr>
          {rows.map((r) => {
            const net = signed(r.debit, r.credit)
            return (
              <tr key={r.id}>
                <td className="whitespace-nowrap">{shortDate(r.date)}</td>
                {pro ? <td className="fig whitespace-nowrap">{r.entry_number}</td> : null}
                <td>{r.description || r.entry_number}</td>
                {pro ? <>
                  <td>{r.reference ?? ''}</td>
                  <td className="num">{r.debit ? figure(r.debit, d) : ''}</td>
                  <td className="num">{r.credit ? figure(r.credit, d) : ''}</td>
                </> : <td className="num">{net >= 0 ? '+' : '−'}{figure(Math.abs(net), d)}</td>}
                <Num v={r.running} d={d} />
              </tr>
            )
          })}
          <tr className="total">
            <td colSpan={pro ? 4 : 3}>{pro ? 'Totals and closing balance' : 'At the end'}</td>
            {pro ? <><Num v={debits} d={d} /><Num v={credits} d={d} /></> : null}
            <Num v={closing} d={d} />
          </tr>
        </tbody>
      </table>
    </PrintDoc>
  )
}

export function IncomeDoc() {
  const { org, pro } = useApp()
  const { period } = useSearch({ from: '/print/income-statement' })
  const { from, to } = periodRange(period)
  const r = useQuery(incomeStatement(org.id, from, to)).data
  const d = org.decimals
  const groups = r ? [
    { lines: r.revenue.breakdown, sign: 1, sub: [pro ? 'Total revenue' : 'Total sales', r.revenue.total] as const },
    { lines: r.costOfSales.breakdown, sign: -1, sub: [pro ? 'Gross profit' : 'Left after the cost of what you sold', r.grossProfit] as const },
    { lines: [...r.operatingExpenses.breakdown, ...r.otherExpenses.breakdown], sign: -1, sub: null },
  ] : []
  const csv: Csv | null = r ? [['Item', 'Amount'], ...groups.flatMap((g) => [...g.lines.map((l): (string | number)[] => [l.account, (g.sign * Math.abs(num(l.amount))).toFixed(d)]), ...(g.sub ? [[g.sub[0], num(g.sub[1]).toFixed(d)]] : [])]), [pro ? 'Net income' : 'Profit', num(r.netIncome).toFixed(d)]] : null
  return (
    <PrintDoc title={pro ? 'Income Statement' : 'Profit'} period={`${shortDate(from)} to ${shortDate(to)}`} file={`Income Statement ${from} to ${to}`} back={{ to: '/reports/income-statement', search: { period }, label: 'Back to report' }} csv={csv}>
      <table className="doc-table">
        <thead><tr><th>{pro ? 'Account' : 'Item'}</th><th className="num">{org.currency}</th></tr></thead>
        <tbody>
          {groups.map((g, i) => [
            ...g.lines.map((l) => <tr key={`${i}-${l.account}`}><td>{l.account}</td><td className="num">{figure(g.sign * Math.abs(num(l.amount)), d)}</td></tr>),
            g.sub ? <tr key={`sub-${i}`} className="sub"><td>{g.sub[0]}</td><Num v={g.sub[1]} d={d} /></tr> : null,
          ])}
          {r ? <tr className="total"><td>{pro ? 'Net income' : 'Profit'}</td><Num v={r.netIncome} d={d} /></tr> : null}
        </tbody>
      </table>
    </PrintDoc>
  )
}

export function BalanceDoc() {
  const { org, pro } = useApp()
  const asOf = today()
  const r = useQuery(balanceSheet(org.id, asOf)).data
  const d = org.decimals
  const groups: [string, Section[], Money][] = r ? [
    [pro ? 'Assets' : 'What you own', r.assetSections, r.totalAssets],
    [pro ? 'Liabilities' : 'What you owe', r.liabilitySections, r.totalLiabilities],
    [pro ? 'Equity' : "What's yours", r.equitySections, r.totalEquity],
  ] : []
  const both = r ? num(r.totalLiabilities) + num(r.totalEquity) : 0
  const bothLabel = pro ? 'Total liabilities and equity' : 'Owed plus yours'
  const csv: Csv | null = r ? [['Item', 'Amount'], ...groups.flatMap(([title, sections, total]) => [[title, ''], ...sections.flatMap((s) => s.accounts).map((a): (string | number)[] => [a.name, num(a.balance).toFixed(d)]), [`Total ${title.toLowerCase()}`, num(total).toFixed(d)]]), [bothLabel, both.toFixed(d)]] : null
  return (
    <PrintDoc title={pro ? 'Balance Sheet' : 'What you own and owe'} period={`As of ${shortDate(asOf)}`} file={`Balance Sheet ${asOf}`} back={{ to: '/reports/balance-sheet', label: 'Back to report' }} csv={csv}>
      <table className="doc-table">
        <thead><tr><th>{pro ? 'Account' : 'Item'}</th><th className="num">{org.currency}</th></tr></thead>
        <tbody>
          {groups.map(([title, sections, total]) => [
            <tr key={title} className="group"><td colSpan={2}>{title}</td></tr>,
            ...sections.flatMap((s) => s.accounts).map((a) => <tr key={a.id}><td>{a.name}</td><Num v={a.balance} d={d} /></tr>),
            <tr key={`${title}-total`} className="sub"><td>Total {title.toLowerCase()}</td><Num v={total} d={d} /></tr>,
          ])}
          {r ? <tr className="total"><td>{bothLabel}</td><Num v={both} d={d} /></tr> : null}
        </tbody>
      </table>
    </PrintDoc>
  )
}

export function TrialDoc() {
  const { org } = useApp()
  const asOf = today()
  const rows = useQuery(trialBalance(org.id)).data
  const d = org.decimals
  const dr = (rows ?? []).reduce((s, r) => s + num(r.debit_balance), 0)
  const cr = (rows ?? []).reduce((s, r) => s + num(r.credit_balance), 0)
  const csv: Csv | null = rows ? [['Code', 'Account', 'Type', 'Debit', 'Credit'], ...rows.map((r): (string | number)[] => [r.account_code, r.account_name, r.account_type, num(r.debit_balance).toFixed(d), num(r.credit_balance).toFixed(d)]), ['', 'Total', '', dr.toFixed(d), cr.toFixed(d)]] : null
  return (
    <PrintDoc title="Trial Balance" period={`As of ${shortDate(asOf)}`} file={`Trial Balance ${asOf}`} back={{ to: '/trial-balance', label: 'Back to trial balance' }} csv={csv}>
      <table className="doc-table">
        <thead><tr><th>Code</th><th>Account</th><th className="num">Debit</th><th className="num">Credit</th></tr></thead>
        <tbody>
          {(rows ?? []).map((r) => <tr key={r.account_id}><td className="fig">{r.account_code}</td><td>{r.account_name}</td><td className="num">{num(r.debit_balance) ? figure(num(r.debit_balance), d) : ''}</td><td className="num">{num(r.credit_balance) ? figure(num(r.credit_balance), d) : ''}</td></tr>)}
          <tr className="total"><td colSpan={2}>Total</td><Num v={dr} d={d} /><Num v={cr} d={d} /></tr>
        </tbody>
      </table>
    </PrintDoc>
  )
}

export function DocumentDoc() {
  const { org } = useApp()
  const { documentId } = useParams({ from: '/print/document/$documentId' })
  const doc = useQuery(q<Doc>(['document', documentId], 'BooksService', 'getDocument', [org.id, Number(documentId)])).data
  const d = org.decimals
  const invoice = doc?.kind !== 'bill'
  const n = (v: number) => num(v).toFixed(d)
  const csv: Csv | null = doc ? [
    ['Number', doc.number], [invoice ? 'Customer' : 'Supplier', doc.party_name], ['Date', doc.issue_date.slice(0, 10)], ['Due', doc.due_date.slice(0, 10)], ['Status', statusBadge(doc).label], [],
    ['Description', 'Quantity', 'Price', 'Tax', 'Amount'],
    ...doc.lines.map((l): (string | number)[] => [l.description, num(l.quantity), n(l.unit_price), l.tax_name ?? '', n(l.amount)]),
    ['', '', '', 'Subtotal', n(doc.subtotal)], ['', '', '', 'Tax', n(doc.tax_total)], ['', '', '', 'Total', n(doc.total)], ['', '', '', 'Balance due', n(doc.balance)],
  ] : null
  return (
    <PrintDoc title={invoice ? 'Invoice' : 'Bill'} heading={doc?.number} period={doc ? `${shortDate(doc.issue_date)}, due ${shortDate(doc.due_date)}` : ''} file={doc ? `${invoice ? 'Invoice' : 'Bill'} ${doc.number}` : 'Document'} back={{ to: invoice ? '/invoices' : '/bills', label: `Back to ${invoice ? 'invoices' : 'bills'}` }} csv={csv}>
      {doc ? <>
        <div className="mb-4"><p className="doc-muted">{invoice ? 'Bill to' : 'From'}</p><p className="text-[13px] font-semibold">{doc.party_name}</p>{doc.status === 'void' ? <p className="font-bold">VOID{doc.void_reason ? `: ${doc.void_reason}` : ''}</p> : doc.status === 'draft' ? <p className="font-bold">DRAFT</p> : null}</div>
        <table className="doc-table">
          <thead><tr><th>Description</th><th className="num">Qty</th><th className="num">Price</th><th>Tax</th><th className="num">Amount</th></tr></thead>
          <tbody>
            {doc.lines.map((l) => <tr key={l.id}><td>{l.description}</td><td className="num">{num(l.quantity)}</td><td className="num">{figure(num(l.unit_price), d)}</td><td>{l.tax_name ?? ''}</td><Num v={l.amount} d={d} /></tr>)}
            <tr><td colSpan={4} className="text-right">Subtotal</td><Num v={doc.subtotal} d={d} /></tr>
            <tr><td colSpan={4} className="text-right">Tax</td><Num v={doc.tax_total} d={d} /></tr>
            <tr className="total"><td colSpan={4} className="text-right">Total ({org.currency})</td><Num v={doc.total} d={d} /></tr>
            {num(doc.amount_paid) ? <><tr><td colSpan={4} className="text-right">Paid</td><Num v={doc.amount_paid} d={d} /></tr><tr className="sub"><td colSpan={4} className="text-right">Balance due</td><Num v={doc.balance} d={d} /></tr></> : null}
          </tbody>
        </table>
        {doc.notes ? <p className="mt-4">{doc.notes}</p> : null}
      </> : null}
    </PrintDoc>
  )
}

function AgedDoc({ kind }: { kind: 'invoice' | 'bill' }) {
  const { org, pro } = useApp()
  const a = useQuery(q<Aged>(['aged', org.id, kind, 'print'], 'BooksService', 'getAgedReport', [org.id, kind])).data
  const d = org.decimals
  const title = kind === 'invoice' ? (pro ? 'Aged Receivables' : 'Who owes you') : (pro ? 'Aged Payables' : 'Who you owe')
  const csv: Csv | null = a ? [[kind === 'invoice' ? 'Customer' : 'Supplier', ...AGE_COLUMNS.map(([, l]) => l)], ...[...a.rows, a.totals].map((r): (string | number)[] => [r.party_name, ...AGE_COLUMNS.map(([k]) => num(r[k]).toFixed(d))])] : null
  return (
    <PrintDoc title={title} period={`As of ${shortDate(a?.as_of ?? today())}`} file={`${title} ${today()}`} back={{ to: kind === 'invoice' ? '/reports/aged-receivables' : '/reports/aged-payables', label: 'Back to report' }} csv={csv}>
      <table className="doc-table">
        <thead><tr><th>{kind === 'invoice' ? 'Customer' : 'Supplier'}</th>{AGE_COLUMNS.map(([k, l]) => <th key={k} className="num">{l}</th>)}</tr></thead>
        <tbody>
          {a?.rows.map((r) => <tr key={r.party_name}><td>{r.party_name}</td>{AGE_COLUMNS.map(([k]) => <td key={k} className="num">{r[k] ? figure(num(r[k]), d) : ''}</td>)}</tr>)}
          {a ? <tr className="total"><td>Total</td>{AGE_COLUMNS.map(([k]) => <Num key={k} v={a.totals[k]} d={d} />)}</tr> : null}
        </tbody>
      </table>
    </PrintDoc>
  )
}
export const AgedReceivablesDoc = () => <AgedDoc kind="invoice" />
export const AgedPayablesDoc = () => <AgedDoc kind="bill" />
