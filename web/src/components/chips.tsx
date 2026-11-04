import { useId, type ReactNode } from 'react'
import { motion } from 'motion/react'
import { cn } from '@/lib/utils'

export type Tone = 'neutral' | 'good' | 'warn' | 'bad' | 'solid'

const TONES: Record<Tone, string> = {
  neutral: 'bg-muted text-muted-foreground',
  good: 'bg-[color-mix(in_srgb,var(--tick)_14%,transparent)] text-[var(--tick)]',
  warn: 'bg-[color-mix(in_srgb,var(--note)_16%,transparent)] text-[var(--note)]',
  bad: 'bg-[color-mix(in_srgb,var(--destructive)_13%,transparent)] text-destructive',
  solid: 'fill-cta',
}

/** A short label for what something is or what state it's in. `dot` marks a status. */
export function Badge({ children, tone = 'neutral', dot }: { children: ReactNode; tone?: Tone; dot?: boolean }) {
  return (
    <span className={cn('inline-flex items-center gap-1.5 h-5 rounded-full text-[11.5px] leading-none font-medium whitespace-nowrap align-middle', dot ? 'pl-1.5 pr-2' : 'px-2', TONES[tone])}>
      {dot ? <i aria-hidden className="size-1.5 shrink-0 rounded-full bg-current" /> : null}
      {children}
    </span>
  )
}

/** A number on its own, such as how many things are waiting. Shows nothing at zero. */
export function Count({ n, tone = 'neutral', label }: { n: number; tone?: Tone; label: string }) {
  if (!n) return null
  return <span key={n} aria-label={`${n} ${label}`} title={`${n} ${label}`} className={cn('pop-in inline-grid place-items-center min-w-[18px] h-[18px] px-1 rounded-full text-[11px] leading-none font-semibold tabular-nums', TONES[tone])}>{n > 99 ? '99+' : n}</span>
}

/** One filter you can turn on or off. Inside `Chips`, the selected pill slides across rather than jumping. */
export function Chip({ active, onClick, count, children, pill }: { active: boolean; onClick: () => void; count?: number; children: ReactNode; pill?: string }) {
  return (
    <button type="button" aria-pressed={active} onClick={onClick} className={cn('press relative inline-flex items-center gap-1.5 h-7 px-2.5 rounded-full border text-[12.5px] leading-none whitespace-nowrap cursor-pointer', active ? 'border-transparent font-medium' : 'bg-card border-input text-muted-foreground hover:text-foreground hover:bg-accent', active && !pill && 'fill-cta', active && pill && 'on-cta')}>
      {active && pill ? <motion.span aria-hidden layoutId={pill} transition={{ type: 'spring', bounce: 0, duration: 0.35 }} className="fill-cta absolute -inset-px rounded-full" /> : null}
      <span className="relative inline-flex items-center gap-1.5">{children}</span>
      {count !== undefined ? <span className={cn('relative text-[11.5px] tabular-nums', active ? 'opacity-75' : 'opacity-70')}>{count}</span> : null}
    </button>
  )
}

/** A set of filters where exactly one is on. */
export function Chips({ label, value, options, onChange }: { label: string; value: string; options: { id: string; label: string; count?: number }[]; onChange: (id: string) => void }) {
  const pill = useId()
  return (
    <div role="group" aria-label={label} className="flex items-center gap-1.5 max-w-full md:flex-wrap max-md:overflow-x-auto [scrollbar-width:none]">
      {options.map((o) => <Chip key={o.id} pill={pill} active={value === o.id} count={o.count} onClick={() => onChange(o.id)}>{o.label}</Chip>)}
    </div>
  )
}
