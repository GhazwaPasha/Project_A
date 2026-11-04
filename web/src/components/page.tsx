import { useEffect, useRef, useState, type ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import { motion } from 'motion/react'
import type { UseQueryResult } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, Printer, Search, X } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api'
import { useApp } from '@/lib/boot'
import { cn, scrollPageToTop } from '@/lib/utils'

export function Screen({ title, sub, search, actions, tabs, children }: { title: string; sub?: ReactNode; search?: ReactNode; actions?: ReactNode; tabs?: ReactNode; children: ReactNode }) {
  return (
    <div className="page-in flex flex-col gap-3.5">
      <header className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <div className="min-w-0">
          <h1 className="text-[20px] leading-tight font-semibold tracking-[-0.018em] text-balance">{title}</h1>
          {sub ? <p className="text-[13px] text-muted-foreground">{sub}</p> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 print:hidden">
          {search}
          {actions}
        </div>
      </header>
      {tabs}
      {children}
    </div>
  )
}

/** A search icon that opens into a field. It stays open while there's a search, so a filtered list is never a mystery. */
export function SearchIcon({ label, placeholder, value, onChange }: { label: string; placeholder?: string; value: string; onChange: (v: string) => void }) {
  const [opened, setOpened] = useState(false)
  const input = useRef<HTMLInputElement>(null)
  const open = opened || value !== ''
  useEffect(() => { if (opened) input.current?.focus() }, [opened])
  const close = () => { onChange(''); setOpened(false) }
  return (
    <div className={cn('flex items-center h-8 max-w-full rounded-[6px] border bg-card overflow-hidden transition-[width] duration-150 ease-out motion-reduce:transition-none', open ? 'w-[200px] border-primary' : 'w-8 border-input')}>
      <button type="button" aria-label={label} aria-expanded={open} title={label} tabIndex={open ? -1 : 0} onClick={() => setOpened(true)} className={cn('size-[30px] shrink-0 grid place-items-center text-muted-foreground', !open && 'cursor-pointer hover:bg-accent hover:text-foreground')}>
        <Search className="size-4" />
      </button>
      <input
        ref={input}
        aria-label={label}
        placeholder={placeholder ?? label}
        tabIndex={open ? 0 : -1}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onBlur={() => { if (!value) setOpened(false) }}
        onKeyDown={(e) => { if (e.key === 'Escape') { e.stopPropagation(); close() } }}
        className="flex-1 min-w-0 bg-transparent outline-none text-[13.5px] placeholder:text-muted-foreground"
      />
      {value ? <button type="button" aria-label="Clear search" onClick={() => { onChange(''); input.current?.focus() }} className="size-[26px] mr-0.5 shrink-0 grid place-items-center rounded-[4px] text-muted-foreground cursor-pointer hover:bg-accent hover:text-foreground"><X className="size-3.5" /></button> : null}
    </div>
  )
}

export function Tabs({ items }: { items: { to: string; label: string }[] }) {
  return (
    <nav className="flex gap-5 border-b border-border overflow-x-auto overflow-y-hidden print:hidden" aria-label="Sections">
      {items.map((i) => (
        <Link key={i.to} to={i.to} activeOptions={{ exact: true, includeSearch: false }} className="relative pb-2 text-[13.5px] text-muted-foreground whitespace-nowrap transition-colors duration-100 hover:text-foreground" activeProps={{ className: 'text-foreground! font-medium' }}>
          {({ isActive }) => <>{i.label}{isActive ? <motion.span aria-hidden layoutId="page-tab" transition={{ type: 'spring', bounce: 0, duration: 0.35 }} className="tab-mark absolute inset-x-0 -bottom-px h-0.5 rounded-full" /> : null}</>}
        </Link>
      ))}
    </nav>
  )
}

/** Connections use the agent's tools, so only roles with the agent see that tab. */
export function SettingsTabs() {
  const { canSeeBooks } = useApp()
  return canSeeBooks ? <Tabs items={[{ to: '/settings', label: 'General' }, { to: '/settings/connections', label: 'Connections' }]} /> : null
}

/** One way to show loading, errors and empty lists on every screen. */
export function Loaded<T>({ query, empty, skeleton, children }: { query: UseQueryResult<T>; empty?: (d: T) => ReactNode | null; skeleton?: ReactNode; children: (d: T) => ReactNode }) {
  if (query.isPending) return <>{skeleton ?? <Skeleton className="h-48 w-full" />}</>
  if (query.isError) {
    const denied = query.error instanceof ApiError && query.error.status === 403
    return (
      <div className="sheet p-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-medium">{denied ? 'Your role does not include this' : "This didn't load"}</p>
          <p className="text-[13.5px] text-muted-foreground">{denied ? 'Ask the organization owner for access.' : query.error.message}</p>
        </div>
        {denied ? null : <Button variant="secondary" size="sm" onClick={() => query.refetch()}>Try again</Button>}
      </div>
    )
  }
  const none = empty?.(query.data)
  return <>{none ?? children(query.data)}</>
}

export function Empty({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="sheet px-6 py-8 flex flex-col items-center gap-1 text-center">
      <span aria-hidden className="empty-prop"><i /><i /><i /></span>
      <p className="font-medium">{title}</p>
      <p className="text-[13.5px] text-muted-foreground max-w-[44ch]">{body}</p>
      {action ? <div className="mt-2.5">{action}</div> : null}
    </div>
  )
}

export function Cell({ className, children, right }: { className?: string; children: ReactNode; right?: boolean }) {
  return <td className={cn('px-3.5 py-1.5 border-b border-border', right && 'text-right whitespace-nowrap fig text-[13px]', className)}>{children}</td>
}
export function Head({ children, right }: { children?: ReactNode; right?: boolean }) {
  return <th className={cn('px-3.5 py-1.5 text-[12px] font-medium text-muted-foreground border-b border-border bg-muted/50 whitespace-nowrap', right ? 'text-right' : 'text-left')}>{children}</th>
}
export function Table({ children, min = 460, footer, wrap }: { children: ReactNode; min?: number; footer?: ReactNode; wrap?: boolean }) {
  return (
    <div className="sheet overflow-hidden">
      <div className="overflow-x-auto"><table className={cn('w-full border-collapse text-[13.5px] [&_tbody_tr:last-child_td]:border-b-0', !wrap && 'whitespace-nowrap')} style={{ minWidth: min }}>{children}</table></div>
      {footer}
    </div>
  )
}

/** Shows a long list a page at a time. Goes back to the first page whenever the list changes length, as it does when searching. */
export function Paged<T>({ rows, size = 25, children }: { rows: T[]; size?: number; children: (page: T[], pager: ReactNode) => ReactNode }) {
  const [at, setAt] = useState(0)
  const [seen, setSeen] = useState(rows.length)
  if (seen !== rows.length) {
    setSeen(rows.length)
    setAt(0)
  }
  const pages = Math.max(1, Math.ceil(rows.length / size))
  const current = Math.min(at, pages - 1)
  const go = (n: number) => { setAt(n); scrollPageToTop() }
  const arrow = 'size-7 grid place-items-center rounded-[6px] border border-input bg-card cursor-pointer hover:bg-accent disabled:opacity-40 disabled:pointer-events-none'
  const pager = rows.length > size ? (
    <nav aria-label="Pages" className="print:hidden flex items-center justify-between gap-3 px-3.5 py-1.5 border-t border-border text-[12.5px] text-muted-foreground">
      <span>{current * size + 1}–{Math.min((current + 1) * size, rows.length)} of {rows.length}</span>
      <span className="flex items-center gap-1.5">
        <span className="mr-1">Page {current + 1} of {pages}</span>
        <button type="button" aria-label="Previous page" disabled={current === 0} onClick={() => go(current - 1)} className={arrow}><ChevronLeft className="size-3.5" /></button>
        <button type="button" aria-label="Next page" disabled={current === pages - 1} onClick={() => go(current + 1)} className={arrow}><ChevronRight className="size-3.5" /></button>
      </span>
    </nav>
  ) : null
  return <>{children(rows.slice(current * size, (current + 1) * size), pager)}</>
}

/** Search on the left, filters beside it, everything on one line where it fits. */
export function Toolbar({ children }: { children: ReactNode }) {
  return <div className="print:hidden flex flex-wrap items-center gap-2">{children}</div>
}

const BTN = 'press inline-flex gap-1.5 items-center justify-center h-8 px-3 rounded-[6px] text-[13px] font-medium whitespace-nowrap cursor-pointer disabled:opacity-50 disabled:pointer-events-none'
export const btn = { primary: `${BTN} fill-cta`, plain: `${BTN} border border-input bg-card hover:bg-accent` }

/** Opens a report's document page, where it can be printed or exported. */
export function PrintLink({ to, search }: { to: string; search?: Record<string, unknown> }) {
  return <Link to={to} search={search as never} className={btn.plain}><Printer className="size-3.5" />Print or export</Link>
}

export function Check({ ok, title, body, children }: { ok: boolean; title: string; body?: ReactNode; children?: ReactNode }) {
  return (
    <div className="flex gap-2.5 px-3.5 py-2.5 bg-card">
      {ok ? <CheckCircle2 aria-hidden className="size-4 mt-0.5 shrink-0 text-[var(--tick)]" /> : <AlertTriangle aria-hidden className="size-4 mt-0.5 shrink-0 text-[var(--note)]" />}
      <div className="min-w-0 flex-1"><p className="font-medium text-[13.5px]">{title}</p>{body ? <p className="text-[13px] text-muted-foreground">{body}</p> : null}{children}</div>
    </div>
  )
}
