import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from 'react'
import { useRouterState } from '@tanstack/react-router'
import { streamAgent, type AgentEvent, type AgentRequest, type Proposal } from './api'
import { useApp } from './boot'
import { queryClient, today } from './data'
import { readPage } from './page-context'

export type Turn =
  | { id: number; role: 'user'; text: string }
  | { id: number; role: 'agent'; text: string; status: string | null; proposals: Proposal[]; error: string | null; done: boolean }

type Ctx = {
  turns: Turn[]
  open: boolean
  setOpen: (v: boolean) => void
  busy: boolean
  ask: (text: string) => void
  /** True while the New entry section is open, so the agent's entries go into it. */
  entryOpen: boolean
  registerEntryForm: (fill: (p: Proposal) => void) => () => void
  /** The proposal currently in the New entry form. Its card can't also approve it, or it would be recorded twice. */
  entryProposal: string | null
  setEntryProposal: (id: string | null) => void
}
const AgentContext = createContext<Ctx | null>(null)

export const useAgent = () => {
  const ctx = useContext(AgentContext)
  if (!ctx) throw new Error('useAgent must be used inside AgentProvider')
  return ctx
}

const describe = (p: Proposal) => `[I proposed an entry for approval: ${p.description}, ${p.lines.map((l) => `${l.name} Dr ${l.debit} Cr ${l.credit}`).join('; ')}]`

export function AgentProvider({ children }: { children: ReactNode }) {
  const { org, pro } = useApp()
  const path = useRouterState({ select: (s) => s.location.pathname })
  const [turns, setTurns] = useState<Turn[]>([])
  const [open, setOpen] = useState(false)
  const [busy, setBusy] = useState(false)
  const nextId = useRef(1)
  const latest = useRef<Turn[]>([])
  latest.current = turns
  const fillEntry = useRef<((p: Proposal) => void) | null>(null)
  const [entryOpen, setEntryOpen] = useState(false)
  const [entryProposal, setEntryProposal] = useState<string | null>(null)
  const registerEntryForm = useCallback((fill: (p: Proposal) => void) => {
    fillEntry.current = fill
    setEntryOpen(true)
    return () => {
      if (fillEntry.current !== fill) return
      fillEntry.current = null
      setEntryOpen(false)
      setEntryProposal(null)
    }
  }, [])

  const ask = useCallback((text: string) => {
    if (!text.trim() || busy) return
    setOpen(true)
    setBusy(true)
    const userId = nextId.current++
    const agentId = nextId.current++
    const history = latest.current.flatMap((t): AgentRequest['messages'] => {
      if (t.role === 'user') return [{ role: 'user', text: t.text }]
      const content = [t.text, ...t.proposals.map(describe)].filter(Boolean).join('\n')
      return content ? [{ role: 'assistant', text: content }] : []
    }).slice(-20)
    setTurns((ts) => [...ts, { id: userId, role: 'user', text }, { id: agentId, role: 'agent', text: '', status: 'Thinking', proposals: [], error: null, done: false }])

    const patch = (fn: (t: Extract<Turn, { role: 'agent' }>) => Extract<Turn, { role: 'agent' }>) =>
      setTurns((ts) => ts.map((t) => (t.id === agentId && t.role === 'agent' ? fn(t) : t)))
    let finished = false
    const onEvent = (e: AgentEvent) => {
      if (e.type === 'done') finished = true
      if (e.type === 'text') patch((t) => ({ ...t, text: t.text + e.text, status: null }))
      if (e.type === 'status') patch((t) => ({ ...t, status: e.text }))
      if (e.type === 'proposal') {
        patch((t) => ({ ...t, status: null, proposals: [...t.proposals, e.proposal] }))
        if (fillEntry.current) {
          fillEntry.current(e.proposal)
          setEntryProposal(e.proposal.id)
        }
        void queryClient.invalidateQueries({ queryKey: ['proposals'] })
      }
      if (e.type === 'error') patch((t) => ({ ...t, status: null, error: e.message }))
    }
    void streamAgent({
      org: org.id,
      screen: path,
      mode: pro ? 'accountant' : 'simple',
      currency: org.currency,
      today: today(),
      page: readPage(),
      messages: [...history, { role: 'user', text }],
    }, onEvent)
      .catch((e: Error) => patch((t) => ({ ...t, error: e.message })))
      .finally(() => {
        // A reply that stops early, or comes back empty, says so rather than leaving a blank.
        patch((t) => ({
          ...t,
          status: null,
          done: true,
          error: t.error ?? (!finished ? 'This reply was cut off. Try asking again.' : !t.text && !t.proposals.length ? "I didn't get an answer from the AI service. Try asking again." : null),
        }))
        setBusy(false)
      })
  }, [busy, org.id, org.currency, path, pro])

  const value = useMemo(() => ({ turns, open, setOpen, busy, ask, entryOpen, registerEntryForm, entryProposal, setEntryProposal }), [turns, open, busy, ask, entryOpen, registerEntryForm, entryProposal])
  return <AgentContext.Provider value={value}>{children}</AgentContext.Provider>
}
