import { useEffect, useRef, useState, type ComponentType, type KeyboardEvent } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Command, defaultFilter } from 'cmdk'
import { AnimatePresence, motion, useReducedMotion } from 'motion/react'
import { Building2, FileBarChart, Scale, Search, Sparkles } from 'lucide-react'
import { NAV, canOpen } from '@/components/shell'
import { useAgent } from '@/lib/agent'
import { useApp } from '@/lib/boot'

const HEADER = 44
const OPEN = { type: 'spring', bounce: 0, duration: 0.32 } as const
const CLOSE = { type: 'spring', bounce: 0, duration: 0.2 } as const
const ASK = 'ask the agent '
// Real matches first. Asking the agent always shows, last, so it's never what Enter picks over a match.
const rank = (value: string, search: string, keywords?: string[]) => (value.startsWith(ASK) ? 0.001 : (defaultFilter?.(value, search, keywords) ?? 0))
const FIELD = 'aside [data-sidebar-search]'

/** Where the panel grows from: the sidebar's search field, or the top of the screen where there's no sidebar. */
function measure() {
  const field = document.querySelector(FIELD)?.getBoundingClientRect()
  const width = Math.min(480, innerWidth - 24)
  if (!field?.width) return { left: 12, top: 12, fromWidth: width, fromHeight: 32, width, hasField: false }
  return { left: Math.min(field.left, innerWidth - width - 12), top: field.top, fromWidth: field.width, fromHeight: field.height, width, hasField: true }
}

function Row({ icon: Icon, title, sub, value, keywords, onSelect, accent }: { icon: ComponentType<{ className?: string }>; title: string; sub?: string; value: string; keywords?: string[]; onSelect: () => void; accent?: boolean }) {
  return (
    <Command.Item value={value} keywords={keywords} onSelect={onSelect} className="flex items-center gap-2.5 min-h-11 px-[9px] py-1 rounded-[8px] cursor-pointer select-none data-[selected=true]:bg-accent">
      <Icon className={accent ? 'size-4 shrink-0 text-[var(--c-violet)]' : 'size-4 shrink-0 text-muted-foreground'} />
      <span className="min-w-0 flex-1">
        <span className="block truncate text-[13px] leading-[18px] font-medium">{title}</span>
        {sub ? <span className="block truncate text-[12px] leading-4 text-muted-foreground">{sub}</span> : null}
      </span>
    </Command.Item>
  )
}

/** The sidebar's search field grows into this panel, and shrinks back into the field when it closes. */
function Panel({ onClose }: { onClose: () => void }) {
  const navigate = useNavigate()
  const { orgs, org, setOrg, isSuperAdmin, canSeeBooks, access } = useApp()
  const { ask } = useAgent()
  const reduce = useReducedMotion()
  const [box] = useState(measure)
  const [query, setQuery] = useState('')
  const asked = query.trim()

  // Listens on the window so Esc works wherever focus is, and comes before anything else that closes on Esc.
  useEffect(() => {
    const onEscape = (e: globalThis.KeyboardEvent) => {
      if (e.key !== 'Escape') return
      e.stopImmediatePropagation()
      onClose()
    }
    window.addEventListener('keydown', onEscape, true)
    return () => window.removeEventListener('keydown', onEscape, true)
  }, [onClose])

  const run = (fn: () => void) => { onClose(); fn() }
  const onKeyDown = (e: KeyboardEvent) => { if (e.key === 'Tab') e.preventDefault() }
  const closed = { width: box.fromWidth, height: box.fromHeight, borderRadius: 6, opacity: box.hasField ? 1 : 0 }
  const listHeight = Math.max(160, Math.min(360, innerHeight - box.top - HEADER - 24))

  return (
    <>
      <div aria-hidden className="fixed inset-0 z-50" onPointerDown={onClose} />
      <motion.div
        data-search-panel
        role="dialog"
        aria-label="Search"
        initial={closed}
        animate={{ width: box.width, height: 'auto', borderRadius: 12, opacity: 1, transition: reduce ? { duration: 0 } : OPEN }}
        exit={{ ...closed, opacity: 0, transition: reduce ? { duration: 0 } : { ...CLOSE, opacity: { duration: 0.1, delay: 0.1 } } }}
        style={{ left: box.left, top: box.top }}
        onKeyDown={onKeyDown}
        className="fixed z-50 overflow-hidden border border-border bg-popover text-popover-foreground shadow-xl"
      >
        <Command loop label="Search" filter={rank}>
          <motion.div initial={{ height: box.fromHeight - 2 }} animate={{ height: HEADER }} exit={{ height: box.fromHeight - 2 }} transition={reduce ? { duration: 0 } : OPEN} className="flex items-center gap-2 px-[9px] border-b border-border">
            <Search aria-hidden className="size-3.5 shrink-0 text-muted-foreground" />
            <Command.Input autoFocus aria-label="Search" placeholder="Search" value={query} onValueChange={setQuery} className="flex-1 min-w-0 bg-transparent outline-none text-[16px] sm:text-[13px] placeholder:text-muted-foreground" />
            <motion.button type="button" onClick={onClose} initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="key-cap shrink-0 cursor-pointer">Esc</motion.button>
          </motion.div>
          <motion.div initial={{ opacity: 0, y: -4 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} transition={reduce ? { duration: 0 } : { duration: 0.18, delay: 0.05 }}>
            <Command.List style={{ maxHeight: listHeight }} className="overflow-y-auto overscroll-contain p-1 [scrollbar-width:thin]">
              {canSeeBooks && asked ? null : <Command.Empty className="px-[9px] py-6 text-center text-[13px] text-muted-foreground">No matches.</Command.Empty>}
              {NAV.flatMap((g) => g.items.filter((i) => canOpen(i, access, isSuperAdmin)).map((i) => (
                <Row key={i.label} icon={i.icon} title={i.label} sub={g.group || undefined} value={i.label} keywords={[g.group]} onSelect={() => run(() => void navigate({ to: i.to }))} />
              )))}
              {canSeeBooks ? <>
                <Row icon={Scale} title="Balance Sheet" sub="Reports" value="Balance Sheet" keywords={['Reports']} onSelect={() => run(() => void navigate({ to: '/reports/balance-sheet' }))} />
                <Row icon={FileBarChart} title="Income Statement" sub="Reports" value="Income Statement" keywords={['Reports', 'profit']} onSelect={() => run(() => void navigate({ to: '/reports/income-statement', search: { period: 'month' } }))} />
              </> : null}
              {orgs.filter((o) => o.id !== org.id).map((o) => (
                <Row key={o.id} icon={Building2} title={o.name} sub="Switch organization" value={`switch ${o.name}`} onSelect={() => run(() => setOrg(o.id))} />
              ))}
              {canSeeBooks && asked ? <Row accent icon={Sparkles} title={`"${asked}"`} sub="Ask the agent" value={`${ASK}${asked}`} onSelect={() => run(() => ask(asked))} /> : null}
            </Command.List>
          </motion.div>
        </Command>
      </motion.div>
    </>
  )
}

export function CommandMenu({ open, onOpenChange }: { open: boolean; onOpenChange: (v: boolean) => void }) {
  // Focus goes back to the field it grew from.
  const wasOpen = useRef(false)
  useEffect(() => {
    if (wasOpen.current && !open) document.querySelector<HTMLElement>(FIELD)?.focus({ preventScroll: true })
    wasOpen.current = open
  }, [open])
  return <AnimatePresence>{open ? <Panel key="search" onClose={() => onOpenChange(false)} /> : null}</AnimatePresence>
}
