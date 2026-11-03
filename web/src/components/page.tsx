import type { ReactNode } from 'react'
import { Link } from '@tanstack/react-router'
import type { UseQueryResult } from '@tanstack/react-query'
import { CheckCircle2, AlertTriangle, Printer } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api'
import { cn } from '@/lib/utils'

export function Screen({ title, sub, actions, tabs, children }: { title: string; sub?: ReactNode; actions?: ReactNode; tabs?: ReactNode; children: ReactNode }) {
  return (
    <div className="flex flex-col gap-5">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-[22px] leading-tight font-semibold tracking-[-0.018em] text-balance">{title}</h1>
          {sub ? <p className="mt-0.5 text-muted-foreground">{sub}</p> : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-2 print:hidden">{actions}</div> : null}
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
        <Link key={i.to} to={i.to} activeOptions={{ exact: true }} className="pb-2 -mb-px border-b-2 border-transparent text-[13.5px] text-muted-foreground whitespace-nowrap hover:text-foreground" activeProps={{ className: 'border-primary! text-foreground! font-medium' }}>{i.label}</Link>
      ))}
    </nav>
  )
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
    <div className="sheet px-6 py-10 flex flex-col items-center gap-1 text-center">
      <p className="font-medium">{title}</p>
      <p className="text-[13.5px] text-muted-foreground max-w-[44ch]">{body}</p>
      {action}
    </div>
  )
}

export function Cell({ className, children, right }: { className?: string; children: ReactNode; right?: boolean }) {
  return <td className={cn('px-4 py-2 border-b border-border', right && 'text-right whitespace-nowrap fig text-[13px]', className)}>{children}</td>
}
export function Head({ children, right }: { children?: ReactNode; right?: boolean }) {
  return <th className={cn('px-4 py-2 text-[12px] font-medium text-muted-foreground border-b border-border bg-muted/50 whitespace-nowrap', right ? 'text-right' : 'text-left')}>{children}</th>
}
export function Table({ children, min = 460 }: { children: ReactNode; min?: number }) {
  return <div className="sheet overflow-x-auto"><table className="w-full border-collapse text-[13.5px]" style={{ minWidth: min }}>{children}</table></div>
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

export function Range({ value, options, onChange, label }: { value: string; options: { id: string; label: string }[]; onChange: (id: string) => void; label: string }) {
  return (
    <select aria-label={label} value={value} onChange={(e) => onChange(e.target.value)} className={cn(btn.plain, 'pr-2')}>
      {options.map((o) => <option key={o.id} value={o.id}>{o.label}</option>)}
    </select>
  )
}

export function Check({ ok, title, body, children }: { ok: boolean; title: string; body?: ReactNode; children?: ReactNode }) {
  return (
    <div className="flex gap-3 px-4 py-3 border-b border-border last:border-b-0">
      {ok ? <CheckCircle2 aria-hidden className="size-4 mt-0.5 shrink-0 text-[var(--tick)]" /> : <AlertTriangle aria-hidden className="size-4 mt-0.5 shrink-0 text-[var(--note)]" />}
      <div className="min-w-0 flex-1"><p className="font-medium text-[13.5px]">{title}</p>{body ? <p className="text-[13px] text-muted-foreground">{body}</p> : null}{children}</div>
    </div>
  )
}
