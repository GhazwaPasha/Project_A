import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Plus, Star, Trash2 } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { AskLink } from '@/components/agent-panel'
import { Choice, ConfirmDelete, FormBody, Modal, Pill, Stat, Stats, Text, Toggle, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Range, Screen, Table, btn } from '@/components/page'
import { call } from '@/lib/api'
import { figure, useApp } from '@/lib/boot'
import { accounts, num, q, type Id, type Money } from '@/lib/data'

type Terms = 'net_15' | 'net_30' | 'net_45' | 'net_60' | 'due_on_receipt' | 'cash_on_delivery' | 'prepaid'
type Supplier = { id: Id; supplier_code: string; name: string; legal_name?: string | null; description?: string | null; contact_person?: string | null; email?: string | null; phone?: string | null; fax?: string | null; website?: string | null; billing_address_line1?: string | null; billing_address_line2?: string | null; billing_city?: string | null; billing_state?: string | null; billing_postal_code?: string | null; billing_country?: string | null; shipping_address_line1?: string | null; shipping_city?: string | null; shipping_state?: string | null; shipping_postal_code?: string | null; shipping_country?: string | null; tax_id?: string | null; registration_number?: string | null; currency: string; credit_limit?: Money | null; current_balance?: Money | null; payment_terms?: Terms | null; status: 'active' | 'inactive' | 'suspended'; is_preferred: boolean; notes?: string | null }
type Contact = { id: Id; name: string; title?: string | null; email?: string | null; phone?: string | null; mobile?: string | null; is_primary: boolean; is_billing: boolean }
type Mappings = { payable_account_id?: Id | null; cash_account_id?: Id | null; expense_account_id?: Id | null; inventory_account_id?: Id | null }

const TERMS: { value: Terms; label: string }[] = [{ value: 'net_15', label: 'Net 15 days' }, { value: 'net_30', label: 'Net 30 days' }, { value: 'net_45', label: 'Net 45 days' }, { value: 'net_60', label: 'Net 60 days' }, { value: 'due_on_receipt', label: 'Due on receipt' }, { value: 'cash_on_delivery', label: 'Cash on delivery' }, { value: 'prepaid', label: 'Prepaid' }]
const STATUS_TONE = { active: 'good', inactive: 'neutral', suspended: 'bad' } as const
const REFRESH = ['suppliers', 'supplier', 'supplier-picker', 'supplier-stats']

const blank = { supplier_code: '', name: '', legal_name: '', description: '', contact_person: '', email: '', phone: '', website: '', billing_address_line1: '', billing_city: '', billing_state: '', billing_postal_code: '', billing_country: '', tax_id: '', registration_number: '', currency: '', credit_limit: '', payment_terms: 'net_30', status: 'active', is_preferred: false, notes: '', payable_account_id: '' }
type Draft = typeof blank & { id?: Id }

export function Suppliers() {
  const { org, pro, access } = useApp()
  const canWrite = access !== 'observer'
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('all')
  const filters = { ...(search.trim() ? { search: search.trim() } : {}), ...(status !== 'all' ? { status: [status] } : {}) }
  const list = useQuery(q<Supplier[]>(['suppliers', org.id, search.trim(), status], 'SupplierService', 'getSuppliers', [org.id, filters]))
  const all = list.data ?? []
  const [draft, setDraft] = useState<Draft | null>(null)
  const [opened, setOpened] = useState<Supplier | null>(null)
  const owed = all.reduce((s, x) => s + num(x.current_balance), 0)
  return (
    <Screen
      title="Suppliers"
      sub={pro ? 'Vendor records, terms and account mappings.' : 'The businesses you buy from.'}
      actions={canWrite ? <button className={btn.primary} onClick={() => setDraft({ ...blank, currency: org.currency })}><Plus className="size-3.5 mr-1.5" />New supplier</button> : undefined}
    >
      <Stats cols={3}>
        <Stat label="Suppliers" value={all.length} />
        <Stat label="Preferred" value={all.filter((s) => s.is_preferred).length} />
        <Stat label={pro ? 'Current balance' : 'You owe them'} value={`${org.currency} ${figure(owed, 0)}`} />
      </Stats>
      <div className="flex flex-wrap items-center gap-2">
        <Input aria-label="Search suppliers" placeholder="Search suppliers" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
        <Range label="Status" value={status} onChange={setStatus} options={[{ id: 'all', label: 'All statuses' }, { id: 'active', label: 'Active' }, { id: 'inactive', label: 'Inactive' }, { id: 'suspended', label: 'Suspended' }]} />
      </div>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No suppliers found" body={canWrite ? 'Add the businesses you buy from.' : 'Nothing matches right now.'} /> : null)}>
        {() => (
          <Table min={620}>
            <thead><tr><Head>Supplier</Head><Head>Contact</Head><Head>Terms</Head><Head>Status</Head><Head right>Balance</Head></tr></thead>
            <tbody>
              {all.map((s) => (
                <tr key={s.id} tabIndex={0} className="cursor-pointer hover:bg-accent/50 focus-visible:bg-accent/50 outline-none" onClick={() => setOpened(s)} onKeyDown={(e) => { if (e.key === 'Enter') setOpened(s) }}>
                  <Cell><span className="flex items-center gap-1.5">{s.name}{s.is_preferred ? <Star aria-label="Preferred" className="size-3 fill-current text-[var(--note)]" /> : null}</span>{pro ? <span className="fig text-[12px] text-muted-foreground">{s.supplier_code}</span> : null}</Cell>
                  <Cell className="text-muted-foreground">{s.contact_person || s.email || s.phone || ''}</Cell>
                  <Cell className="text-muted-foreground">{TERMS.find((t) => t.value === s.payment_terms)?.label ?? ''}</Cell>
                  <Cell><Pill tone={STATUS_TONE[s.status]}>{s.status[0].toUpperCase() + s.status.slice(1)}</Pill></Cell>
                  <Cell right>{figure(num(s.current_balance), org.decimals)}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Loaded>
      <SupplierForm key={String(draft?.id ?? (draft ? 'new' : 'closed'))} draft={draft} onClose={() => setDraft(null)} />
      {opened ? <SupplierDetail supplier={opened} canWrite={canWrite} onClose={() => setOpened(null)} onEdit={(d) => { setOpened(null); setDraft(d) }} /> : null}
    </Screen>
  )
}

function SupplierForm({ draft, onClose }: { draft: Draft | null; onClose: () => void }) {
  const { org } = useApp()
  const chart = useQuery({ ...accounts(org.id), enabled: draft !== null })
  const [f, setF] = useState<Draft>(draft ?? blank)
  const set = (k: keyof Draft) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const options = (chart.data ?? []).filter((a) => a.is_postable !== false).map((a) => ({ value: String(a.id), label: `${a.code} ${a.name}` }))
  const save = useSave(async () => {
    const { id, payable_account_id, credit_limit, ...rest } = f
    const fields = { ...Object.fromEntries(Object.entries(rest).map(([k, v]) => [k, typeof v === 'string' ? v.trim() || undefined : v])), credit_limit: credit_limit ? Number(credit_limit) : undefined, account_mappings: payable_account_id ? { payable_account_id: Number(payable_account_id) } : undefined }
    return id != null ? call('SupplierService', 'updateSupplier', [id, fields]) : call('SupplierService', 'createSupplier', [fields, org.id])
  }, { success: 'Supplier saved', refresh: REFRESH, onDone: onClose })
  const needsPayable = f.id == null
  return (
    <Modal wide open={draft !== null} onClose={onClose} title={f.id != null ? 'Edit supplier' : 'New supplier'}>
      <FormBody onSubmit={() => save.mutate()} submit="Save supplier" pending={save.isPending} onCancel={onClose} disabled={!f.name.trim() || (needsPayable && !f.payable_account_id)}>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text label="Supplier name" required value={f.name} onChange={set('name')} />
          <Text label="Supplier code" hint="Leave blank to number it automatically." value={f.supplier_code} onChange={set('supplier_code')} />
          <Text label="Contact person" value={f.contact_person} onChange={set('contact_person')} />
          <Text label="Email" type="email" value={f.email} onChange={set('email')} />
          <Text label="Phone" value={f.phone} onChange={set('phone')} />
          <Text label="Website" value={f.website} onChange={set('website')} />
        </div>
        <h3 className="text-[12.5px] font-medium text-muted-foreground -mb-1">Terms</h3>
        <div className="grid sm:grid-cols-3 gap-3">
          <Choice label="Payment terms" value={f.payment_terms} onChange={set('payment_terms')} options={TERMS} />
          <Text label="Currency" value={f.currency} onChange={set('currency')} />
          <Text label="Credit limit" inputMode="decimal" value={f.credit_limit} onChange={set('credit_limit')} />
          <Choice label="Status" value={f.status} onChange={set('status')} options={[{ value: 'active', label: 'Active' }, { value: 'inactive', label: 'Inactive' }, { value: 'suspended', label: 'Suspended' }]} />
          {needsPayable ? <Choice className="sm:col-span-2" label="Payable account" hint="Where what you owe this supplier is tracked." required placeholder="Select account" value={f.payable_account_id} onChange={set('payable_account_id')} options={options} /> : null}
        </div>
        <Toggle label="Preferred supplier" checked={f.is_preferred} onChange={(v) => setF((x) => ({ ...x, is_preferred: v }))} />
        <h3 className="text-[12.5px] font-medium text-muted-foreground -mb-1">Address</h3>
        <div className="grid sm:grid-cols-2 gap-3">
          <Text className="sm:col-span-2" label="Street" value={f.billing_address_line1} onChange={set('billing_address_line1')} />
          <Text label="City" value={f.billing_city} onChange={set('billing_city')} />
          <Text label="State" value={f.billing_state} onChange={set('billing_state')} />
          <Text label="Postal code" value={f.billing_postal_code} onChange={set('billing_postal_code')} />
          <Text label="Country" value={f.billing_country} onChange={set('billing_country')} />
        </div>
        <h3 className="text-[12.5px] font-medium text-muted-foreground -mb-1">Business details</h3>
        <div className="grid sm:grid-cols-3 gap-3">
          <Text label="Legal name" value={f.legal_name} onChange={set('legal_name')} />
          <Text label="Tax ID" value={f.tax_id} onChange={set('tax_id')} />
          <Text label="Registration number" value={f.registration_number} onChange={set('registration_number')} />
        </div>
        <Text label="Notes" value={f.notes} onChange={set('notes')} />
      </FormBody>
    </Modal>
  )
}

function SupplierDetail({ supplier: s, canWrite, onClose, onEdit }: { supplier: Supplier; canWrite: boolean; onClose: () => void; onEdit: (d: Draft) => void }) {
  const { org, pro } = useApp()
  const contacts = useQuery(q<Contact[]>(['supplier', s.id, 'contacts'], 'SupplierService', 'getSupplierContacts', [s.id]))
  const mapping = useQuery({ ...q<Mappings | null>(['supplier', s.id, 'mappings'], 'SupplierService', 'getSupplierAccountMappings', [s.id]), enabled: pro })
  const chart = useQuery({ ...accounts(org.id), enabled: pro })
  const [adding, setAdding] = useState(false)
  const [c, setC] = useState({ name: '', title: '', email: '', phone: '', is_primary: false })
  const add = useSave(() => call('SupplierService', 'addSupplierContact', [s.id, { name: c.name.trim(), title: c.title.trim() || undefined, email: c.email.trim() || undefined, phone: c.phone.trim() || undefined, is_primary: c.is_primary, is_billing: false, is_shipping: false, is_technical: false }]), { success: 'Contact added', refresh: REFRESH, onDone: () => { setAdding(false); setC({ name: '', title: '', email: '', phone: '', is_primary: false }) } })
  const removeContact = useSave((id: Id) => call('SupplierService', 'deleteSupplierContact', [id]), { success: 'Contact removed', refresh: REFRESH })
  const remove = useSave(() => call('SupplierService', 'deleteSupplier', [s.id]), { success: 'Supplier deleted', refresh: REFRESH, onDone: onClose })
  const accountName = (id?: Id | null) => (chart.data ?? []).find((a) => String(a.id) === String(id))
  const payable = accountName(mapping.data?.payable_account_id)
  const edit = () => onEdit({ ...blank, ...Object.fromEntries(Object.entries(s).filter(([k, v]) => k in blank && v != null).map(([k, v]) => [k, typeof v === 'number' ? String(v) : v])), id: s.id })
  return (
    <Modal wide open onClose={onClose} title={s.name}>
      <div className="flex flex-col gap-4 min-w-0">
        <div className="flex flex-wrap items-center gap-2"><Pill tone={STATUS_TONE[s.status]}>{s.status[0].toUpperCase() + s.status.slice(1)}</Pill>{s.is_preferred ? <Pill tone="warn">Preferred</Pill> : null}<span className="fig text-[12.5px] text-muted-foreground">{s.supplier_code}</span></div>
        <dl className="grid sm:grid-cols-2 gap-x-6 gap-y-2 text-[13.5px]">
          {[['Email', s.email], ['Phone', s.phone], ['Website', s.website], ['Terms', TERMS.find((t) => t.value === s.payment_terms)?.label], ['Credit limit', s.credit_limit != null ? `${s.currency} ${figure(num(s.credit_limit), org.decimals)}` : null], ['Balance', `${s.currency} ${figure(num(s.current_balance), org.decimals)}`], ['Tax ID', s.tax_id], ['Address', [s.billing_address_line1, s.billing_city, s.billing_country].filter(Boolean).join(', ')], ['Payable account', pro && payable ? `${payable.code} ${payable.name}` : null], ['Notes', s.notes]].filter(([, v]) => v).map(([k, v]) => <div key={k as string}><dt className="text-[12px] text-muted-foreground">{k}</dt><dd>{v}</dd></div>)}
        </dl>
        <section>
          <div className="flex items-center justify-between mb-1.5"><h3 className="text-[13px] font-medium">Contacts</h3>{canWrite ? <button onClick={() => setAdding((a) => !a)} className="text-[13px] font-medium underline underline-offset-[3px] cursor-pointer">{adding ? 'Cancel' : 'Add contact'}</button> : null}</div>
          {adding ? (
            <div className="border border-border rounded-[8px] p-3 mb-2">
              <FormBody onSubmit={() => add.mutate()} submit="Add contact" pending={add.isPending} disabled={!c.name.trim()}>
                <div className="grid sm:grid-cols-2 gap-3">
                  <Text label="Name" required value={c.name} onChange={(v) => setC((x) => ({ ...x, name: v }))} />
                  <Text label="Title" value={c.title} onChange={(v) => setC((x) => ({ ...x, title: v }))} />
                  <Text label="Email" type="email" value={c.email} onChange={(v) => setC((x) => ({ ...x, email: v }))} />
                  <Text label="Phone" value={c.phone} onChange={(v) => setC((x) => ({ ...x, phone: v }))} />
                </div>
                <Toggle label="Primary contact" checked={c.is_primary} onChange={(v) => setC((x) => ({ ...x, is_primary: v }))} />
              </FormBody>
            </div>
          ) : null}
          <Loaded query={contacts} empty={(d) => (d.length === 0 ? <p className="text-[13px] text-muted-foreground">No contacts yet.</p> : null)}>
            {(rows) => (
              <ul className="flex flex-col divide-y divide-border border border-border rounded-[8px]">
                {rows.map((x) => (
                  <li key={x.id} className="flex items-center justify-between gap-3 px-3 py-2 text-[13.5px]">
                    <span className="min-w-0"><span className="font-medium">{x.name}</span>{x.is_primary ? <span className="ml-2"><Pill>Primary</Pill></span> : null}<span className="block text-[12.5px] text-muted-foreground truncate">{[x.title, x.email, x.phone].filter(Boolean).join(' · ')}</span></span>
                    {canWrite ? <button aria-label={`Remove ${x.name}`} onClick={() => removeContact.mutate(x.id)} className="text-muted-foreground cursor-pointer"><Trash2 className="size-3.5" /></button> : null}
                  </li>
                ))}
              </ul>
            )}
          </Loaded>
        </section>
        <div className="flex flex-wrap gap-2 justify-end border-t border-border pt-3">
          <AskLink className="text-[13px] mr-auto self-center" prompt={`What have we bought from ${s.name}, and how much do we owe them?`}>Ask about this supplier</AskLink>
          {canWrite ? <><ConfirmDelete label="Delete" pending={remove.isPending} onConfirm={() => remove.mutate()} /><button className={btn.primary} onClick={edit}>Edit</button></> : null}
        </div>
      </div>
    </Modal>
  )
}
