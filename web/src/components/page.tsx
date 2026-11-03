import { useState, type ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import type { UseQueryResult } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, ChevronLeft, ChevronRight, Printer } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { PageIcons } from '@/components/page-icons'
import { ApiError } from '@/lib/api'
import { useApp } from '@/lib/boot'
import { cn } from '@/lib/utils'

export function Screen({ title, sub, actions, tabs, children }: { title: string; sub?: ReactNode; actions?: ReactNode; tabs?: ReactNode; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-3.5">
      <header className="flex flex-wrap items-center justify-between gap-x-3 gap-y-2">
        <div className="min-w-0">
          <h1 className="text-[20px] leading-tight font-semibold tracking-[-0.018em] text-balance">{title}</h1>
          {sub ? <p className="text-[13px] text-muted-foreground">{sub}</p> : null}
        </div>
        <div className="flex flex-wrap items-center gap-2 print:hidden">
          {actions}
          <PageIcons className="hidden lg:flex" />
        </div>
      </header>
      {tabs}
      {children}
    </div>
  )
}

export function Tabs({ items }: { items: { to: string; label: string }[] }) {
  return (
    <nav className="flex gap-5 border-b border-border overflow-x-auto overflow-y-hidden print:hidden" aria-label="Sections">
      {items.map((i) => (
        <Link key={i.to} to={i.to} activeOptions={{ exact: true, includeSearch: false }} className="pb-2 -mb-px border-b-2 border-transparent text-[13.5px] text-muted-foreground whitespace-nowrap hover:text-foreground" activeProps={{ className: 'border-primary! text-foreground! font-medium' }}>{i.label}</Link>
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
      <p className="font-medium">{title}</p>
      <p className="text-[13.5px] text-muted-foreground max-w-[44ch]">{body}</p>
      {action}
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
  const go = (n: number) => { setAt(n); window.scrollTo(0, 0) }
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

const BTN = 'press inline-flex items-center justify-center h-8 px-3 rounded-[6px] text-[13px] font-medium whitespace-nowrap cursor-pointer disabled:opacity-50 disabled:pointer-events-none'
export const btn = { primary: `${BTN} bg-primary text-primary-foreground hover:opacity-90`, plain: `${BTN} border border-input bg-card hover:bg-accent` }

/** Prints the page, or saves it as a PDF, always on a white background. */
export function PrintButton() {
  const print = () => {
    const root = document.documentElement
    const dark = root.classList.contains('dark')
    root.classList.remove('dark')
    window.print()
    if (dark) root.classList.add('dark')
  }
  return <button className={btn.plain} onClick={print}><Printer className="size-3.5 mr-1.5" />Print or save PDF</button>
}

export function Check({ ok, title, body, children }: { ok: boolean; title: string; body?: ReactNode; children?: ReactNode }) {
  return (
    <div className="flex gap-2.5 px-3.5 py-2.5 bg-card">
      {ok ? <CheckCircle2 aria-hidden className="size-4 mt-0.5 shrink-0 text-[var(--tick)]" /> : <AlertTriangle aria-hidden className="size-4 mt-0.5 shrink-0 text-[var(--note)]" />}
      <div className="min-w-0 flex-1"><p className="font-medium text-[13.5px]">{title}</p>{body ? <p className="text-[13px] text-muted-foreground">{body}</p> : null}{children}</div>
    </div>
  )
}
