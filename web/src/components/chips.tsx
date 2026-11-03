import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

export type Tone = 'neutral' | 'good' | 'warn' | 'bad' | 'solid'

const TONES: Record<Tone, string> = {
  neutral: 'bg-muted text-muted-foreground',
  good: 'bg-[color-mix(in_srgb,var(--tick)_14%,transparent)] text-[var(--tick)]',
  warn: 'bg-[color-mix(in_srgb,var(--note)_16%,transparent)] text-[var(--note)]',
  bad: 'bg-[color-mix(in_srgb,var(--destructive)_13%,transparent)] text-destructive',
  solid: 'bg-primary text-primary-foreground',
}

/** A short label for what something is or what state it's in. `dot` marks a status. */
export function Badge({ children, tone = 'neutral', dot }: { children: ReactNode; tone?: Tone; dot?: boolean }) {
  return (
    <span className={cn('inline-flex items-center gap-1 h-5 px-2 rounded-full text-[11.5px] font-medium whitespace-nowrap', TONES[tone])}>
      {dot ? <i aria-hidden className="size-1.5 rounded-full bg-current" /> : null}
      {children}
    </span>
  )
}

/** A number on its own, such as how many things are waiting. Shows nothing at zero. */
export function Count({ n, tone = 'neutral', label }: { n: number; tone?: Tone; label: string }) {
  if (!n) return null
  return <span aria-label={`${n} ${label}`} title={`${n} ${label}`} className={cn('inline-grid place-items-center min-w-[18px] h-[18px] px-1 rounded-full text-[11px] font-semibold tabular-nums', TONES[tone])}>{n > 99 ? '99+' : n}</span>
}

/** One filter you can turn on or off. */
export function Chip({ active, onClick, count, children }: { active: boolean; onClick: () => void; count?: number; children: ReactNode }) {
  return (
    <button type="button" aria-pressed={active} onClick={onClick} className={cn('press inline-flex items-center gap-1.5 h-7 px-2.5 rounded-full border text-[12.5px] whitespace-nowrap cursor-pointer', active ? 'bg-primary border-primary text-primary-foreground font-medium' : 'bg-card border-input text-muted-foreground hover:text-foreground hover:bg-accent')}>
      {children}
      {count !== undefined ? <span className={cn('text-[11.5px] tabular-nums', active ? 'opacity-75' : 'opacity-70')}>{count}</span> : null}
    </button>
  )
}

/** A set of filters where exactly one is on. */
export function Chips({ label, value, options, onChange }: { label: string; value: string; options: { id: string; label: string; count?: number }[]; onChange: (id: string) => void }) {
  return (
    <div role="group" aria-label={label} className="flex items-center gap-1.5 max-w-full md:flex-wrap max-md:overflow-x-auto [scrollbar-width:none]">
      {options.map((o) => <Chip key={o.id} active={value === o.id} count={o.count} onClick={() => onChange(o.id)}>{o.label}</Chip>)}
    </div>
  )
}
