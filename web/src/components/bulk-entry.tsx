import { useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Modal, download, parseCsv, useSave } from '@/components/form'
import { Cell, Head, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, refreshBooks, type Id } from '@/lib/data'

type Row = { line: number; date: string; description: string; debit: Id; credit: Id; debitName: string; creditName: string; amount: number }
const TEMPLATE = 'Date,Description,Debit Account,Credit Account,Amount\n2026-01-31,Shop rent,6200,1010,65000\n'

/** Records many two-line entries from a CSV, checking every row before anything is posted. */
export function BulkEntry({ open, onClose }: { open: boolean; onClose: () => void }) {
  const { org, userId } = useApp()
  const chart = useQuery({ ...accounts(org.id), enabled: open })
  const input = useRef<HTMLInputElement>(null)
  const [rows, setRows] = useState<Row[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const reset = () => { setRows([]); setErrors([]); if (input.current) input.current.value = '' }
  const close = () => { reset(); onClose() }

  const read = async (file: File) => {
    const postable = (chart.data ?? []).filter((a) => a.is_postable !== false)
    const find = (v: string) => postable.find((a) => a.code.toLowerCase() === v.toLowerCase() || a.name.toLowerCase() === v.toLowerCase())
    const found: Row[] = []
    const bad: string[] = []
    const parsed = parseCsv(await file.text())
    parsed.forEach((r, i) => {
      const line = i + 2
      const debit = find(r['Debit Account'] ?? '')
      const credit = find(r['Credit Account'] ?? '')
      const amount = Number((r.Amount ?? '').replace(/,/g, ''))
      if (!/^\d{4}-\d{2}-\d{2}$/.test(r.Date ?? '')) return void bad.push(`Line ${line}: Date must look like 2026-01-31.`)
      if (!r.Description) return void bad.push(`Line ${line}: Description is required.`)
      if (!debit) return void bad.push(`Line ${line}: debit account "${r['Debit Account'] ?? ''}" was not found.`)
      if (!credit) return void bad.push(`Line ${line}: credit account "${r['Credit Account'] ?? ''}" was not found.`)
      if (String(debit.id) === String(credit.id)) return void bad.push(`Line ${line}: debit and credit accounts must differ.`)
      if (!(amount > 0)) return void bad.push(`Line ${line}: Amount must be above zero.`)
      found.push({ line, date: r.Date, description: r.Description, debit: debit.id, credit: credit.id, debitName: debit.name, creditName: credit.name, amount })
    })
    setRows(found)
    setErrors(parsed.length ? bad : ['No rows found. The file needs a header line and at least one entry.'])
  }

  const post = useSave(async () => {
    const failed: string[] = []
    let done = 0
    for (const [i, r] of rows.entries()) {
      try {
        await call('DataService', 'createJournalEntry', [
          { organization_id: org.id, entry_number: `JE-${Date.now()}-${i + 1}`, entry_date: r.date, description: r.description, reference: null, total_amount: r.amount, is_posted: true, created_by: userId, posted_by: userId, posted_at: new Date().toISOString() },
          [
            { account_id: Number(r.debit), description: null, debit_amount: r.amount, credit_amount: 0, line_order: 1 },
            { account_id: Number(r.credit), description: null, debit_amount: 0, credit_amount: r.amount, line_order: 2 },
          ],
        ])
        done++
      } catch (e) {
        failed.push(`Line ${r.line}: ${e instanceof Error ? e.message : 'could not be recorded'}`)
      }
    }
    return { done, failed }
  }, { refresh: [], onDone: ({ done, failed }) => {
    refreshBooks()
    if (done) toast.success(`${done} ${done === 1 ? 'entry' : 'entries'} recorded`)
    if (failed.length) { setRows([]); setErrors(failed) } else close()
  } })

  return (
    <Modal wide open={open} onClose={close} title="Bulk entry">
      <div className="flex flex-col gap-3 min-w-0">
        <p className="text-[13.5px] text-muted-foreground">Upload a CSV with Date, Description, Debit Account, Credit Account and Amount. Accounts can be a code or a name. <button type="button" onClick={() => download('bulk-entry-template.csv', TEMPLATE)} className="text-foreground font-medium underline underline-offset-[3px] cursor-pointer">Download a template</button></p>
        <input ref={input} aria-label="CSV file" type="file" accept=".csv,text/csv" disabled={!chart.data} onChange={(e) => { const f = e.target.files?.[0]; if (f) void read(f) }} className="text-[13px]" />
        {errors.length ? <ul role="alert" className="text-[13px] text-destructive flex flex-col gap-0.5 max-h-36 overflow-y-auto">{errors.map((e) => <li key={e}>{e}</li>)}</ul> : null}
        {rows.length ? (
          <div className="border border-border rounded-[8px] overflow-auto max-h-[40dvh]">
            <table className="w-full text-[13px] min-w-[620px]">
              <thead><tr><Head>Date</Head><Head>Description</Head><Head>Debit</Head><Head>Credit</Head><Head right>Amount</Head></tr></thead>
              <tbody>{rows.map((r) => <tr key={r.line}><Cell className="whitespace-nowrap text-muted-foreground">{shortDate(r.date)}</Cell><Cell>{r.description}</Cell><Cell>{r.debitName}</Cell><Cell>{r.creditName}</Cell><Cell right>{figure(r.amount, org.decimals)}</Cell></tr>)}</tbody>
            </table>
          </div>
        ) : null}
        <div className="flex justify-end gap-2">
          <button className={btn.plain} onClick={close}>Close</button>
          <button className={btn.primary} disabled={!rows.length || post.isPending} onClick={() => post.mutate()}>{post.isPending ? 'Recording…' : rows.length ? `Record ${rows.length} ${rows.length === 1 ? 'entry' : 'entries'}` : 'Record'}</button>
        </div>
      </div>
    </Modal>
  )
}
