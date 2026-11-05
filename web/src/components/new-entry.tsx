import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { createPortal } from 'react-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { ArrowUp, Plus, Sparkles, X } from 'lucide-react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { selectClass } from '@/components/form'
import { btn } from '@/components/page'
import { useAgent } from '@/lib/agent'
import { call, decideProposal, type Proposal } from '@/lib/api'
import { figure, useApp } from '@/lib/boot'
import { accounts, queryClient, refreshBooks, today } from '@/lib/data'
import { cn, PAGE_SIDE } from '@/lib/utils'

type Row = { key: number; account: string; debit: string; credit: string }
export type Draft = { date: string; description: string; lines: { account: string; debit: string; credit: string }[] }
const cents = (s: string) => Math.round((Number(s) || 0) * 100)

/** Direct entry for accountants, and where a person corrects an agent proposal. Debits must equal credits. A section of the main box, not a popup. */
export function NewEntry({ open, onOpenChange, draft, onRecorded }: { open: boolean; onOpenChange: (v: boolean) => void; draft?: Draft; onRecorded?: () => void }) {
  const { org, userId, canSeeBooks } = useApp()
  const { ask, busy, registerEntryForm } = useAgent()
  const [request, setRequest] = useState('')
  // The agent's proposal behind what's in the form, closed once the entry is recorded so it doesn't stay on the to-do list.
  const [fromProposal, setFromProposal] = useState<string | null>(null)
  const chart = useQuery({ ...accounts(org.id), enabled: open })
  const [date, setDate] = useState(today())
  const [description, setDescription] = useState('')
  const [rows, setRows] = useState<Row[]>([])
  const [nextKey, setNextKey] = useState(1)

  useEffect(() => {
    if (!open) return
    const lines = draft?.lines ?? [{ account: '', debit: '', credit: '' }, { account: '', debit: '', credit: '' }]
    setDate(draft?.date ?? today())
    setDescription(draft?.description ?? '')
    setRows(lines.map((l, i) => ({ key: i + 1, ...l })))
    setNextKey(lines.length + 1)
    setRequest('')
    setFromProposal(null)
  }, [open, draft])

  // While this is open, an entry from the agent lands here. Nothing is recorded until the person presses Record entry.
  useEffect(() => {
    if (!open) return
    return registerEntryForm((p: Proposal) => {
      setDate(p.date)
      setDescription(p.description)
      setRows(p.lines.map((l, i) => ({ key: i + 1, account: String(l.account_id), debit: l.debit ? String(l.debit) : '', credit: l.credit ? String(l.credit) : '' })))
      setNextKey(p.lines.length + 1)
      setFromProposal(p.id)
      toast.success('Filled in by the agent. Check it, then record it.')
    })
  }, [open, registerEntryForm])

  const dr = rows.reduce((s, r) => s + cents(r.debit), 0)
  const cr = rows.reduce((s, r) => s + cents(r.credit), 0)
  const filled = rows.filter((r) => r.account && (cents(r.debit) > 0 || cents(r.credit) > 0))
  const problem = !description.trim() ? 'Add a description.'
    : rows.some((r) => !r.account && (cents(r.debit) > 0 || cents(r.credit) > 0)) ? 'Choose an account for every amount.'
    : rows.some((r) => cents(r.debit) > 0 && cents(r.credit) > 0) ? 'A line can be a debit or a credit, not both.'
    : filled.length < 2 ? 'Add at least two lines.'
    : dr !== cr ? `Out of balance by ${figure(Math.abs(dr - cr) / 100, org.decimals)}.`
    : null

  const postable = useMemo(() => (chart.data ?? []).filter((a) => a.is_postable !== false), [chart.data])
  const update = (key: number, patch: Partial<Row>) => setRows((rs) => rs.map((r) => (r.key === key ? { ...r, ...patch } : r)))

  const post = useMutation({
    mutationFn: () => call('DataService', 'createJournalEntry', [
      { organization_id: org.id, entry_number: `JE-${Date.now()}`, entry_date: date, description: description.trim(), reference: null, total_amount: dr / 100, is_posted: true, created_by: userId, posted_by: userId, posted_at: new Date().toISOString() },
      filled.map((r, i) => ({ account_id: Number(r.account), description: null, debit_amount: cents(r.debit) / 100, credit_amount: cents(r.credit) / 100, line_order: i + 1 })),
    ]),
    onSuccess: () => {
      refreshBooks()
      toast.success('Entry recorded')
      if (fromProposal) void decideProposal(org.id, fromProposal, 'discard').catch(() => null).finally(() => void queryClient.invalidateQueries({ queryKey: ['proposals'] }))
      onRecorded?.()
      onOpenChange(false)
    },
    onError: (e: Error) => toast.error(e.message),
  })

  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!problem && !post.isPending) post.mutate()
  }
  const grid = 'grid grid-cols-[minmax(0,1fr)_96px_96px_24px] gap-1.5 items-center'

  // Esc closes this section only, not the agent behind it. An open dropdown handles its own Esc first.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || e.target instanceof HTMLSelectElement || document.querySelector('[data-search-panel]')) return
      e.stopImmediatePropagation()
      onOpenChange(false)
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [open, onOpenChange])

  const slot = open ? document.getElementById(PAGE_SIDE) : null
  if (!slot) return null

  return createPortal(
      <section aria-label={draft ? 'Change this entry' : 'New entry'} className="side-section absolute inset-0 flex flex-col bg-background">
        <header className="shrink-0 flex items-center justify-between gap-3 h-[61px] px-4 border-b border-border">
          <h2 className="text-[20px] leading-tight font-semibold tracking-[-0.018em]">{draft ? 'Change this entry' : 'New entry'}</h2>
          <button type="button" aria-label="Close" onClick={() => onOpenChange(false)} className="press size-8 -mr-1.5 grid place-items-center rounded-[6px] text-muted-foreground cursor-pointer hover:bg-accent hover:text-foreground"><X className="size-4" /></button>
        </header>
        {canSeeBooks ? (
          <form onSubmit={(e) => { e.preventDefault(); if (request.trim() && !busy) { ask(request.trim()); setRequest('') } }} className="composer shrink-0 flex items-center gap-2 h-10 mx-4 mt-3 pl-3 pr-1 rounded-[8px] border border-input bg-card">
            <Sparkles aria-hidden className="size-3.5 shrink-0 text-[var(--c-violet)]" />
            <input aria-label="Describe this entry for the agent" placeholder="Describe it and the agent fills this in" value={request} onChange={(e) => setRequest(e.target.value)} className="flex-1 min-w-0 bg-transparent outline-none text-[16px] sm:text-[13.5px] placeholder:text-muted-foreground" />
            <button type="submit" aria-label="Fill in with the agent" disabled={!request.trim() || busy} className="press fill-cta size-8 shrink-0 grid place-items-center rounded-[6px] cursor-pointer disabled:opacity-40 disabled:pointer-events-none"><ArrowUp className="size-4" /></button>
          </form>
        ) : null}
        <form data-agent-fields onSubmit={submit} className="flex flex-1 min-h-0 flex-col">
          <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain p-4 flex flex-col gap-3">
          <div className="grid sm:grid-cols-[150px_minmax(0,1fr)] gap-2">
            <Input aria-label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} className="fig" />
            <Input autoFocus={!draft} aria-label="Description" placeholder="What happened?" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <div className={cn(grid, 'text-[12px] text-muted-foreground')}><span>Account</span><span className="text-right">Debit</span><span className="text-right">Credit</span><span /></div>
            {rows.map((r) => (
              <div key={r.key} className={cn(grid, 'rise-in')}>
                <select aria-label="Account" value={r.account} onChange={(e) => update(r.key, { account: e.target.value })} className={selectClass}>
                  <option value="">Choose account</option>
                  {postable.map((a) => <option key={a.id} value={String(a.id)}>{a.code} {a.name}</option>)}
                </select>
                <Input aria-label="Debit" inputMode="decimal" value={r.debit} onChange={(e) => update(r.key, { debit: e.target.value })} className="fig text-right h-8" />
                <Input aria-label="Credit" inputMode="decimal" value={r.credit} onChange={(e) => update(r.key, { credit: e.target.value })} className="fig text-right h-8" />
                <button type="button" aria-label="Remove line" disabled={rows.length <= 2} onClick={() => setRows((rs) => rs.filter((x) => x.key !== r.key))} className="size-6 grid place-items-center rounded-[6px] text-muted-foreground cursor-pointer hover:bg-accent hover:text-foreground disabled:opacity-30 disabled:pointer-events-none"><X className="size-3.5" /></button>
              </div>
            ))}
            <button type="button" onClick={() => { setRows((rs) => [...rs, { key: nextKey, account: '', debit: '', credit: '' }]); setNextKey((k) => k + 1) }} className="self-start inline-flex items-center gap-1 text-[13.5px] text-primary font-medium cursor-pointer mt-1"><Plus className="size-3.5" />Add line</button>
          </div>
          </div>
          <div className="shrink-0 flex flex-wrap items-center justify-between gap-3 border-t border-border p-4 pb-[calc(16px+env(safe-area-inset-bottom))]">
            <p className={cn('text-[13.5px]', problem ? 'text-muted-foreground' : 'text-[var(--tick)] font-medium')}>{problem ?? `✓ Balanced at ${figure(dr / 100, org.decimals)}`}</p>
            <button type="submit" disabled={Boolean(problem) || post.isPending} className={btn.primary}>{post.isPending ? 'Recording…' : 'Record entry'}</button>
          </div>
        </form>
      </section>,
    slot,
  )
}
