import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { Plus, X } from 'lucide-react'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, useApp } from '@/lib/boot'
import { accounts, refreshBooks, today } from '@/lib/data'
import { cn } from '@/lib/utils'

type Row = { key: number; account: string; debit: string; credit: string }
export type Draft = { date: string; description: string; lines: { account: string; debit: string; credit: string }[] }
const cents = (s: string) => Math.round((Number(s) || 0) * 100)

/** Direct entry for accountants, and where a person corrects an agent proposal. Debits must equal credits. */
export function NewEntry({ open, onOpenChange, draft, onRecorded }: { open: boolean; onOpenChange: (v: boolean) => void; draft?: Draft; onRecorded?: () => void }) {
  const { org } = useApp()
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
  }, [open, draft])

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
      { organization_id: org.id, entry_number: `JE-${Date.now()}`, entry_date: date, description: description.trim(), reference: null, total_amount: dr / 100, is_posted: true, created_by: null, posted_by: null, posted_at: new Date().toISOString() },
      filled.map((r, i) => ({ account_id: Number(r.account), description: null, debit_amount: cents(r.debit) / 100, credit_amount: cents(r.credit) / 100, line_order: i + 1 })),
    ]),
    onSuccess: () => {
      refreshBooks()
      toast.success('Entry recorded')
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[640px] max-h-[90dvh] overflow-y-auto">
        <DialogHeader><DialogTitle>{draft ? 'Change this entry' : 'New entry'}</DialogTitle></DialogHeader>
        <form onSubmit={submit} className="flex flex-col gap-3">
          <div className="grid sm:grid-cols-[150px_minmax(0,1fr)] gap-2">
            <Input aria-label="Date" type="date" value={date} onChange={(e) => setDate(e.target.value)} className="fig" />
            <Input aria-label="Description" placeholder="What happened?" value={description} onChange={(e) => setDescription(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <div className={cn(grid, 'text-[12px] text-muted-foreground')}><span>Account</span><span className="text-right">Debit</span><span className="text-right">Credit</span><span /></div>
            {rows.map((r) => (
              <div key={r.key} className={grid}>
                <select aria-label="Account" value={r.account} onChange={(e) => update(r.key, { account: e.target.value })} className="h-8 min-w-0 w-full rounded-[var(--radius)] border border-input bg-transparent px-2 text-[13.5px]">
                  <option value="">Choose account</option>
                  {postable.map((a) => <option key={a.id} value={String(a.id)}>{a.code} {a.name}</option>)}
                </select>
                <Input aria-label="Debit" inputMode="decimal" value={r.debit} onChange={(e) => update(r.key, { debit: e.target.value })} className="fig text-right h-8" />
                <Input aria-label="Credit" inputMode="decimal" value={r.credit} onChange={(e) => update(r.key, { credit: e.target.value })} className="fig text-right h-8" />
                <button type="button" aria-label="Remove line" disabled={rows.length <= 2} onClick={() => setRows((rs) => rs.filter((x) => x.key !== r.key))} className="grid place-items-center text-muted-foreground cursor-pointer disabled:opacity-30"><X className="size-3.5" /></button>
              </div>
            ))}
            <button type="button" onClick={() => { setRows((rs) => [...rs, { key: nextKey, account: '', debit: '', credit: '' }]); setNextKey((k) => k + 1) }} className="self-start inline-flex items-center gap-1 text-[13.5px] text-primary font-medium cursor-pointer mt-1"><Plus className="size-3.5" />Add line</button>
          </div>
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-border pt-3">
            <p className={cn('text-[13.5px]', problem ? 'text-muted-foreground' : 'text-[var(--tick)] font-medium')}>{problem ?? `✓ Balanced at ${figure(dr / 100, org.decimals)}`}</p>
            <button type="submit" disabled={Boolean(problem) || post.isPending} className={btn.primary}>{post.isPending ? 'Recording…' : 'Record entry'}</button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
