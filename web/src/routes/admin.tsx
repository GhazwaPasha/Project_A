import { useState } from 'react'
import { useQuery, queryOptions } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { Input } from '@/components/ui/input'
import { CreateOrganization } from '@/components/auth'
import { Choice, FormBody, Modal, Pill, Stat, Stats, Text, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Screen, Table, btn } from '@/components/page'
import { call, rest } from '@/lib/api'
import { shortDate, useApp } from '@/lib/boot'
import { useTheme } from '@/lib/theme'
import { cn } from '@/lib/utils'

type Member = { id: string; user_id: string; email: string; full_name: string | null; role: string; joined_at?: string | null }
const ROLE_LABEL: Record<string, string> = { organization_owner: 'Owner', accountant: 'Accountant', member: 'Member', observer: 'Observer', super_admin: 'Platform admin' }
const ASSIGNABLE = [
  { value: 'accountant', label: 'Accountant', hint: 'Books, reports and approvals, but not organization settings.' },
  { value: 'member', label: 'Member', hint: 'Inventory, suppliers and vouchers.' },
  { value: 'observer', label: 'Observer', hint: 'Can view inventory only.' },
]

export function Team() {
  const { org, access, email } = useApp()
  const isOwner = access === 'owner'
  const list = useQuery(queryOptions<Member[]>({ queryKey: ['members', org.id], queryFn: () => rest<{ members: Member[] }>(`/api/organizations/${org.id}/members`).then((r) => r.members) }))
  const [search, setSearch] = useState('')
  const [adding, setAdding] = useState(false)
  const [newEmail, setNewEmail] = useState('')
  const [role, setRole] = useState('member')
  const add = useSave(() => rest(`/api/organizations/${org.id}/members`, { body: { email: newEmail.trim(), role } }), { success: 'Team member added', refresh: ['members'], onDone: () => { setAdding(false); setNewEmail(''); setRole('member') } })
  const change = useSave((v: { memberId: string; role: string }) => rest(`/api/organizations/${org.id}/members`, { method: 'PATCH', body: v }), { success: 'Role updated', refresh: ['members'] })
  const rows = (list.data ?? []).filter((m) => !search.trim() || `${m.email} ${m.full_name} ${ROLE_LABEL[m.role]}`.toLowerCase().includes(search.trim().toLowerCase()))
  return (
    <Screen
      title="Team Management"
      sub={`People who can access ${org.name}.`}
      actions={isOwner ? <button className={btn.primary} onClick={() => setAdding(true)}><Plus className="size-3.5 mr-1.5" />Add team member</button> : undefined}
    >
      <Input aria-label="Search team" placeholder="Search by name, email or role" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No team members" body="Add people to work with you." /> : null)}>
        {() => (
          <Table min={520}>
            <thead><tr><Head>Person</Head><Head>Role</Head><Head>Joined</Head></tr></thead>
            <tbody>
              {rows.map((m) => (
                <tr key={m.id}>
                  <Cell>{m.full_name || m.email}{m.email === email ? <span className="ml-2"><Pill>You</Pill></span> : null}<span className="block text-[12.5px] text-muted-foreground">{m.email}</span></Cell>
                  <Cell>{isOwner && m.role !== 'organization_owner'
                    ? <select aria-label={`Role for ${m.email}`} value={m.role} disabled={change.isPending} onChange={(e) => change.mutate({ memberId: m.id, role: e.target.value })} className="h-7 rounded-[6px] border border-input bg-transparent px-1.5 text-[13px]">{ASSIGNABLE.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}</select>
                    : ROLE_LABEL[m.role] ?? m.role}</Cell>
                  <Cell className="text-muted-foreground whitespace-nowrap">{m.joined_at ? shortDate(m.joined_at) : ''}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Loaded>
      <Modal open={adding} onClose={() => setAdding(false)} title="Add team member">
        <FormBody onSubmit={() => add.mutate()} submit="Add" pending={add.isPending} onCancel={() => setAdding(false)} disabled={!newEmail.trim()}>
          <Text label="Work email" hint="They need an Accountuitive account with this email." type="email" required value={newEmail} onChange={setNewEmail} />
          <Choice label="Role" value={role} onChange={setRole} hint={ASSIGNABLE.find((r) => r.value === role)?.hint} options={ASSIGNABLE} />
        </FormBody>
      </Modal>
    </Screen>
  )
}

const MONTHS = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12'].map((m, i) => ({ value: m, label: new Date(2000, i, 1).toLocaleDateString('en', { month: 'long' }) }))

export function OrganizationSettings() {
  const { org, access } = useApp()
  const s = org.settings
  const [f, setF] = useState({
    name: org.name, description: org.description ?? '',
    legalName: s?.companyInfo.legalName ?? '', taxId: s?.companyInfo.taxId ?? '', registrationNumber: s?.companyInfo.registrationNumber ?? '', industry: s?.companyInfo.industry ?? '', website: s?.companyInfo.website ?? '', email: s?.companyInfo.email ?? '', phone: s?.companyInfo.phone ?? '',
    street: s?.companyInfo.address.street ?? '', city: s?.companyInfo.address.city ?? '', state: s?.companyInfo.address.state ?? '', zipCode: s?.companyInfo.address.zipCode ?? '', country: s?.companyInfo.address.country ?? '',
    reportingCurrency: org.currency, decimalPlaces: String(org.decimals), fiscalYearStart: String(s?.accountingSettings.fiscalYearStart ?? '01').slice(0, 2),
    lowBalanceAlert: String(s?.notificationSettings.lowBalanceAlert ?? ''), sessionTimeout: String(s?.securitySettings.sessionTimeout ?? ''),
  })
  const set = (k: keyof typeof f) => (v: string) => setF((x) => ({ ...x, [k]: v }))
  const save = useSave(() => rest(`/api/organizations/${org.id}`, { method: 'PATCH', body: {
    name: f.name.trim(),
    description: f.description.trim() || null,
    settings: {
      companyInfo: { legalName: f.legalName, taxId: f.taxId, registrationNumber: f.registrationNumber, industry: f.industry, website: f.website, email: f.email, phone: f.phone, address: { street: f.street, city: f.city, state: f.state, zipCode: f.zipCode, country: f.country } },
      accountingSettings: { ...s?.accountingSettings, reportingCurrency: f.reportingCurrency.trim().toUpperCase(), decimalPlaces: Number(f.decimalPlaces) || 0, fiscalYearStart: f.fiscalYearStart },
      notificationSettings: { ...s?.notificationSettings, lowBalanceAlert: Number(f.lowBalanceAlert) || 0 },
      securitySettings: { ...s?.securitySettings, sessionTimeout: Number(f.sessionTimeout) || 0 },
    },
  } }), { success: 'Organization saved', refresh: ['bootstrap'] })
  if (access !== 'owner') return <Screen title="Organization Settings"><Empty title="Owners only" body="Ask the organization owner to change these settings." /></Screen>
  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => <section className="sheet p-5 flex flex-col gap-3"><h2 className="font-semibold text-[14px]">{title}</h2><div className="grid sm:grid-cols-2 gap-3">{children}</div></section>
  return (
    <Screen title="Organization Settings" sub="Details used across your books and reports.">
      <FormBody onSubmit={() => save.mutate()} submit="Save changes" pending={save.isPending} disabled={!f.name.trim()}>
        {Section({ title: 'General', children: <>
          <Text label="Organization name" required value={f.name} onChange={set('name')} />
          <Text label="Description" value={f.description} onChange={set('description')} />
          <Text label="Legal name" value={f.legalName} onChange={set('legalName')} />
          <Text label="Industry" value={f.industry} onChange={set('industry')} />
          <Text label="Tax ID" value={f.taxId} onChange={set('taxId')} />
          <Text label="Registration number" value={f.registrationNumber} onChange={set('registrationNumber')} />
        </> })}
        {Section({ title: 'Contact and address', children: <>
          <Text label="Email" type="email" value={f.email} onChange={set('email')} />
          <Text label="Phone" value={f.phone} onChange={set('phone')} />
          <Text label="Website" value={f.website} onChange={set('website')} />
          <Text label="Street" value={f.street} onChange={set('street')} />
          <Text label="City" value={f.city} onChange={set('city')} />
          <Text label="State" value={f.state} onChange={set('state')} />
          <Text label="Postal code" value={f.zipCode} onChange={set('zipCode')} />
          <Text label="Country" value={f.country} onChange={set('country')} />
        </> })}
        {Section({ title: 'Accounting', children: <>
          <Text label="Reporting currency" hint="Three-letter code, for example PKR or USD." maxLength={3} value={f.reportingCurrency} onChange={set('reportingCurrency')} />
          <Choice label="Decimal places" value={f.decimalPlaces} onChange={set('decimalPlaces')} options={['0', '2', '3'].map((v) => ({ value: v, label: v }))} />
          <Choice label="Fiscal year starts" value={f.fiscalYearStart} onChange={set('fiscalYearStart')} options={MONTHS} />
          <Text label="Low cash alert" hint="Warn when cash falls below this amount." inputMode="decimal" value={f.lowBalanceAlert} onChange={set('lowBalanceAlert')} />
        </> })}
      </FormBody>
    </Screen>
  )
}

export function Settings() {
  const { userId, profile, email, pro, setPro, orgs } = useApp()
  const { dark, toggle } = useTheme()
  const [name, setName] = useState(profile?.full_name ?? '')
  const [phone, setPhone] = useState(profile?.phone ?? '')
  const [addingOrg, setAddingOrg] = useState(false)
  const save = useSave(() => call('DataService', 'updateUserProfile', [userId, { full_name: name.trim() || null, phone: phone.trim() || null }]), { success: 'Profile saved', refresh: ['bootstrap'] })
  const segment = (active: boolean) => cn('h-7 px-3 rounded-[5px] text-[13px] cursor-pointer', active ? 'bg-card font-medium shadow-[0_0_0_1px_var(--border)]' : 'text-muted-foreground')
  return (
    <Screen title="Settings" sub={email}>
      <section className="sheet p-5">
        <h2 className="font-semibold text-[14px] mb-3">Profile</h2>
        <FormBody onSubmit={() => save.mutate()} submit="Save profile" pending={save.isPending}>
          <div className="grid sm:grid-cols-2 gap-3">
            <Text label="Full name" autoComplete="name" value={name} onChange={setName} />
            <Text label="Phone" autoComplete="tel" value={phone} onChange={setPhone} />
          </div>
        </FormBody>
      </section>
      <section className="sheet p-5 flex flex-col gap-4">
        <h2 className="font-semibold text-[14px]">Preferences</h2>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="font-medium text-[13.5px]">Appearance</p><p className="text-[12.5px] text-muted-foreground">Light or dark theme.</p></div>
          <div className="flex p-0.5 rounded-[7px] border border-border bg-muted" role="group" aria-label="Appearance"><button aria-pressed={!dark} onClick={() => { if (dark) toggle() }} className={segment(!dark)}>Light</button><button aria-pressed={dark} onClick={() => { if (!dark) toggle() }} className={segment(dark)}>Dark</button></div>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><p className="font-medium text-[13.5px]">Level of detail</p><p className="text-[12.5px] text-muted-foreground">Simple uses everyday words. Accountant shows codes, debits and credits.</p></div>
          <div className="flex p-0.5 rounded-[7px] border border-border bg-muted" role="group" aria-label="Level of detail"><button aria-pressed={!pro} onClick={() => setPro(false)} className={segment(!pro)}>Simple</button><button aria-pressed={pro} onClick={() => setPro(true)} className={segment(pro)}>Accountant</button></div>
        </div>
      </section>
      <section className="sheet p-5">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="font-semibold text-[14px]">Organizations</h2><p className="text-[12.5px] text-muted-foreground">You belong to {orgs.length}. Switch between them from the top of the sidebar.</p></div>
          <button className={btn.plain} onClick={() => setAddingOrg(true)}>New organization</button>
        </div>
      </section>
      <Modal open={addingOrg} onClose={() => setAddingOrg(false)} title="New organization"><CreateOrganization /></Modal>
    </Screen>
  )
}

type Overview = {
  stats: { totalUsers: number; totalOrganizations: number; superAdmins: number; activeMemberships: number }
  users: { id: string; email: string; full_name: string | null; is_super_admin: boolean }[]
  organizations: { id: string; name: string; member_count: number; owner_emails: string[]; created_at: string }[]
  memberships: { id: string; organization_name: string; email: string; role: string }[]
}

export function SuperAdmin() {
  const { isSuperAdmin, email } = useApp()
  const data = useQuery({ ...queryOptions({ queryKey: ['super-admin'], queryFn: () => rest<Overview>('/api/super-admin/overview') }), enabled: isSuperAdmin })
  const [search, setSearch] = useState('')
  const [tab, setTab] = useState<'users' | 'organizations' | 'memberships'>('users')
  const setAdmin = useSave((v: { userId: string; isSuperAdmin: boolean }) => rest('/api/super-admin/users', { method: 'PATCH', body: v }), { success: 'User updated', refresh: ['super-admin', 'bootstrap'] })
  const setRole = useSave((v: { membershipId: string; role: string }) => rest('/api/super-admin/memberships', { method: 'PATCH', body: v }), { success: 'Role updated', refresh: ['super-admin'] })
  if (!isSuperAdmin) return <Screen title="Super Admin"><Empty title="Super admins only" body="This area is for platform administrators." /></Screen>
  const match = (...v: (string | null | undefined)[]) => !search.trim() || v.join(' ').toLowerCase().includes(search.trim().toLowerCase())
  return (
    <Screen title="Super Admin" sub="Every user and organization on the platform.">
      <Loaded query={data}>
        {(o) => (
          <>
            <Stats>
              <Stat label="Users" value={o.stats.totalUsers} />
              <Stat label="Organizations" value={o.stats.totalOrganizations} />
              <Stat label="Super admins" value={o.stats.superAdmins} />
              <Stat label="Active memberships" value={o.stats.activeMemberships} />
            </Stats>
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex p-0.5 rounded-[7px] border border-border bg-muted text-[13px]" role="group" aria-label="Show">
                {(['users', 'organizations', 'memberships'] as const).map((t) => <button key={t} aria-pressed={tab === t} onClick={() => setTab(t)} className={cn('h-7 px-3 rounded-[5px] capitalize cursor-pointer', tab === t ? 'bg-card font-medium shadow-[0_0_0_1px_var(--border)]' : 'text-muted-foreground')}>{t}</button>)}
              </div>
              <Input aria-label="Search" placeholder="Search" value={search} onChange={(e) => setSearch(e.target.value)} className="h-8 max-w-sm" />
            </div>
            {tab === 'users' ? (
              <Table>
                <thead><tr><Head>User</Head><Head>Super admin</Head></tr></thead>
                <tbody>{o.users.filter((u) => match(u.email, u.full_name)).map((u) => (
                  <tr key={u.id}><Cell>{u.full_name || u.email}{u.email === email ? <span className="ml-2"><Pill>You</Pill></span> : null}<span className="block text-[12.5px] text-muted-foreground">{u.email}</span></Cell>
                  <Cell><label className="inline-flex items-center gap-2 cursor-pointer"><input type="checkbox" aria-label={`Super admin: ${u.email}`} checked={u.is_super_admin} disabled={setAdmin.isPending || u.email === email} onChange={(e) => setAdmin.mutate({ userId: u.id, isSuperAdmin: e.target.checked })} />{u.is_super_admin ? 'Yes' : 'No'}</label></Cell></tr>
                ))}</tbody>
              </Table>
            ) : tab === 'organizations' ? (
              <Table>
                <thead><tr><Head>Organization</Head><Head>Owners</Head><Head right>Members</Head><Head>Created</Head></tr></thead>
                <tbody>{o.organizations.filter((x) => match(x.name, x.owner_emails.join(' '))).map((x) => <tr key={x.id}><Cell>{x.name}</Cell><Cell className="text-muted-foreground">{x.owner_emails.join(', ')}</Cell><Cell right>{x.member_count}</Cell><Cell className="text-muted-foreground whitespace-nowrap">{shortDate(x.created_at)}</Cell></tr>)}</tbody>
              </Table>
            ) : (
              <Table>
                <thead><tr><Head>Person</Head><Head>Organization</Head><Head>Role</Head></tr></thead>
                <tbody>{o.memberships.filter((m) => match(m.email, m.organization_name, m.role)).map((m) => (
                  <tr key={m.id}><Cell>{m.email}</Cell><Cell className="text-muted-foreground">{m.organization_name}</Cell>
                  <Cell>{m.role === 'organization_owner' ? 'Owner' : <select aria-label={`Role for ${m.email} in ${m.organization_name}`} value={m.role} disabled={setRole.isPending} onChange={(e) => setRole.mutate({ membershipId: m.id, role: e.target.value })} className="h-7 rounded-[6px] border border-input bg-transparent px-1.5 text-[13px]">{ASSIGNABLE.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}</select>}</Cell></tr>
                ))}</tbody>
              </Table>
            )}
          </>
        )}
      </Loaded>
    </Screen>
  )
}
