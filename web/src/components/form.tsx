import { useState, type FormEvent, type ReactNode } from 'react'
import { useMutation } from '@tanstack/react-query'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { btn } from '@/components/page'
import { queryClient } from '@/lib/data'
import { cn } from '@/lib/utils'

export function Field({ label, hint, children, className }: { label: string; hint?: string; children: ReactNode; className?: string }) {
  return (
    <label className={cn('flex flex-col gap-1.5 text-[13px] font-medium min-w-0', className)}>
      {label}
      {children}
      {hint ? <span className="text-[12px] font-normal text-muted-foreground">{hint}</span> : null}
    </label>
  )
}

export function Text({ label, hint, value, onChange, className, ...rest }: { label: string; hint?: string; value: string | number | null | undefined; onChange: (v: string) => void; className?: string } & Omit<React.ComponentProps<typeof Input>, 'value' | 'onChange' | 'className'>) {
  return <Field label={label} hint={hint} className={className}><Input value={value ?? ''} onChange={(e) => onChange(e.target.value)} {...rest} /></Field>
}

/** Every dropdown in the app: same height, radius, type and chevron. `selectInline` sits inside a table row. */
export const selectClass = 'select-pick h-8 w-full min-w-0 text-[13.5px]'
export const selectInline = 'select-pick h-7 text-[13px]'

export function Choice({ label, hint, value, onChange, options, placeholder, required, className }: { label: string; hint?: string; value: string | number | null | undefined; onChange: (v: string) => void; options: { value: string | number; label: string }[]; placeholder?: string; required?: boolean; className?: string }) {
  return (
    <Field label={label} hint={hint} className={className}>
      <select value={value ?? ''} required={required} onChange={(e) => onChange(e.target.value)} className={selectClass}>
        {placeholder !== undefined ? <option value="">{placeholder}</option> : null}
        {options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </Field>
  )
}

export function Toggle({ label, hint, checked, onChange }: { label: string; hint?: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex items-start gap-3 cursor-pointer">
      <Switch checked={checked} onCheckedChange={onChange} className="mt-0.5" />
      <span><span className="font-medium text-[13.5px] block">{label}</span>{hint ? <span className="text-[12.5px] text-muted-foreground">{hint}</span> : null}</span>
    </label>
  )
}

export function Modal({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean }) {
  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) onClose() }}>
      <DialogContent className={cn('max-h-[90dvh] overflow-y-auto', wide ? 'sm:max-w-[760px]' : 'sm:max-w-[520px]')}>
        <DialogHeader><DialogTitle>{title}</DialogTitle></DialogHeader>
        {children}
      </DialogContent>
    </Dialog>
  )
}

export function FormBody({ onSubmit, children, submit, pending, onCancel, disabled }: { onSubmit: () => void; children: ReactNode; submit: string; pending?: boolean; onCancel?: () => void; disabled?: boolean }) {
  const handle = (e: FormEvent) => {
    e.preventDefault()
    if (!pending && !disabled) onSubmit()
  }
  return (
    <form onSubmit={handle} className="flex flex-col gap-3.5">
      {children}
      <div className="flex justify-end gap-2 pt-1">
        {onCancel ? <button type="button" className={btn.plain} onClick={onCancel}>Cancel</button> : null}
        <button type="submit" disabled={pending || disabled} className={btn.primary}>{pending ? 'Saving…' : submit}</button>
      </div>
    </form>
  )
}

/** Deleting takes a second click, so a slip can't remove anything. */
export function ConfirmDelete({ label, onConfirm, pending }: { label: string; onConfirm: () => void; pending?: boolean }) {
  const [armed, setArmed] = useState(false)
  if (!armed) return <button type="button" disabled={pending} onClick={() => setArmed(true)} className="h-8 self-start text-[13px] text-destructive underline underline-offset-[3px] cursor-pointer">{label}</button>
  return (
    <span className="flex items-center gap-3 text-[13px]">
      <button type="button" disabled={pending} onClick={onConfirm} className="h-8 px-3 rounded-[6px] bg-destructive text-white font-medium cursor-pointer disabled:opacity-50">Yes, delete</button>
      <button type="button" onClick={() => setArmed(false)} className="underline underline-offset-[3px] cursor-pointer">Keep it</button>
    </span>
  )
}

/** A save that reports its result and refreshes every screen listed in `refresh`, with no page reload. */
export function useSave<T, V = void>(fn: (v: V) => Promise<T>, opts: { success?: string; refresh: string[]; onDone?: (r: T) => void }) {
  return useMutation({
    mutationFn: fn,
    onSuccess: (r) => {
      opts.refresh.forEach((key) => void queryClient.invalidateQueries({ queryKey: [key] }))
      if (opts.success) toast.success(opts.success)
      opts.onDone?.(r)
    },
    onError: (e: Error) => toast.error(e.message),
  })
}

export function Stat({ label, value, tone }: { label: string; value: ReactNode; tone?: 'warn' }) {
  return (
    <div className="stat-card relative px-3.5 py-2.5 min-w-0">
      <p className="text-[12.5px] text-muted-foreground truncate">{label}</p>
      <p className={cn('text-[18px] print:text-[13px] leading-tight font-semibold tracking-[-0.02em] truncate', tone === 'warn' && 'text-[var(--note)]')}>{value}</p>
    </div>
  )
}

export function Stats({ children, cols = 4 }: { children: ReactNode; cols?: 2 | 3 | 4 }) {
  if (cols === 2) return <section className="sheet grid grid-cols-2 overflow-hidden [&>*]:border-border [&>*:nth-child(odd)]:border-r [&>*:nth-child(-n+2)]:border-b">{children}</section>
  return <section className={cn('sheet grid grid-cols-2 overflow-hidden', cols === 4 ? 'lg:grid-cols-4' : 'lg:grid-cols-3', '[&>*]:border-border [&>*:not(:last-child)]:border-r max-lg:[&>*:nth-child(2n)]:border-r-0 max-lg:[&>*:nth-child(-n+2)]:border-b', 'print:grid-cols-4 print:[&>*]:border-b-0! print:[&>*:not(:last-child)]:border-r!')}>{children}</section>
}

/** Downloads text as a file. */
export function download(filename: string, content: string, type = 'text/csv') {
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([content], { type }))
  a.download = filename
  a.click()
  URL.revokeObjectURL(a.href)
}

/** Parses CSV text, including quoted commas and quotes. Returns rows keyed by header. */
export function parseCsv(text: string): Record<string, string>[] {
  const rows: string[][] = []
  let row: string[] = []
  let cell = ''
  let quoted = false
  for (let i = 0; i < text.length; i++) {
    const c = text[i]
    if (quoted) {
      if (c === '"' && text[i + 1] === '"') { cell += '"'; i++ }
      else if (c === '"') quoted = false
      else cell += c
    } else if (c === '"') quoted = true
    else if (c === ',') { row.push(cell); cell = '' }
    else if (c === '\n' || c === '\r') {
      if (c === '\r' && text[i + 1] === '\n') i++
      row.push(cell); cell = ''
      if (row.some((x) => x.trim())) rows.push(row)
      row = []
    } else cell += c
  }
  row.push(cell)
  if (row.some((x) => x.trim())) rows.push(row)
  const [head, ...body] = rows
  if (!head) return []
  const keys = head.map((h) => h.trim())
  return body.map((r) => Object.fromEntries(keys.map((k, i) => [k, (r[i] ?? '').trim()])))
}
