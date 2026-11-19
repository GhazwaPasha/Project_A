import { createContext, useContext, useEffect, useLayoutEffect, useRef, useState, type FormEvent, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { useMutation } from '@tanstack/react-query'
import { X } from 'lucide-react'
import { toast } from 'sonner'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Switch } from '@/components/ui/switch'
import { btn } from '@/components/page'
import { queryClient } from '@/lib/data'
import { cn, PAGE_SIDE } from '@/lib/utils'

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

/** True inside a side section, so a form keeps its buttons in view at the bottom. */
const InSide = createContext(false)

/**
 * A form or detail that opens beside the page, in the same place as New entry, so the page stays in view.
 * The page beside it keeps working. Where the screen is too narrow for both, it covers the page instead.
 * Esc or the close button closes it. Without the page's side slot (outside the app shell) it falls back to a dialog.
 */
export function Modal({ open, onClose, title, children, wide }: { open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean }) {
  const body = useRef<HTMLDivElement>(null)
  const close = useRef(onClose)
  close.current = onClose
  // Esc closes this section only. An open dropdown handles its own Esc first.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== 'Escape' || e.target instanceof HTMLSelectElement || document.querySelector('[data-search-panel]')) return
      e.stopImmediatePropagation()
      close.current()
    }
    window.addEventListener('keydown', onKey, true)
    return () => window.removeEventListener('keydown', onKey, true)
  }, [open])
  // A wide form, like an invoice with its line table, gets a wider side section.
  useEffect(() => {
    const slot = open && wide ? document.getElementById(PAGE_SIDE) : null
    if (!slot) return
    slot.dataset.wide = ''
    return () => { delete slot.dataset.wide }
  }, [open, wide])
  // Start typing straight away, in the first field, unless something inside already took focus.
  useEffect(() => {
    if (!open || !body.current || body.current.contains(document.activeElement)) return
    body.current.querySelector<HTMLElement>('input:not([type=hidden]):not([disabled]), select:not([disabled]), textarea:not([disabled])')?.focus({ preventScroll: true })
  }, [open])
  if (!open) return null
  const slot = document.getElementById(PAGE_SIDE)
  if (!slot) {
    return (
      <Dialog open onOpenChange={(v) => { if (!v) onClose() }}>
        <DialogContent className={cn('max-h-[90dvh] overflow-y-auto', wide ? 'sm:max-w-[760px]' : 'sm:max-w-[520px]')}>
          <DialogHeader><DialogTitle>{title}</DialogTitle></DialogHeader>
          {children}
        </DialogContent>
      </Dialog>
    )
  }
  return createPortal(
    <section aria-label={title} className="side-section absolute inset-0 flex flex-col bg-background">
      <header className="shrink-0 flex items-center justify-between gap-3 h-[61px] px-4 border-b border-border">
        <h2 className="text-[20px] leading-tight font-semibold tracking-[-0.018em] truncate">{title}</h2>
        <button type="button" aria-label="Close" onClick={onClose} className="press size-8 -mr-1.5 grid place-items-center rounded-[6px] text-muted-foreground cursor-pointer hover:bg-accent hover:text-foreground"><X className="size-4" /></button>
      </header>
      <div ref={body} data-side-body className="flex-1 min-h-0 overflow-y-auto overscroll-contain px-4 pt-4 flex flex-col gap-3.5 [&>*:last-child:not(form)]:mb-4">
        <InSide.Provider value>{children}</InSide.Provider>
      </div>
    </section>,
    slot,
  )
}

export function FormBody({ onSubmit, children, submit, pending, onCancel, disabled }: { onSubmit: () => void; children: ReactNode; submit: string; pending?: boolean; onCancel?: () => void; disabled?: boolean }) {
  // Only the section's own form pins its buttons to the bottom. A smaller form inside it, like a payment box, keeps them in place.
  const inSide = useContext(InSide)
  const ref = useRef<HTMLFormElement>(null)
  const [side, setSide] = useState(false)
  useLayoutEffect(() => { setSide(inSide && ref.current?.parentElement?.hasAttribute('data-side-body') === true) }, [inSide])
  const handle = (e: FormEvent) => {
    e.preventDefault()
    if (!pending && !disabled) onSubmit()
  }
  return (
    <form ref={ref} onSubmit={handle} className={cn('flex flex-col gap-3.5', side && 'flex-1')}>
      {children}
      <div className={cn('flex justify-end gap-2 pt-1', side && 'sticky bottom-0 -mx-4 mt-auto px-4 py-3 pb-[calc(12px+env(safe-area-inset-bottom))] border-t border-border bg-background')}>
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
    // The save stays pending until the screens it changed have their new figures, so nobody sees the old
    // state after "Saved", or clicks the same action twice while it catches up.
    onSuccess: async (r) => {
      if (opts.success) toast.success(opts.success)
      await Promise.all(opts.refresh.map((key) => queryClient.invalidateQueries({ queryKey: [key] }).catch(() => null)))
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
