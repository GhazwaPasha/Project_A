import { useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { ChevronRight, Download, Plus, Upload } from 'lucide-react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { AskLink } from '@/components/agent-panel'
import { Choice, ConfirmDelete, FormBody, Modal, Pill, Text, Toggle, download, parseCsv, useSave } from '@/components/form'
import { Empty, Loaded, Paged, Screen, Toolbar, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, useApp } from '@/lib/boot'
import { balancesFor, num, q, type Account, type AccountType, type Id } from '@/lib/data'
import { cn } from '@/lib/utils'

const TYPES: { id: AccountType; pro: string; simple: string }[] = [
  { id: 'asset', pro: 'Assets', simple: 'What you have' },
  { id: 'liability', pro: 'Liabilities', simple: 'What you owe' },
  { id: 'equity', pro: 'Equity', simple: "What's yours" },
  { id: 'revenue', pro: 'Revenue', simple: 'Money earned' },
  { id: 'expense', pro: 'Expenses', simple: 'Money spent' },
]
const CATEGORIES: Record<AccountType, { value: string; label: string }[]> = {
  asset: [['current_asset', 'Current asset'], ['fixed_asset', 'Fixed asset'], ['other_asset', 'Other asset']].map(([value, label]) => ({ value, label })),
  liability: [['current_liability', 'Current liability'], ['long_term_liability', 'Long-term liability'], ['other_liability', 'Other liability']].map(([value, label]) => ({ value, label })),
  equity: [['owners_equity', "Owner's equity"], ['retained_earnings', 'Retained earnings'], ['other_equity', 'Other equity']].map(([value, label]) => ({ value, label })),
  revenue: [['operating_revenue', 'Operating revenue'], ['other_revenue', 'Other revenue']].map(([value, label]) => ({ value, label })),
  expense: [['cost_of_sales', 'Cost of sales'], ['operating_expense', 'Operating expense'], ['other_expense', 'Other expense']].map(([value, label]) => ({ value, label })),
}
const chart = (org: string) => q<Account[]>(['accounts', org, 'all'], 'AccountService', 'getAccounts', [org])

type Draft = { id?: Id; name: string; account_type: AccountType; parent_id: string; description: string; group: string; report_category: string; is_postable: boolean }
const blank: Draft = { name: '', account_type: 'expense', parent_id: '', description: '', group: '', report_category: '', is_postable: true }

export function Accounts() {
  const { org, pro, access } = useApp()
  const canEdit = access === 'owner' || access === 'books'
  const list = useQuery(chart(org.id))
  const balances = useQuery(balancesFor(org.id))
  const [search, setSearch] = useState('')
  const [draft, setDraft] = useState<Draft | null>(null)
  const [closed, setClosed] = useState<Set<string>>(new Set())
  const [importing, setImporting] = useState(false)
  const [type, setType] = useState<AccountType>('asset')
  const balanceOf = useMemo(() => new Map((balances.data ?? []).map((b) => [String(b.id), num(b.balance)])), [balances.data])
  const rows = list.data ?? []
  const childrenOf = useMemo(() => {
    const m = new Map<string, Account[]>()
    const known = new Set(rows.map((a) => String(a.id)))
    rows.forEach((a) => {
      // An account whose parent isn't in the list still has to appear somewhere.
      const k = a.parent_id != null && known.has(String(a.parent_id)) ? String(a.parent_id) : 'root'
      m.set(k, [...(m.get(k) ?? []), a])
    })
    return m
  }, [rows])

  const remove = useSave((a: Account) => call('AccountService', 'deleteAccount', [a.id]), { success: 'Account deleted', refresh: ['accounts', 'balances'], onDone: () => setDraft(null) })

  const exportCsv = () => {
    const esc = (v: unknown) => `"${String(v ?? '').replace(/"/g, '""')}"`
    const byId = new Map(rows.map((a) => [String(a.id), a]))
    const lines = [['Code', 'Name', 'Type', 'Parent Code', 'Report category', 'Description', 'Is Postable'].join(','), ...rows.map((a) => [a.code, a.name, a.account_type, byId.get(String(a.parent_id))?.code ?? '', a.report_category ?? '', a.description ?? '', a.is_postable === false ? 'no' : 'yes'].map(esc).join(','))]
    download('chart-of-accounts.csv', lines.join('\n'))
  }

  const term = search.trim().toLowerCase()
  const visible = useMemo(() => {
    if (term) return rows.filter((a) => `${a.code} ${a.name} ${a.group ?? ''}`.toLowerCase().includes(term)).map((a) => ({ a, depth: 0 }))
    const out: { a: Account; depth: number }[] = []
    const walk = (a: Account, depth: number) => {
      out.push({ a, depth })
      if (!closed.has(String(a.id))) (childrenOf.get(String(a.id)) ?? []).forEach((k) => walk(k, depth + 1))
    }
    ;(childrenOf.get('root') ?? []).filter((a) => a.account_type === type).forEach((a) => walk(a, 0))
    return out
  }, [term, rows, childrenOf, closed, type])

  const Row = ({ a, depth }: { a: Account; depth: number }) => {
    const kids = childrenOf.get(String(a.id)) ?? []
    const isClosed = closed.has(String(a.id))
    const header = a.is_postable === false
    const open = () => setDraft({ id: a.id, name: a.name, account_type: a.account_type ?? 'expense', parent_id: a.parent_id == null ? '' : String(a.parent_id), description: a.description ?? '', group: a.group ?? '', report_category: a.report_category ?? '', is_postable: a.is_postable !== false })
    return (
      <>
        <div className="flex items-center gap-1.5 pr-4 border-t border-border hover:bg-accent/50" style={{ paddingLeft: 12 + depth * 18 }}>
          <button aria-label={isClosed ? `Expand ${a.name}` : `Collapse ${a.name}`} disabled={!kids.length} onClick={() => setClosed((s) => { const n = new Set(s); if (n.has(String(a.id))) n.delete(String(a.id)); else n.add(String(a.id)); return n })} className={cn('size-5 grid place-items-center text-muted-foreground shrink-0', kids.length ? 'cursor-pointer' : 'invisible')}>
            <ChevronRight className={cn('size-3.5 transition-transform duration-100', !isClosed && 'rotate-90')} />
          </button>
          <button onClick={canEdit ? open : undefined} className={cn('flex-1 min-w-0 flex items-center gap-2.5 py-1.5 text-left text-[13.5px]', canEdit && 'cursor-pointer')}>
            {pro ? <span className="fig text-[12.5px] text-muted-foreground shrink-0">{a.code}</span> : null}
            <span className={cn('truncate', header && 'font-medium')}>{a.name}</span>
            {pro && header ? <Pill>Header</Pill> : null}
            {pro && a.group ? <span className="text-[12px] text-muted-foreground truncate max-md:hidden">{a.group}</span> : null}
          </button>
          <span className={cn('fig text-[13px] shrink-0', (balanceOf.get(String(a.id)) ?? 0) < 0 && 'text-[var(--note)]')}>{balanceOf.has(String(a.id)) && !header ? figure(balanceOf.get(String(a.id))!, org.decimals) : ''}</span>
        </div>
      </>
    )
  }

  return (
    <Screen
      title="Accounts"
      sub={pro ? `Chart of accounts. ${rows.length} accounts.` : 'The categories your money is sorted into. The agent uses these when it records things.'}
      actions={<>
        {pro ? <button className={btn.plain} disabled={!rows.length} onClick={exportCsv}><Download className="size-3.5 mr-1.5" />Export</button> : null}
        {pro && canEdit ? <button className={btn.plain} onClick={() => setImporting(true)}><Upload className="size-3.5 mr-1.5" />Import</button> : null}
        {canEdit ? <button className={btn.primary} onClick={() => setDraft(blank)}><Plus className="size-3.5 mr-1.5" />New account</button> : null}
      </>}
    >
      <Toolbar>
        <Input aria-label="Search accounts" placeholder="Search accounts" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
        <div role="group" aria-label="Account type" className="flex p-0.5 rounded-[7px] border border-border bg-muted text-[13px] overflow-x-auto max-w-full">
          {TYPES.map((t) => <button key={t.id} aria-pressed={!term && type === t.id} onClick={() => { setType(t.id); setSearch('') }} className={cn('h-7 px-2.5 rounded-[5px] whitespace-nowrap cursor-pointer', !term && type === t.id ? 'bg-card font-medium shadow-[0_0_0_1px_var(--border)]' : 'text-muted-foreground')}>{pro ? t.pro : t.simple} <span className="fig text-[12px] text-muted-foreground">{rows.filter((a) => a.account_type === t.id).length}</span></button>)}
        </div>
        {!pro ? <AskLink className="text-[13px] ml-auto" prompt="Look at my accounts and tell me if anything is missing or set up wrong for my business.">Ask the agent to check these</AskLink> : null}
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No accounts yet" body="Add your first account, or import a chart of accounts." /> : null)}>
        {() => (
          <Paged rows={visible}>
            {(page, pager) => (
              <div className="sheet overflow-hidden [&>div:first-child]:border-t-0">
                {page.length ? page.map(({ a, depth }) => <Row key={a.id} a={a} depth={depth} />) : <p className="p-3.5 text-muted-foreground">{term ? 'No matches.' : 'No accounts of this type yet.'}</p>}
                {pager}
              </div>
            )}
          </Paged>
        )}
      </Loaded>

      <AccountForm key={String(draft?.id ?? (draft ? 'new' : 'closed'))} draft={draft} accounts={rows} onClose={() => setDraft(null)} onDelete={(a) => remove.mutate(a)} />
      <ImportDialog open={importing} onClose={() => setImporting(false)} accounts={rows} />
    </Screen>
  )
}

function AccountForm({ draft, accounts, onClose, onDelete }: { draft: Draft | null; accounts: Account[]; onClose: () => void; onDelete: (a: Account) => void }) {
  const { org, userId } = useApp()
  const [form, setForm] = useState<Draft>(draft ?? blank)
  const set = <K extends keyof Draft>(k: K, v: Draft[K]) => setForm((f) => ({ ...f, [k]: v }))
  const parents = accounts.filter((a) => a.account_type === form.account_type && String(a.id) !== String(form.id))
  const save = useSave(() => {
    const fields = { name: form.name.trim(), account_type: form.account_type, parent_id: form.parent_id ? Number(form.parent_id) : null, description: form.description.trim() || null, group: form.group.trim() || null, report_category: form.report_category || null, is_postable: form.is_postable }
    return form.id != null
      ? call('AccountService', 'updateAccount', [form.id, fields])
      : call('AccountService', 'createAccount', [{ ...fields, organization_id: org.id, is_active: true, created_by: userId }])
  }, { success: form.id != null ? 'Account saved' : 'Account created', refresh: ['accounts', 'balances'], onDone: onClose })
  const existing = accounts.find((a) => String(a.id) === String(form.id))

  return (
    <Modal open={draft !== null} onClose={onClose} title={form.id != null ? 'Edit account' : 'New account'}>
      <FormBody onSubmit={() => save.mutate()} submit={form.id != null ? 'Save account' : 'Create account'} pending={save.isPending} onCancel={onClose} disabled={!form.name.trim()}>
        <Text label="Name" required placeholder="For example, Shop rent" value={form.name} onChange={(v) => set('name', v)} />
        {form.id != null ? <p className="text-[12.5px] text-muted-foreground">Code <span className="fig">{existing?.code}</span> is assigned automatically.</p> : null}
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label="Type" value={form.account_type} onChange={(v) => setForm((f) => ({ ...f, account_type: v as AccountType, parent_id: '', report_category: '' }))} options={TYPES.map((t) => ({ value: t.id, label: t.pro }))} />
          <Choice label="Report category" placeholder="Not set" value={form.report_category} onChange={(v) => set('report_category', v)} options={CATEGORIES[form.account_type]} />
        </div>
        <Choice label="Parent account" placeholder="None" value={form.parent_id} onChange={(v) => set('parent_id', v)} options={parents.map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))} />
        <Text label="Group" value={form.group} onChange={(v) => set('group', v)} />
        <Text label="Description" value={form.description} onChange={(v) => set('description', v)} />
        <Toggle label="Entries can be posted here" hint="Turn off for a header account that only groups other accounts." checked={form.is_postable} onChange={(v) => set('is_postable', v)} />
        {existing ? <ConfirmDelete label="Delete this account" onConfirm={() => onDelete(existing)} /> : null}
      </FormBody>
    </Modal>
  )
}

type Plan = { name: string; type: AccountType; parent: string; category: string; description: string; postable: boolean; line: number }

function ImportDialog({ open, onClose, accounts }: { open: boolean; onClose: () => void; accounts: Account[] }) {
  const { org, userId } = useApp()
  const input = useRef<HTMLInputElement>(null)
  const [plan, setPlan] = useState<Plan[]>([])
  const [errors, setErrors] = useState<string[]>([])
  const reset = () => { setPlan([]); setErrors([]); if (input.current) input.current.value = '' }
  const close = () => { reset(); onClose() }

  const read = async (file: File) => {
    const rows = parseCsv(await file.text())
    const found: Plan[] = []
    const bad: string[] = []
    const valid = TYPES.map((t) => t.id as string)
    rows.forEach((r, i) => {
      const line = i + 2
      const type = (r.Type ?? '').toLowerCase()
      if (!r.Name) return void bad.push(`Line ${line}: Name is required.`)
      if (!valid.includes(type)) return void bad.push(`Line ${line}: Type must be asset, liability, equity, revenue or expense.`)
      found.push({ name: r.Name, type: type as AccountType, parent: r['Parent Code'] || r['Parent Name'] || '', category: r['Report category'] ?? '', description: r.Description ?? '', postable: !/^(no|false|0)$/i.test(r['Is Postable'] ?? 'yes'), line })
    })
    setPlan(found)
    setErrors(rows.length ? bad : ['No rows found. The file needs a header line with at least Name and Type.'])
  }

  const run = useSave(async () => {
    const known = new Map<string, Id>()
    accounts.forEach((a) => { known.set(a.code.toLowerCase(), a.id); known.set(a.name.toLowerCase(), a.id) })
    const failed: string[] = []
    let done = 0
    // Parents first: a row is created once the parent it names exists, whatever order the file uses.
    let waiting = plan
    for (let pass = 0; waiting.length && pass < 10; pass++) {
      const later: Plan[] = []
      for (const p of waiting) {
        const parentId = p.parent ? known.get(p.parent.toLowerCase()) : null
        if (p.parent && !parentId) { later.push(p); continue }
        try {
          const created = await call<Account>('AccountService', 'createAccount', [{ organization_id: org.id, name: p.name, account_type: p.type, parent_id: parentId ? Number(parentId) : null, description: p.description || null, group: null, report_category: p.category || null, is_postable: p.postable, is_active: true, created_by: userId }])
          known.set(p.name.toLowerCase(), created.id)
          done++
        } catch (e) {
          failed.push(`Line ${p.line}: ${e instanceof Error ? e.message : 'could not create'}`)
        }
      }
      if (later.length === waiting.length) { later.forEach((p) => failed.push(`Line ${p.line}: parent "${p.parent}" was not found.`)); break }
      waiting = later
    }
    return { done, failed }
  }, { refresh: ['accounts', 'balances'], onDone: ({ done, failed }) => {
    toast.success(`${done} ${done === 1 ? 'account' : 'accounts'} imported`)
    if (failed.length) { setPlan([]); setErrors(failed) } else close()
  } })

  return (
    <Modal open={open} onClose={close} title="Import accounts">
      <div className="flex flex-col gap-3">
        <p className="text-[13.5px] text-muted-foreground">Upload a CSV with <strong className="font-medium text-foreground">Name</strong> and <strong className="font-medium text-foreground">Type</strong> columns. You can also include Parent Code, Parent Name, Report category, Description and Is Postable. Codes are assigned automatically.</p>
        <input ref={input} aria-label="CSV file" type="file" accept=".csv,text/csv" onChange={(e) => { const f = e.target.files?.[0]; if (f) void read(f) }} className="text-[13px]" />
        {plan.length ? <p className="text-[13.5px] font-medium">{plan.length} {plan.length === 1 ? 'account' : 'accounts'} ready to import.</p> : null}
        {errors.length ? <ul className="text-[13px] text-destructive flex flex-col gap-0.5 max-h-40 overflow-y-auto">{errors.map((e) => <li key={e}>{e}</li>)}</ul> : null}
        <div className="flex justify-end gap-2">
          <button className={btn.plain} onClick={close}>Close</button>
          <button className={btn.primary} disabled={!plan.length || run.isPending} onClick={() => run.mutate()}>{run.isPending ? 'Importing…' : 'Import'}</button>
        </div>
      </div>
    </Modal>
  )
}
