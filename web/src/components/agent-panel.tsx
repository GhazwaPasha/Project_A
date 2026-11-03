import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import { useRouterState } from '@tanstack/react-router'
import { ArrowUp, Eye, Sparkles, X } from 'lucide-react'
import { toast } from 'sonner'
import { Badge } from '@/components/chips'
import { NewEntry, type Draft } from '@/components/new-entry'
import { btn } from '@/components/page'
import { decideProposal, type Proposal } from '@/lib/api'
import { useAgent } from '@/lib/agent'
import { figure, shortDate, useApp } from '@/lib/boot'
import { proposals, queryClient, refreshBooks } from '@/lib/data'
import { suggestionsFor } from '@/lib/page-context'
import { cn } from '@/lib/utils'

export function Composer({ placeholder, large, id = 'agent-input' }: { placeholder: string; large?: boolean; id?: string }) {
  const { ask, busy } = useAgent()
  const [text, setText] = useState('')
  const submit = (e: FormEvent) => {
    e.preventDefault()
    if (!text.trim() || busy) return
    ask(text.trim())
    setText('')
  }
  return (
    <form onSubmit={submit} className={cn('flex items-center gap-2 bg-card border border-input focus-within:border-primary', large ? 'pl-4 pr-2 h-12 rounded-[10px]' : 'pl-3.5 pr-1.5 h-11 rounded-[10px]')}>
      <input id={id} aria-label={placeholder} autoComplete="off" value={text} onChange={(e) => setText(e.target.value)} placeholder={placeholder} className="flex-1 min-w-0 bg-transparent outline-none text-[16px] sm:text-[14.5px] placeholder:text-muted-foreground" />
      <button type="submit" aria-label="Send" disabled={!text.trim() || busy} className={cn('press bg-primary text-primary-foreground shrink-0 grid place-items-center cursor-pointer font-semibold disabled:opacity-40 disabled:pointer-events-none', large ? 'h-8 px-3.5 rounded-[6px]' : 'size-8 rounded-[6px]')}>
        {large ? 'Send' : <ArrowUp className="size-4" />}
      </button>
    </form>
  )
}

export function AskLink({ prompt, children, className }: { prompt: string; children: React.ReactNode; className?: string }) {
  const { ask, busy } = useAgent()
  const { canSeeBooks } = useApp()
  if (!canSeeBooks) return null
  return <button type="button" disabled={busy} onClick={() => ask(prompt)} className={cn('text-primary font-medium underline decoration-border underline-offset-[3px] hover:decoration-primary cursor-pointer text-left disabled:opacity-50', className)}>{children}</button>
}

/** Something to ask the agent, one click away. */
export function AskChip({ prompt, children }: { prompt: string; children: React.ReactNode }) {
  const { ask, busy } = useAgent()
  const { canSeeBooks } = useApp()
  if (!canSeeBooks) return null
  return (
    <button type="button" disabled={busy} onClick={() => ask(prompt)} className="press inline-flex items-center gap-1.5 h-7 px-2.5 rounded-full border border-input bg-card text-[12.5px] font-medium whitespace-nowrap max-w-full cursor-pointer hover:bg-accent disabled:opacity-50">
      <Sparkles aria-hidden className="size-3 shrink-0 text-muted-foreground" />
      <span className="truncate">{children}</span>
    </button>
  )
}

export function ProposalCard({ proposal: p }: { proposal: Proposal }) {
  const { org, pro } = useApp()
  const [status, setStatus] = useState(p.status)
  const [editing, setEditing] = useState<Draft | null>(null)
  const [showLines, setShowLines] = useState(false)
  const total = p.lines.reduce((s, l) => s + l.debit, 0)
  const live = useQuery(proposals(org.id))
  // Reflect a decision made elsewhere, such as on Home while this card sits in the conversation.
  const gone = status === 'pending' && live.isSuccess && !live.isFetching && !live.data.some((x) => x.id === p.id)
  const decide = useMutation({
    mutationFn: (action: 'approve' | 'discard') => decideProposal(org.id, p.id, action),
    onSuccess: (_r, action) => {
      setStatus(action === 'approve' ? 'recorded' : 'discarded')
      if (action === 'approve') { refreshBooks(); toast.success('Recorded in your books') }
      void queryClient.invalidateQueries({ queryKey: ['proposals'] })
    },
    onError: (e: Error) => toast.error(e.message),
  })
  const open = status === 'pending' && !gone

  return (
    <div className={cn('rounded-[8px] p-3.5 flex flex-col gap-2 border', open ? 'border-primary/40 bg-card' : 'border-border bg-muted opacity-75')}>
      <div className="flex items-baseline justify-between gap-3">
        <p className="font-semibold min-w-0">{p.description}</p>
        <span className="font-semibold shrink-0 whitespace-nowrap">{org.currency} {figure(total, org.decimals)}</span>
      </div>
      <p className="text-[13px] text-muted-foreground">{p.explanation}</p>
      <div className="flex flex-wrap items-center gap-1.5 text-[12px] text-muted-foreground">
        <span className="mr-0.5">{shortDate(p.date)}</span>
        {p.source === 'mcp' ? <Badge>From {p.source_name ?? 'a connected app'}</Badge> : null}
        {p.confidence === 'medium' ? <Badge tone="warn" dot>Please check this one</Badge> : p.confidence === 'low' ? <Badge tone="bad" dot>The agent is unsure</Badge> : null}
      </div>
      {pro || showLines ? (
        <table className="w-full text-[12.5px] rounded-[6px] bg-muted">
          <tbody>
            {p.lines.map((l) => (
              <tr key={`${l.account_id}-${l.debit}-${l.credit}`}>
                <td className="py-1 pl-2.5 pr-2"><span className="fig text-muted-foreground mr-1.5">{l.code}</span>{l.name}</td>
                <td className="fig text-right whitespace-nowrap">{l.debit ? `Dr ${figure(l.debit, org.decimals)}` : ''}</td>
                <td className="fig text-right whitespace-nowrap px-2.5">{l.credit ? `Cr ${figure(l.credit, org.decimals)}` : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : <button type="button" onClick={() => setShowLines(true)} className="self-start text-[12.5px] text-primary underline decoration-border underline-offset-[3px] hover:decoration-primary cursor-pointer">See the accounting</button>}
      {open ? (
        <div className="flex flex-wrap gap-2 pt-1">
          <button className={btn.primary} disabled={decide.isPending} onClick={() => decide.mutate('approve')}>{decide.isPending ? 'Working…' : 'Approve and record'}</button>
          <button className={btn.plain} disabled={decide.isPending} onClick={() => setEditing({ date: p.date, description: p.description, lines: p.lines.map((l) => ({ account: String(l.account_id), debit: l.debit ? String(l.debit) : '', credit: l.credit ? String(l.credit) : '' })) })}>Change</button>
          <button className={btn.plain} disabled={decide.isPending} onClick={() => decide.mutate('discard')}>Discard</button>
        </div>
      ) : <div><Badge tone={status === 'recorded' ? 'good' : 'neutral'} dot>{status === 'recorded' ? 'Recorded' : status === 'discarded' ? 'Discarded' : 'Already decided'}</Badge></div>}
      <NewEntry open={editing !== null} draft={editing ?? undefined} onOpenChange={(v) => { if (!v) setEditing(null) }} onRecorded={() => decide.mutate('discard')} />
    </div>
  )
}

/** The heading of the page behind the panel, kept current as the page changes or finishes loading. */
function usePageTitle(active: boolean) {
  const [title, setTitle] = useState('')
  useEffect(() => {
    const main = document.querySelector('main')
    if (!active || !main) return
    const read = () => setTitle(main.querySelector('h1')?.textContent?.trim() ?? '')
    read()
    const watch = new MutationObserver(read)
    watch.observe(main, { childList: true, subtree: true, characterData: true })
    return () => watch.disconnect()
  }, [active])
  return title
}

export function AgentPanel() {
  const { turns, open, setOpen } = useAgent()
  const path = useRouterState({ select: (x) => x.location.pathname })
  const title = usePageTitle(open)
  const suggestions = suggestionsFor(path)
  const end = useRef<HTMLDivElement>(null)
  useEffect(() => { end.current?.scrollIntoView({ block: 'end' }) }, [turns])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && open) setOpen(false) }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, setOpen])

  return (
    <aside aria-label="Agent" inert={!open} className={cn('agent-panel print:hidden fixed top-0 right-0 bottom-0 z-20 w-full sm:w-[400px] bg-background border-l border-border flex flex-col', open ? 'translate-x-0' : 'translate-x-full')}>
      <div className="flex items-center justify-between h-12 px-4 shrink-0 border-b border-border">
        <div className="flex items-center gap-2 min-w-0">
          <h2 className="font-semibold text-[14px]">Agent</h2>
          {title ? <span title={`The agent can see this page: ${title}`} className="inline-flex items-center gap-1 min-w-0 h-5 px-2 rounded-full bg-muted text-muted-foreground text-[11.5px] font-medium"><Eye aria-hidden className="size-3 shrink-0" /><span className="sr-only">The agent can see </span><span className="truncate">{title}</span></span> : null}
        </div>
        <button aria-label="Close" onClick={() => setOpen(false)} className="size-8 -mr-1.5 grid place-items-center rounded-full text-muted-foreground hover:bg-accent cursor-pointer"><X className="size-4" /></button>
      </div>
      <div className="flex-1 overflow-y-auto overscroll-contain p-4 flex flex-col gap-4" aria-live="polite">
        {turns.length === 0 ? (
          <div className="flex flex-col gap-2.5 items-start">
            <p className="text-muted-foreground">I can see the page you're on, so ask about it, or tell me what happened in your business. I'll prepare the entries, and nothing is recorded until you approve it.</p>
          </div>
        ) : turns.map((t) => t.role === 'user' ? (
          <p key={t.id} className="self-end max-w-[85%] rounded-[8px] bg-accent px-3.5 py-2">{t.text}</p>
        ) : (
          <div key={t.id} className="flex flex-col gap-2.5">
            {t.text ? <p className="whitespace-pre-wrap">{t.text}</p> : null}
            {t.status ? <p className="text-[13px] text-muted-foreground animate-pulse">{t.status}…</p> : null}
            {t.proposals.map((p) => <ProposalCard key={p.id} proposal={p} />)}
            {t.error ? <p className="text-[13.5px] text-destructive">{t.error}</p> : null}
          </div>
        ))}
        <div ref={end} />
      </div>
      <div className="px-4 pt-2 shrink-0 pb-[calc(16px+env(safe-area-inset-bottom))] flex flex-col gap-2">
        <div className="flex gap-1.5 overflow-x-auto [scrollbar-width:none] -mx-4 px-4" aria-label="Suggestions for this page">{suggestions.map((s) => <AskChip key={s} prompt={s}>{s}</AskChip>)}</div>
        <Composer id="agent-panel-input" placeholder="Ask about this page" />
      </div>
    </aside>
  )
}
