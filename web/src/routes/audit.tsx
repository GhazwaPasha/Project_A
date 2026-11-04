import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Badge, Chips } from '@/components/chips'
import { Modal } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, Table, Toolbar } from '@/components/page'
import { useApp } from '@/lib/boot'
import { q, type Id } from '@/lib/data'

type Row = { id: Id; source: string; action: string; target_type: string | null; target_id: string | null; details: unknown; created_at: string; email: string | null; full_name: string | null }

const when = (s: string) => new Date(s).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
const originOf = (r: Row) => (r.source.startsWith('mcp') ? 'mcp' : r.source)
const ORIGIN: Record<string, string> = { app: 'Person', agent: 'Agent', mcp: 'Connected AI' }

/** Who changed what. Entries can be added but never edited or removed. */
export function AuditLog() {
  const { org, pro } = useApp()
  const list = useQuery(q<Row[]>(['audit', org.id], 'BooksService', 'listAuditLog', [org.id, { limit: 1000 }]))
  const [search, setSearch] = useState('')
  const [origin, setOrigin] = useState('all')
  const [open, setOpen] = useState<Row | null>(null)
  const all = list.data ?? []
  const s = search.trim().toLowerCase()
  const rows = all.filter((r) => (origin === 'all' || originOf(r) === origin) && (!s || `${r.action} ${r.email} ${r.full_name} ${r.target_id}`.toLowerCase().includes(s)))
  const count = (o: string) => all.filter((r) => originOf(r) === o).length
  return (
    <Screen
      title={pro ? 'Audit log' : 'History'}
      sub="Every change made in this organization, and who made it. This record can't be edited."
      search={<SearchIcon label="Search history" placeholder="Search" value={search} onChange={setSearch} />}
    >
      <Toolbar>
        <Chips label="Made by" value={origin} onChange={setOrigin} options={[{ id: 'all', label: 'All', count: all.length }, ...['app', 'agent', 'mcp'].map((o) => ({ id: o, label: ORIGIN[o], count: count(o) }))]} />
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="Nothing recorded yet" body="Changes appear here as people and the agent work." /> : null)}>
        {() => rows.length === 0 ? <Empty title="No matches" body="Try another word or filter." /> : (
          <Paged rows={rows}>
            {(page, pager) => (
              <Table min={720} footer={pager}>
                <thead><tr><Head>When</Head><Head>Who</Head><Head>What</Head><Head>Made by</Head><Head right>Record</Head></tr></thead>
                <tbody>
                  {page.map((r) => (
                    <tr key={r.id} tabIndex={0} className="cursor-pointer hover:bg-accent/50 focus-visible:bg-accent/50 outline-none" onClick={() => setOpen(r)} onKeyDown={(e) => { if (e.key === 'Enter') setOpen(r) }}>
                      <Cell className="text-muted-foreground whitespace-nowrap">{when(r.created_at)}</Cell>
                      <Cell className="whitespace-nowrap">{r.full_name || r.email || 'Unknown'}</Cell>
                      <Cell className="max-w-0 w-full truncate">{r.action}</Cell>
                      <Cell><Badge>{r.source.startsWith('mcp:') ? r.source.slice(4).trim() : ORIGIN[originOf(r)] ?? r.source}</Badge></Cell>
                      <Cell right>{r.target_id ?? ''}</Cell>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {open ? (
        <Modal wide open onClose={() => setOpen(null)} title={open.action}>
          <div className="flex flex-col gap-2.5 text-[13px] min-w-0">
            <p className="text-muted-foreground">{when(open.created_at)}, {open.full_name || open.email || 'Unknown'}{open.target_type ? `, ${open.target_type}${open.target_id ? ` ${open.target_id}` : ''}` : ''}</p>
            {open.details ? <pre className="fig text-[12px] bg-muted/50 rounded-[8px] p-3 overflow-auto max-h-[50vh] whitespace-pre-wrap break-words">{JSON.stringify(open.details, null, 2)}</pre> : <p className="text-muted-foreground">No other details.</p>}
          </div>
        </Modal>
      ) : null}
    </Screen>
  )
}
