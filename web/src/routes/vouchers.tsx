import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Paperclip, Plus, X } from 'lucide-react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { AskChip } from '@/components/agent-panel'
import { Choice, ConfirmDelete, FormBody, Modal, Stat, Stats, Text, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, Table, Tabs, Toolbar, btn } from '@/components/page'
import { Badge, Chips } from '@/components/chips'
import { call, uploadAttachment } from '@/lib/api'
import { figure, shortDate, useApp } from '@/lib/boot'
import { accounts, num, q, refreshBooks, today, type Id, type Money } from '@/lib/data'
import { INVENTORY_TABS, items, useCanWriteStock, warehousesQuery } from '@/routes/inventory'

type Status = 'draft' | 'pending_finance' | 'approved' | 'receiving' | 'issuing' | 'posted' | 'completed' | 'rejected' | 'expired' | 'cancelled'
type Line = { id: Id; item_id: Id; line_number: number; quantity_requested: Money; quantity_actual?: Money | null; unit_cost_estimated?: Money | null; unit_cost_actual?: Money | null; total_cost: Money; item?: { name: string; sku: string } }
type Attachment = { id: Id; file_name: string; file_size?: number }
export type Voucher = { id: Id; voucher_number: string; voucher_type: 'purchase' | 'issuance'; status: Status; requested_date: string; vendor_name?: string | null; purpose?: string | null; destination?: string | null; description?: string | null; notes?: string | null; payment_type: string; total_estimated_cost: Money; total_actual_cost?: Money | null; approval_deadline?: string | null; renewal_count?: number; rejection_reason?: string | null; lines?: Line[]; attachments?: Attachment[] }
type StatsRow = { total_vouchers: Money; pending_approval: Money; approved: Money; rejected: Money; expired: Money; completed: Money; total_value: Money }

const STATUS: Record<Status, { label: string; tone: 'neutral' | 'good' | 'warn' | 'bad' }> = {
  draft: { label: 'Draft', tone: 'neutral' },
  pending_finance: { label: 'Needs approval', tone: 'warn' },
  approved: { label: 'Approved', tone: 'good' },
  receiving: { label: 'Receiving', tone: 'neutral' },
  issuing: { label: 'Issuing', tone: 'neutral' },
  posted: { label: 'Posted', tone: 'good' },
  completed: { label: 'Completed', tone: 'good' },
  rejected: { label: 'Rejected', tone: 'bad' },
  expired: { label: 'Expired', tone: 'bad' },
  cancelled: { label: 'Cancelled', tone: 'neutral' },
}
const REFRESH = ['vouchers', 'voucher', 'voucher-stats', 'stock', 'low-stock', 'movements']
const vouchersQuery = (org: string, status: string, type: string, search: string) => q<Voucher[]>(['vouchers', org, status, type, search], 'VoucherService', 'getVouchers', [org, { ...(status !== 'all' ? { status: [status] } : {}), ...(type !== 'all' ? { voucher_type: [type] } : {}), ...(search ? { search } : {}) }])
const statsQuery = (org: string) => q<StatsRow>(['voucher-stats', org, 'full'], 'VoucherService', 'getVoucherStats', [org])

function VoucherTable({ rows, onOpen }: { rows: Voucher[]; onOpen: (v: Voucher) => void }) {
  const { org, pro } = useApp()
  return (
    <Paged rows={rows}>
      {(page, pager) => (
    <Table min={720} footer={pager}>
      <thead><tr><Head>Voucher</Head><Head>Type</Head><Head>{pro ? 'Vendor or purpose' : 'For'}</Head><Head>Status</Head><Head>Date</Head><Head right>Amount</Head></tr></thead>
      <tbody>
        {page.map((v) => (
          <tr key={v.id} tabIndex={0} className="cursor-pointer hover:bg-accent/50 focus-visible:bg-accent/50 outline-none" onClick={() => onOpen(v)} onKeyDown={(e) => { if (e.key === 'Enter') onOpen(v) }}>
            <Cell className="fig text-[12.5px] whitespace-nowrap">{v.voucher_number}</Cell>
            <Cell><Badge>{v.voucher_type === 'purchase' ? 'Purchase' : 'Issuance'}</Badge></Cell>
            <Cell className="max-w-0 w-full truncate">{v.vendor_name || v.purpose || v.description || ''}</Cell>
            <Cell><Badge dot tone={STATUS[v.status]?.tone}>{STATUS[v.status]?.label ?? v.status}</Badge></Cell>
            <Cell className="text-muted-foreground whitespace-nowrap">{shortDate(v.requested_date)}</Cell>
            <Cell right>{figure(num(v.total_estimated_cost), org.decimals)}</Cell>
          </tr>
        ))}
      </tbody>
    </Table>
      )}
    </Paged>
  )
}

function useSearchable() {
  const [search, setSearch] = useState('')
  const [type, setType] = useState('all')
  return { search, setSearch, type, setType }
}

export function Vouchers() {
  const { org, pro } = useApp()
  const canWrite = useCanWriteStock()
  const { search, setSearch, type, setType } = useSearchable()
  const [status, setStatus] = useState('all')
  const list = useQuery(vouchersQuery(org.id, status, type, search.trim()))
  const [opened, setOpened] = useState<Id | null>(null)
  const [creating, setCreating] = useState(false)
  return (
    <Screen search={<SearchIcon label="Search vouchers" placeholder="Search vouchers" value={search} onChange={setSearch} />}
      title="Inventory"
      sub={pro ? 'Purchase and issuance vouchers.' : 'Requests to buy stock or take it out, and where each one stands.'}
      actions={canWrite ? <button className={btn.primary} onClick={() => setCreating(true)}><Plus className="size-3.5 mr-1.5" />New voucher</button> : undefined}
      tabs={<Tabs items={INVENTORY_TABS} />}
    >
      <Toolbar>
        <Chips label="Type" value={type} onChange={setType} options={[{ id: 'all', label: 'All' }, { id: 'purchase', label: 'Purchases' }, { id: 'issuance', label: 'Issuances' }]} />
        <Chips label="Status" value={status} onChange={setStatus} options={[{ id: 'all', label: 'Any status' }, ...Object.entries(STATUS).map(([id, s]) => ({ id, label: s.label }))]} />
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No vouchers found" body={canWrite ? 'Create one when you need to buy stock or take it out.' : 'Nothing matches right now.'} /> : null)}>
        {(rows) => <VoucherTable rows={rows} onOpen={(v) => setOpened(v.id)} />}
      </Loaded>
      <VoucherDetail id={opened} onClose={() => setOpened(null)} />
      {creating ? <VoucherForm onClose={() => setCreating(false)} /> : null}
    </Screen>
  )
}

export function Approvals() {
  const { org, pro } = useApp()
  const { search, setSearch, type, setType } = useSearchable()
  const [status, setStatus] = useState('pending_finance')
  const stats = useQuery(statsQuery(org.id))
  const list = useQuery(vouchersQuery(org.id, status, type, search.trim()))
  const [opened, setOpened] = useState<Id | null>(null)
  return (
    <Screen search={<SearchIcon label="Search vouchers" placeholder="Search vouchers" value={search} onChange={setSearch} />} title="Approvals" sub={pro ? 'Vouchers awaiting a finance decision.' : 'Spending and stock requests waiting on a decision.'}>
      <Stats>
        <Stat label="Waiting" value={num(stats.data?.pending_approval)} tone={num(stats.data?.pending_approval) ? 'warn' : undefined} />
        <Stat label="Approved" value={num(stats.data?.approved)} />
        <Stat label="Rejected" value={num(stats.data?.rejected)} />
        <Stat label="Expired" value={num(stats.data?.expired)} />
      </Stats>
      <Toolbar>
        <Chips label="Type" value={type} onChange={setType} options={[{ id: 'all', label: 'All' }, { id: 'purchase', label: 'Purchases' }, { id: 'issuance', label: 'Issuances' }]} />
        <Chips label="Status" value={status} onChange={setStatus} options={[{ id: 'pending_finance', label: 'Needs approval', count: num(stats.data?.pending_approval) }, { id: 'approved', label: 'Approved', count: num(stats.data?.approved) }, { id: 'rejected', label: 'Rejected', count: num(stats.data?.rejected) }, { id: 'expired', label: 'Expired', count: num(stats.data?.expired) }, { id: 'all', label: 'Any status' }]} />
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title={status === 'pending_finance' ? "You're all caught up" : 'No vouchers found'} body={status === 'pending_finance' ? 'Nothing is waiting for a decision.' : 'Nothing matches right now.'} /> : null)}>
        {(rows) => <VoucherTable rows={rows} onOpen={(v) => setOpened(v.id)} />}
      </Loaded>
      <VoucherDetail id={opened} onClose={() => setOpened(null)} />
    </Screen>
  )
}

function VoucherDetail({ id, onClose }: { id: Id | null; onClose: () => void }) {
  const { org, access } = useApp()
  const detail = useQuery({ ...q<Voucher | null>(['voucher', id], 'VoucherService', 'getVoucher', [id]), enabled: id !== null })
  const v = detail.data
  const canAct = access !== 'observer'
  const canDecide = canAct
  const [reason, setReason] = useState('')
  const [actual, setActual] = useState<Record<string, string>>({})
  const [costs, setCosts] = useState<Record<string, string>>({})
  const done = (msg: string) => ({ success: msg, refresh: REFRESH, onDone: () => { setReason(''); setActual({}); setCosts({}) } })
  const submit = useSave(() => call('VoucherService', 'submitForApproval', [id, org.id]), done('Sent for approval'))
  const approve = useSave(() => call('VoucherService', 'approveVoucher', [id, reason.trim() || undefined]), done('Approved'))
  const reject = useSave(() => call('VoucherService', 'rejectVoucher', [id, reason.trim()]), done('Rejected'))
  const renew = useSave(() => call('VoucherService', 'renewExpiredVoucher', [id, reason.trim()]), done('Sent for approval again'))
  const execute = useSave(() => call('VoucherService', 'executeVoucher', [id, Object.fromEntries((v?.lines ?? []).map((l) => [l.id, Number(actual[String(l.id)] ?? num(l.quantity_requested))])), Object.fromEntries((v?.lines ?? []).filter((l) => costs[String(l.id)]).map((l) => [l.id, Number(costs[String(l.id)])]))]), done('Quantities recorded'))
  const complete = useSave(() => call('VoucherService', 'completeVoucher', [id]), done('Completed'))
  const remove = useSave(() => call('VoucherService', 'deleteVoucher', [id]), { success: 'Voucher deleted', refresh: REFRESH, onDone: onClose })
  const removeFile = useSave((fileId: Id) => call('VoucherService', 'deleteAttachment', [fileId]), { success: 'File removed', refresh: REFRESH })
  const busy = [submit, approve, reject, renew, execute, complete, remove].some((m) => m.isPending)
  const upload = async (file: File) => {
    try {
      await uploadAttachment(id!, file)
      toast.success('File attached')
      void detail.refetch()
    } catch (e) {
      toast.error(e instanceof Error ? e.message : 'Could not upload the file')
    }
  }

  return (
    <Modal wide open={id !== null} onClose={onClose} title={v ? `${v.voucher_number}` : 'Voucher'}>
      {!v ? <p className="text-muted-foreground">{detail.isPending ? 'Loading…' : "This voucher didn't load."}</p> : (
        <div className="flex flex-col gap-4 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <Badge dot tone={STATUS[v.status]?.tone}>{STATUS[v.status]?.label ?? v.status}</Badge>
            <span className="text-[13px] text-muted-foreground">{v.voucher_type === 'purchase' ? 'Purchase' : 'Issuance'} · {shortDate(v.requested_date)}{v.approval_deadline && v.status === 'pending_finance' ? ` · decide by ${shortDate(v.approval_deadline)}` : ''}</span>
          </div>
          <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-[13.5px]">
            {[['Vendor', v.vendor_name], ['Purpose', v.purpose], ['Destination', v.destination], ['Payment', v.payment_type ? v.payment_type[0].toUpperCase() + v.payment_type.slice(1).replace('_', ' ') : null], ['Description', v.description], ['Notes', v.notes], ['Reason', v.rejection_reason]].filter(([, x]) => x).map(([k, x]) => <div key={k as string}><dt className="text-[12px] text-muted-foreground">{k}</dt><dd>{x}</dd></div>)}
          </dl>
          <div className="border border-border rounded-[8px] overflow-x-auto">
            <table className="w-full text-[13px] min-w-[460px]">
              <thead><tr><Head>Item</Head><Head right>Requested</Head><Head right>Actual</Head>{v.status === 'approved' && v.voucher_type === 'purchase' && canAct ? <Head right>Unit cost</Head> : null}<Head right>Cost</Head></tr></thead>
              <tbody>
                {(v.lines ?? []).map((l) => (
                  <tr key={l.id}>
                    <Cell>{l.item?.name ?? `Item ${l.item_id}`}</Cell>
                    <Cell right>{figure(num(l.quantity_requested), 0)}</Cell>
                    <Cell right>{v.status === 'approved' && canAct
                      ? <Input aria-label={`Actual quantity of ${l.item?.name ?? l.item_id}`} inputMode="decimal" value={actual[String(l.id)] ?? String(num(l.quantity_requested))} onChange={(e) => setActual((a) => ({ ...a, [String(l.id)]: e.target.value }))} className="h-7 w-20 ml-auto text-right fig" />
                      : l.quantity_actual != null ? figure(num(l.quantity_actual), 0) : ''}</Cell>
                    {v.status === 'approved' && v.voucher_type === 'purchase' && canAct ? <Cell right><Input aria-label={`Actual unit cost of ${l.item?.name ?? l.item_id}`} inputMode="decimal" value={costs[String(l.id)] ?? String(num(l.unit_cost_estimated) || '')} onChange={(e) => setCosts((c) => ({ ...c, [String(l.id)]: e.target.value }))} className="h-7 w-24 ml-auto text-right fig" /></Cell> : null}
                    <Cell right>{figure(num(l.total_cost), org.decimals)}</Cell>
                  </tr>
                ))}
                <tr className="font-medium"><Cell className="border-b-0">Total</Cell><Cell className="border-b-0">{' '}</Cell><Cell className="border-b-0">{' '}</Cell>{v.status === 'approved' && v.voucher_type === 'purchase' && canAct ? <Cell className="border-b-0">{' '}</Cell> : null}<Cell right className="border-b-0">{figure(num(v.total_actual_cost ?? v.total_estimated_cost), org.decimals)}</Cell></tr>
              </tbody>
            </table>
          </div>

          <div>
            <h3 className="text-[12.5px] font-medium text-muted-foreground mb-1.5">Attachments</h3>
            <ul className="flex flex-col gap-1 text-[13px]">
              {(v.attachments ?? []).map((a) => <li key={a.id} className="flex items-center gap-2"><Paperclip className="size-3.5 text-muted-foreground" /><span className="truncate">{a.file_name}</span>{canAct ? <button aria-label={`Remove ${a.file_name}`} onClick={() => removeFile.mutate(a.id)} className="text-muted-foreground cursor-pointer"><X className="size-3.5" /></button> : null}</li>)}
            </ul>
            {canAct ? <label className="inline-flex items-center gap-1.5 mt-1.5 text-[13px] font-medium underline underline-offset-[3px] cursor-pointer"><input type="file" className="sr-only" onChange={(e) => { const f = e.target.files?.[0]; if (f) void upload(f); e.target.value = '' }} />Attach a file</label> : null}
          </div>

          {v.status === 'pending_finance' && canDecide ? <Text label="Note" hint="Required to reject. Optional to approve." value={reason} onChange={setReason} /> : null}
          {v.status === 'expired' && canAct ? <Text label="Why renew it?" required value={reason} onChange={setReason} /> : null}
          {v.status === 'receiving' || v.status === 'issuing' ? (access === 'owner' || access === 'books' ? <PostPanel voucher={v} /> : <p className="text-[13px] text-muted-foreground">Waiting for an accountant to post this to the books.</p>) : null}
          {v.status === 'posted' ? <p className="text-[13px] text-muted-foreground">Stock is updated and the entry is in your books. Completing just closes this voucher.</p> : null}

          <div className="flex flex-wrap gap-2 justify-end border-t border-border pt-3">
            <span className="mr-auto self-center"><AskChip prompt={`Explain voucher ${v.voucher_number} and what should happen next.`}>Explain this voucher</AskChip></span>
            {canAct && (v.status === 'draft' || v.status === 'rejected') ? <ConfirmDelete label="Delete" pending={busy} onConfirm={() => remove.mutate()} /> : null}
            {canAct && v.status === 'draft' ? <button className={btn.primary} disabled={busy} onClick={() => submit.mutate()}>Send for approval</button> : null}
            {canDecide && v.status === 'pending_finance' ? <><button className={btn.plain} disabled={busy || !reason.trim()} onClick={() => reject.mutate()}>Reject</button><button className={btn.primary} disabled={busy} onClick={() => approve.mutate()}>Approve</button></> : null}
            {canAct && v.status === 'approved' ? <button className={btn.primary} disabled={busy} onClick={() => execute.mutate()}>{v.voucher_type === 'purchase' ? 'Record what arrived' : 'Record what was issued'}</button> : null}
            {canAct && v.status === 'posted' ? <button className={btn.primary} disabled={busy} onClick={() => complete.mutate()}>Complete</button> : null}
            {canAct && v.status === 'expired' ? <button className={btn.primary} disabled={busy || !reason.trim()} onClick={() => renew.mutate()}>Renew and resubmit</button> : null}
          </div>
        </div>
      )}
    </Modal>
  )
}

type Preview = { total: number; problems: string[]; needs_payable: boolean; suggested_payable_account_id: number | null; lines: { account_id: number; code: string; name: string; debit: number; credit: number }[] }

/** Shows the exact entry before it's recorded, then posts it and the stock together. */
function PostPanel({ voucher: v }: { voucher: Voucher }) {
  const { org, pro } = useApp()
  const chart = useQuery(accounts(org.id))
  const [payable, setPayable] = useState('')
  const [date, setDate] = useState(today())
  const [warehouse, setWarehouse] = useState('')
  const warehouses = useQuery(warehousesQuery(org.id))
  const openWarehouses = (warehouses.data ?? []).filter((w) => w.is_active)
  const payableId = payable ? Number(payable) : null
  const preview = useQuery(q<Preview>(['voucher', v.id, 'preview', payableId], 'VoucherService', 'previewVoucherPosting', [v.id, { payable_account_id: payableId }]))
  const post = useSave(() => call('VoucherService', 'postVoucher', [v.id, { payable_account_id: payableId, date, warehouse_id: warehouse ? Number(warehouse) : null }]), { success: 'Posted. Stock and your books are updated.', refresh: REFRESH, onDone: refreshBooks })
  const p = preview.data
  const asking = p?.needs_payable || payable !== ''
  const liabilities = (chart.data ?? []).filter((a) => a.is_postable !== false && a.account_type === 'liability')
  return (
    <section className="border border-border rounded-[8px] p-3 flex flex-col gap-2.5" aria-label="Post to your books">
      <h3 className="font-semibold text-[13.5px]">{pro ? 'Post to the ledger' : 'Post to your books'}</h3>
      <p className="text-[13px] text-muted-foreground">{v.voucher_type === 'purchase' ? 'This adds the stock and records the entry below, together.' : 'This takes the stock out at its average cost and records the entry below, together.'}</p>
      {preview.isPending ? <p className="text-[13px] text-muted-foreground">Working it out…</p> : null}
      {preview.isError ? <p role="alert" className="text-[13px] text-destructive">{preview.error.message}</p> : null}
      {p?.lines.length ? (
        <table className="w-full text-[13px]">
          <thead><tr><Head>Account</Head><Head right>Debit</Head><Head right>Credit</Head></tr></thead>
          <tbody>{p.lines.map((l) => <tr key={`${l.account_id}-${l.debit}-${l.credit}`}><Cell><span className="fig text-muted-foreground mr-1.5">{l.code}</span>{l.name}</Cell><Cell right>{l.debit ? figure(l.debit, org.decimals) : ''}</Cell><Cell right>{l.credit ? figure(l.credit, org.decimals) : ''}</Cell></tr>)}</tbody>
        </table>
      ) : null}
      {p?.problems.length ? <ul role="alert" className="text-[13px] text-destructive flex flex-col gap-0.5">{p.problems.map((x) => <li key={x}>{x}</li>)}</ul> : null}
      <div className="grid sm:grid-cols-2 gap-3">
        {asking ? <Choice label="What you owe goes to" placeholder="Select account" value={payable} onChange={setPayable} options={liabilities.map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))} /> : null}
        <Text label="Date" type="date" value={date} onChange={setDate} />
        {openWarehouses.length > 1 ? <Choice label="Warehouse" placeholder="Default warehouse" value={warehouse} onChange={setWarehouse} options={openWarehouses.map((w) => ({ value: String(w.id), label: w.name }))} /> : null}
      </div>
      <div><button className={btn.primary} disabled={!p || p.problems.length > 0 || post.isPending} onClick={() => post.mutate()}>{post.isPending ? 'Posting…' : `Post ${p ? figure(p.total, org.decimals) : ''}`}</button></div>
    </section>
  )
}

type FormLine = { key: number; item_id: string; quantity: string; cost: string }
type Picker = { id: Id; supplier_code: string; name: string }

function VoucherForm({ onClose }: { onClose: () => void }) {
  const { org } = useApp()
  const itemList = useQuery(items(org.id))
  const chart = useQuery(accounts(org.id))
  const suppliers = useQuery(q<Picker[]>(['supplier-picker', org.id], 'SupplierService', 'getSuppliersForVoucher', [org.id]))
  const [f, setF] = useState({ voucher_type: 'purchase', description: '', notes: '', supplier_id: '', vendor_name: '', vendor_contact: '', purchase_order_number: '', expected_delivery_date: '', payment_type: 'credit', payment_account_id: '', deposit_amount: '', payment_reference: '', purpose: '', destination: '', cost_center: '', project_code: '', destination_account_id: '' })
  const [lines, setLines] = useState<FormLine[]>([{ key: 1, item_id: '', quantity: '', cost: '' }])
  const [nextKey, setNextKey] = useState(2)
  const set = (k: keyof typeof f) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const purchase = f.voucher_type === 'purchase'
  const postable = (chart.data ?? []).filter((a) => a.is_postable !== false).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))
  const good = lines.filter((l) => l.item_id && Number(l.quantity) > 0)
  const total = good.reduce((s, l) => s + Number(l.quantity) * (Number(l.cost) || 0), 0)
  const save = useSave(() => call('VoucherService', 'createVoucher', [{
    voucher_type: f.voucher_type,
    description: f.description.trim(),
    notes: f.notes.trim() || undefined,
    payment_type: purchase ? f.payment_type : 'cash',
    ...(purchase ? {
      supplier_id: f.supplier_id ? Number(f.supplier_id) : undefined,
      vendor_name: f.vendor_name.trim() || undefined,
      vendor_contact: f.vendor_contact.trim() || undefined,
      purchase_order_number: f.purchase_order_number.trim() || undefined,
      expected_delivery_date: f.expected_delivery_date || undefined,
      payment_account_id: f.payment_account_id ? Number(f.payment_account_id) : undefined,
      deposit_amount: f.deposit_amount ? Number(f.deposit_amount) : undefined,
      payment_reference: f.payment_reference.trim() || undefined,
    } : {
      purpose: f.purpose.trim() || undefined,
      destination: f.destination.trim() || undefined,
      cost_center: f.cost_center.trim() || undefined,
      project_code: f.project_code.trim() || undefined,
      destination_account_id: f.destination_account_id ? Number(f.destination_account_id) : undefined,
    }),
    lines: good.map((l) => ({ item_id: Number(l.item_id), quantity_requested: Number(l.quantity), unit_cost_estimated: l.cost ? Number(l.cost) : undefined })),
  }, org.id]), { success: 'Voucher created as a draft', refresh: REFRESH, onDone: onClose })

  return (
    <Modal wide open onClose={onClose} title="New voucher">
      <FormBody onSubmit={() => save.mutate()} submit="Create draft" pending={save.isPending} onCancel={onClose} disabled={!f.description.trim() || !good.length || (!purchase && !f.purpose.trim()) || (purchase && !f.vendor_name.trim())}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Choice label="Type" value={f.voucher_type} onChange={set('voucher_type')} options={[{ value: 'purchase', label: 'Buying stock (purchase)' }, { value: 'issuance', label: 'Taking stock out (issuance)' }]} />
          <Text label="Description" required value={f.description} onChange={set('description')} />
        </div>
        {purchase ? (
          <div className="grid sm:grid-cols-2 gap-3">
            <Choice label="Supplier" placeholder="None selected" value={f.supplier_id} onChange={(v) => setF((x) => ({ ...x, supplier_id: v, vendor_name: suppliers.data?.find((s) => String(s.id) === v)?.name ?? x.vendor_name }))} options={(suppliers.data ?? []).map((s) => ({ value: String(s.id), label: s.name }))} />
            <Text label="Vendor name" required value={f.vendor_name} onChange={set('vendor_name')} />
            <Text label="Vendor contact" value={f.vendor_contact} onChange={set('vendor_contact')} />
            <Text label="PO number" value={f.purchase_order_number} onChange={set('purchase_order_number')} />
            <Text label="Expected delivery" type="date" min={today()} value={f.expected_delivery_date} onChange={set('expected_delivery_date')} />
            <Choice label="Payment" value={f.payment_type} onChange={set('payment_type')} options={[['credit', 'On credit'], ['cash', 'Cash'], ['check', 'Check'], ['card', 'Card'], ['bank_transfer', 'Bank transfer'], ['partial', 'Partial payment']].map(([value, label]) => ({ value, label }))} />
            {f.payment_type !== 'credit' ? <>
              <Choice label="Paid from" placeholder="Select account" value={f.payment_account_id} onChange={set('payment_account_id')} options={postable} />
              <Text label="Payment reference" value={f.payment_reference} onChange={set('payment_reference')} />
            </> : null}
            {f.payment_type === 'partial' ? <Text label="Deposit amount" inputMode="decimal" value={f.deposit_amount} onChange={set('deposit_amount')} /> : null}
          </div>
        ) : (
          <div className="grid sm:grid-cols-2 gap-3">
            <Text label="Purpose" required value={f.purpose} onChange={set('purpose')} />
            <Text label="Destination" value={f.destination} onChange={set('destination')} />
            <Choice label="Cost goes to" placeholder="Use the item's category" value={f.destination_account_id} onChange={set('destination_account_id')} options={postable} />
            <Text label="Cost center" value={f.cost_center} onChange={set('cost_center')} />
            <Text label="Project code" value={f.project_code} onChange={set('project_code')} />
          </div>
        )}
        <div className="flex flex-col gap-1.5">
          <div className="grid grid-cols-[minmax(0,1fr)_84px_96px_24px] gap-1.5 text-[12px] text-muted-foreground"><span>Item</span><span className="text-right">Quantity</span><span className="text-right">Unit cost</span><span /></div>
          {lines.map((l) => (
            <div key={l.key} className="grid grid-cols-[minmax(0,1fr)_84px_96px_24px] gap-1.5 items-center">
              <select aria-label="Item" value={l.item_id} onChange={(e) => setLines((ls) => ls.map((x) => x.key === l.key ? { ...x, item_id: e.target.value, cost: x.cost || String(num(itemList.data?.find((i) => String(i.id) === e.target.value)?.average_unit_cost) || '') } : x))} className="h-8 min-w-0 w-full rounded-[6px] border border-input bg-transparent px-2 text-[13.5px]">
                <option value="">Select item</option>
                {(itemList.data ?? []).map((i) => <option key={i.id} value={String(i.id)}>{i.name}</option>)}
              </select>
              <Input aria-label="Quantity" inputMode="decimal" value={l.quantity} onChange={(e) => setLines((ls) => ls.map((x) => x.key === l.key ? { ...x, quantity: e.target.value } : x))} className="h-8 text-right fig" />
              <Input aria-label="Unit cost" inputMode="decimal" value={l.cost} onChange={(e) => setLines((ls) => ls.map((x) => x.key === l.key ? { ...x, cost: e.target.value } : x))} className="h-8 text-right fig" />
              <button type="button" aria-label="Remove line" disabled={lines.length < 2} onClick={() => setLines((ls) => ls.filter((x) => x.key !== l.key))} className="grid place-items-center text-muted-foreground cursor-pointer disabled:opacity-30"><X className="size-3.5" /></button>
            </div>
          ))}
          <div className="flex items-center justify-between mt-1">
            <button type="button" onClick={() => { setLines((ls) => [...ls, { key: nextKey, item_id: '', quantity: '', cost: '' }]); setNextKey((k) => k + 1) }} className="inline-flex items-center gap-1 text-[13px] font-medium cursor-pointer"><Plus className="size-3.5" />Add line</button>
            <span className="text-[13px]">Total <span className="fig font-medium ml-1">{figure(total, org.decimals)}</span></span>
          </div>
        </div>
        <Text label="Notes" value={f.notes} onChange={set('notes')} />
      </FormBody>
    </Modal>
  )
}
