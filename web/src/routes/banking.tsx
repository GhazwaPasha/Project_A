import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CheckCircle2, Upload } from 'lucide-react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { AskChip } from '@/components/agent-panel'
import { Badge, Chips } from '@/components/chips'
import { Choice, FormBody, Modal, Stat, Stats, Text, parseCsv, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, Table, Toolbar, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, num, q, refreshBooks, today, type Id } from '@/lib/data'

type Ledger = { id: number; date: string; entry_number: string; description: string; amount: number }
type Line = { id: number; date: string; description: string; reference: string | null; amount: number; status: 'unmatched' | 'matched' | 'ignored'; candidates: Ledger[] }
type Rec = { as_of: string; book_balance: number; lines: Line[]; outstanding: Ledger[]; summary: { outstanding: number; unrecorded: number; reconciled: number; difference: number; balanced: boolean } | null; history: { id: Id; as_of: string; statement_balance: number; completed_at: string }[] }

const REFRESH = ['bank', 'work-summary']

/** Finds the columns of a bank's CSV, whatever each bank calls them. */
export function statementRows(text: string) {
  const find = (row: Record<string, string>, ...names: string[]) => {
    const key = Object.keys(row).find((k) => names.includes(k.trim().toLowerCase()))
    return key ? row[key] : undefined
  }
  return parseCsv(text).map((r) => ({
    date: find(r, 'date', 'transaction date', 'value date', 'posting date') ?? '',
    description: find(r, 'description', 'details', 'narration', 'particulars', 'memo') ?? '',
    reference: find(r, 'reference', 'ref', 'cheque no', 'check number'),
    amount: find(r, 'amount', 'value'),
    debit: find(r, 'debit', 'withdrawal', 'withdrawals', 'money out', 'paid out'),
    credit: find(r, 'credit', 'deposit', 'deposits', 'money in', 'paid in'),
  }))
}

export function Banking() {
  const { org, pro } = useApp()
  const chart = useQuery(accounts(org.id))
  const banks = (chart.data ?? []).filter((a) => a.is_postable !== false && a.account_type === 'asset').sort((a, b) => Number(/bank|cash/i.test(b.name)) - Number(/bank|cash/i.test(a.name)))
  const [picked, setPicked] = useState('')
  const account = picked || (banks[0] ? String(banks[0].id) : '')
  const [asOf, setAsOf] = useState(today())
  const [statement, setStatement] = useState('')
  const [show, setShow] = useState('unmatched')
  const [recording, setRecording] = useState<Line | null>(null)
  const file = useRef<HTMLInputElement>(null)
  const balance = statement.trim() === '' ? null : Number(statement.replace(/,/g, ''))
  const rec = useQuery({ ...q<Rec>(['bank', org.id, account, asOf, balance], 'BooksService', 'getReconciliation', [org.id, Number(account), { as_of: asOf, statement_balance: balance }]), enabled: !!account })
  const imported = useSave((rows: ReturnType<typeof statementRows>) => call<{ added: number; skipped: number }>('BooksService', 'importStatement', [org.id, Number(account), rows]), { refresh: REFRESH, onDone: (r) => toast.success(`${r.added} ${r.added === 1 ? 'line' : 'lines'} added${r.skipped ? `, ${r.skipped} already imported` : ''}`) })
  const match = useSave((v: { line: number; ledger: number }) => call('BooksService', 'matchStatementLine', [org.id, v.line, v.ledger]), { refresh: REFRESH })
  const unmatch = useSave((line: number) => call('BooksService', 'unmatchStatementLine', [org.id, line]), { refresh: REFRESH })
  const ignore = useSave((line: number) => call('BooksService', 'ignoreStatementLine', [org.id, line]), { refresh: REFRESH })
  const finish = useSave(() => call('BooksService', 'completeReconciliation', [org.id, Number(account), { as_of: asOf, statement_balance: balance }]), { success: 'Reconciled', refresh: REFRESH })
  const lines = rec.data?.lines ?? []
  const count = (s: string) => lines.filter((l) => l.status === s).length
  const shown = lines.filter((l) => show === 'all' || l.status === show)
  const s = rec.data?.summary
  const d = org.decimals
  const onFile = async (f: File) => {
    try { imported.mutate(statementRows(await f.text())) } finally { if (file.current) file.current.value = '' }
  }

  return (
    <Screen
      title="Banking"
      sub={pro ? 'Reconcile bank statements against the ledger.' : "Check your books against what the bank says happened."}
      actions={<>
        <input ref={file} aria-label="Bank statement CSV" type="file" accept=".csv,text/csv" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) void onFile(f) }} />
        <button className={btn.primary} disabled={!account || imported.isPending} onClick={() => file.current?.click()}><Upload className="size-3.5 mr-1.5" />{imported.isPending ? 'Importing…' : 'Import statement'}</button>
      </>}
    >
      <Toolbar>
        <label className="flex items-center gap-2 text-[13px]"><span className="text-muted-foreground">Account</span>
          <select value={account} onChange={(e) => setPicked(e.target.value)} className="h-8 rounded-[6px] border border-input bg-card px-2 text-[13px]">{banks.map((a) => <option key={a.id} value={String(a.id)}>{a.code} {a.name}</option>)}</select>
        </label>
        <label className="flex items-center gap-2 text-[13px]"><span className="text-muted-foreground">Statement date</span><Input aria-label="Statement date" type="date" value={asOf} onChange={(e) => setAsOf(e.target.value || today())} className="h-8 w-[150px]" /></label>
        <label className="flex items-center gap-2 text-[13px]"><span className="text-muted-foreground">Statement balance</span><Input aria-label="Statement balance" inputMode="decimal" placeholder="From your statement" value={statement} onChange={(e) => setStatement(e.target.value)} className="h-8 w-[170px] text-right fig" /></label>
        <span className="ml-auto"><AskChip prompt="Look at my bank reconciliation. What is left to sort out, and is anything unusual?">What is left to sort out?</AskChip></span>
      </Toolbar>
      {!account ? <Empty title="No bank account yet" body="Add an asset account for your bank under Accounts, then come back." /> : (
        <Loaded query={rec}>
          {(r) => (
            <>
              <Stats>
                <Stat label={pro ? 'Book balance' : 'Your books say'} value={figure(r.book_balance, d)} />
                <Stat label={pro ? 'Outstanding items' : 'Not at the bank yet'} value={figure(s?.outstanding ?? r.outstanding.reduce((t, l) => t + num(l.amount), 0), d)} />
                <Stat label={pro ? 'Unmatched lines' : 'Bank lines to sort'} value={count('unmatched')} tone={count('unmatched') ? 'warn' : undefined} />
                <Stat label="Difference" value={s ? figure(s.difference, d) : 'Enter balance'} tone={s && s.difference !== 0 ? 'warn' : undefined} />
              </Stats>
              {s ? (
                <div className="sheet px-3.5 py-2.5 flex flex-wrap items-center justify-between gap-3">
                  {s.balanced
                    ? <p className="flex items-center gap-2 font-medium"><CheckCircle2 className="size-4 text-[var(--tick)]" />This matches the statement.</p>
                    : <p className="text-[13.5px] text-muted-foreground">{s.difference !== 0 ? `${figure(Math.abs(s.difference), d)} still doesn't line up.` : 'The amounts line up, but some bank lines still need sorting.'} Match or record the bank lines below.</p>}
                  <button className={btn.primary} disabled={!s.balanced || finish.isPending} onClick={() => finish.mutate()}>Finish reconciliation</button>
                </div>
              ) : null}
              <Toolbar><Chips label="Bank lines" value={show} onChange={setShow} options={[{ id: 'unmatched', label: 'To sort', count: count('unmatched') }, { id: 'matched', label: 'Matched', count: count('matched') }, { id: 'ignored', label: 'Ignored', count: count('ignored') }, { id: 'all', label: 'All', count: lines.length }]} /></Toolbar>
              {lines.length === 0 ? <Empty title="No statement imported" body="Download a CSV from your bank and import it. Importing the same file twice is safe." /> : shown.length === 0 ? <Empty title={show === 'unmatched' ? "You're all caught up" : 'Nothing here'} body={show === 'unmatched' ? 'Every bank line is matched or set aside.' : 'No bank lines in this view.'} /> : (
                <Paged rows={shown}>
                  {(page, pager) => (
                    <Table min={760} footer={pager}>
                      <thead><tr><Head>Date</Head><Head>Bank says</Head><Head right>Amount</Head><Head>{show === 'unmatched' ? 'Could be' : 'Status'}</Head><Head right>{' '}</Head></tr></thead>
                      <tbody>
                        {page.map((l) => (
                          <tr key={l.id}>
                            <Cell className="text-muted-foreground">{shortDate(l.date)}</Cell>
                            <Cell className="max-w-0 w-1/3 truncate">{l.description}</Cell>
                            <Cell right className={l.amount < 0 ? 'text-[var(--note)]' : undefined}>{figure(num(l.amount), d)}</Cell>
                            <Cell>{l.status === 'unmatched'
                              ? (l.candidates.length ? <span className="flex flex-wrap gap-1.5">{l.candidates.map((c) => <button key={c.id} disabled={match.isPending} onClick={() => match.mutate({ line: l.id, ledger: c.id })} title={c.description} className="press inline-flex items-center h-6 px-2 rounded-full border border-input bg-card text-[12px] font-medium cursor-pointer hover:bg-accent">Match {c.entry_number}, {shortDate(c.date)}</button>)}</span> : <span className="text-muted-foreground text-[13px]">Nothing in your books yet</span>)
                              : <Badge dot tone={l.status === 'matched' ? 'good' : 'neutral'}>{l.status === 'matched' ? 'Matched' : 'Ignored'}</Badge>}</Cell>
                            <Cell right className="font-sans">
                              {l.status === 'unmatched'
                                ? <span className="flex justify-end gap-3 text-[13px]"><button onClick={() => setRecording(l)} className="font-medium underline underline-offset-[3px] cursor-pointer">Record</button><button onClick={() => ignore.mutate(l.id)} className="text-muted-foreground underline underline-offset-[3px] cursor-pointer">Ignore</button></span>
                                : <button onClick={() => unmatch.mutate(l.id)} className="text-[13px] text-muted-foreground underline underline-offset-[3px] cursor-pointer">Undo</button>}
                            </Cell>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  )}
                </Paged>
              )}
              {r.outstanding.length ? (
                <section className="flex flex-col gap-2">
                  <h2 className="font-semibold text-[13.5px]">{pro ? 'Outstanding: in the ledger, not on the statement' : "In your books, not at the bank yet"}</h2>
                  <Paged rows={r.outstanding} size={10}>
                    {(page, pager) => (
                      <Table min={520} footer={pager}>
                        <thead><tr><Head>Date</Head><Head>Entry</Head><Head>Description</Head><Head right>Amount</Head></tr></thead>
                        <tbody>{page.map((l) => <tr key={l.id}><Cell className="text-muted-foreground">{shortDate(l.date)}</Cell><Cell className="fig text-[12.5px] text-muted-foreground">{l.entry_number}</Cell><Cell className="max-w-0 w-full truncate">{l.description}</Cell><Cell right>{figure(num(l.amount), d)}</Cell></tr>)}</tbody>
                      </Table>
                    )}
                  </Paged>
                </section>
              ) : null}
            </>
          )}
        </Loaded>
      )}
      {recording ? <RecordLine line={recording} onClose={() => setRecording(null)} /> : null}
    </Screen>
  )
}

/** For something the books don't have yet, like a bank fee. */
function RecordLine({ line, onClose }: { line: Line; onClose: () => void }) {
  const { org } = useApp()
  const chart = useQuery(accounts(org.id))
  const [offset, setOffset] = useState('')
  const [description, setDescription] = useState(line.description)
  const save = useSave(() => call('BooksService', 'createEntryFromStatementLine', [org.id, line.id, { offset_account_id: Number(offset), description }]), { success: 'Recorded and matched', refresh: REFRESH, onDone: () => { refreshBooks(); onClose() } })
  return (
    <Modal open onClose={onClose} title="Record this bank line">
      <FormBody onSubmit={() => save.mutate()} submit="Record" pending={save.isPending} onCancel={onClose} disabled={!offset}>
        <p className="text-[13.5px]"><span className="fig font-medium">{figure(Math.abs(num(line.amount)), org.decimals)}</span> {line.amount < 0 ? 'left' : 'came into'} the bank on {shortDate(line.date)}.</p>
        <Text label="Description" value={description} onChange={setDescription} />
        <Choice label={line.amount < 0 ? 'What was it for?' : 'Where did it come from?'} placeholder="Select account" value={offset} onChange={setOffset} options={(chart.data ?? []).filter((a) => a.is_postable !== false).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))} />
      </FormBody>
    </Modal>
  )
}
