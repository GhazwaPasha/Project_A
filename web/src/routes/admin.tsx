import { useState } from 'react'
import { useQuery, queryOptions } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { Input } from '@/components/ui/input'
import { CreateOrganization } from '@/components/auth'
import { Choice, FormBody, Modal, Stat, Stats, Text, selectInline, useSave } from '@/components/form'
import { Cell, Empty, Head, Loaded, Paged, Screen, SearchIcon, SettingsTabs, Table, Toolbar, btn } from '@/components/page'
import { Badge, Chip, Chips } from '@/components/chips'
import { call, rest } from '@/lib/api'
import { shortDate, useApp } from '@/lib/boot'
import type { Id } from '@/lib/data'
import { useTheme } from '@/lib/theme'
import { cn } from '@/lib/utils'

type Member = { id: string; user_id: string; email: string; full_name: string | null; role: string; joined_at?: string | null }
const ROLE_LABEL: Record<string, string> = { organization_owner: 'Owner', accountant: 'Accountant', member: 'Member', observer: 'Observer', super_admin: 'Platform admin' }
const ASSIGNABLE = [
  { value: 'accountant', label: 'Accountant', hint: 'Books, reports and approvals, but not organization settings.' },
  { value: 'member', label: 'Member', hint: 'Inventory, suppliers and vouchers.' },
  { value: 'observer', label: 'Observer', hint: 'Can view inventory only.' },
]

type Invite = { id: Id; email: string; role: string; expires_at: string }

export function Team() {
  const { org, access, email } = useApp()
  const isOwner = access === 'owner'
  const list = useQuery(queryOptions<Member[]>({ queryKey: ['members', org.id], queryFn: () => rest<{ members: Member[] }>(`/api/organizations/${org.id}/members`).then((r) => r.members) }))
  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState('all')
  const [adding, setAdding] = useState(false)
  const [newEmail, setNewEmail] = useState('')
  const [role, setRole] = useState('member')
  const invites = useQuery({ ...queryOptions<{ invites: Invite[] }>({ queryKey: ['invites', org.id], queryFn: () => rest<{ invites: Invite[] }>(`/api/organizations/${org.id}/invites`) }), enabled: isOwner })
  const [link, setLink] = useState<{ email: string; url: string } | null>(null)
  const revoke = useSave((id: Id) => rest(`/api/organizations/${org.id}/invites?id=${id}`, { method: 'DELETE' }), { success: 'Invite cancelled', refresh: ['invites'] })
  const add = useSave(async () => {
    const r = await rest<{ invite?: { token: string; email: string } }>(`/api/organizations/${org.id}/members`, { body: { email: newEmail.trim(), role } })
    if (r.invite) setLink({ email: r.invite.email, url: `${location.origin}/invite/${r.invite.token}` })
    return r
  }, { refresh: ['members', 'invites'], onDone: () => { setAdding(false); setNewEmail(''); setRole('member') } })
  const change = useSave((v: { memberId: string; role: string }) => rest(`/api/organizations/${org.id}/members`, { method: 'PATCH', body: v }), { success: 'Role updated', refresh: ['members'] })
  const everyone = list.data ?? []
  const roles = [...new Set(everyone.map((m) => m.role))]
  const rows = everyone.filter((m) => roleFilter === 'all' || m.role === roleFilter).filter((m) => !search.trim() || `${m.email} ${m.full_name} ${ROLE_LABEL[m.role]}`.toLowerCase().includes(search.trim().toLowerCase()))
  return (
    <Screen search={<SearchIcon label="Search team" placeholder="Search team" value={search} onChange={setSearch} />}
      title="Team Management"
     
      actions={isOwner ? <button className={btn.primary} onClick={() => setAdding(true)}><Plus className="size-3.5 mr-1.5" />Add team member</button> : undefined}
    >
      <Toolbar>
        <Chips label="Role" value={roleFilter} onChange={setRoleFilter} options={[{ id: 'all', label: 'Everyone', count: everyone.length }, ...roles.map((r) => ({ id: r, label: ROLE_LABEL[r] ?? r, count: everyone.filter((m) => m.role === r).length }))]} />
      </Toolbar>
      <Loaded query={list} empty={(d) => (d.length === 0 ? <Empty title="No team members" body="Add people to work with you." /> : null)}>
        {() => (
          <Paged rows={rows}>
            {(page, pager) => (
          <Table min={560} footer={pager}>
            <thead><tr><Head>Name</Head><Head>Email</Head><Head>Role</Head><Head>Joined</Head></tr></thead>
            <tbody>
              {page.map((m) => (
                <tr key={m.id}>
                  <Cell>{m.full_name || m.email}{m.email === email ? <span className="ml-2"><Badge>You</Badge></span> : null}</Cell>
                  <Cell className="text-muted-foreground">{m.email}</Cell>
                  <Cell>{isOwner && m.role !== 'organization_owner'
                    ? <select aria-label={`Role for ${m.email}`} value={m.role} disabled={change.isPending} onChange={(e) => change.mutate({ memberId: m.id, role: e.target.value })} className={selectInline}>{ASSIGNABLE.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}</select>
                    : <Badge tone={m.role === 'organization_owner' ? 'solid' : 'neutral'}>{ROLE_LABEL[m.role] ?? m.role}</Badge>}</Cell>
                  <Cell className="text-muted-foreground whitespace-nowrap">{m.joined_at ? shortDate(m.joined_at) : ''}</Cell>
                </tr>
              ))}
            </tbody>
          </Table>
            )}
          </Paged>
        )}
      </Loaded>
      {invites.data?.invites.length ? (
        <section aria-label="Open invites" className="flex flex-col gap-2">
          <h2 className="font-semibold text-[14px]">Waiting to join</h2>
          <Table min={520}>
            <thead><tr><Head>Email</Head><Head>Role</Head><Head>Link expires</Head><Head /></tr></thead>
            <tbody>{invites.data.invites.map((i) => <tr key={i.id}><Cell>{i.email}</Cell><Cell><Badge>{ROLE_LABEL[i.role] ?? i.role}</Badge></Cell><Cell className="text-muted-foreground">{shortDate(i.expires_at)}</Cell><Cell right className="[font-family:inherit] tracking-normal"><button className="text-[13px] font-medium underline underline-offset-[3px] cursor-pointer" disabled={revoke.isPending} onClick={() => revoke.mutate(i.id)}>Cancel</button></Cell></tr>)}</tbody>
          </Table>
        </section>
      ) : null}
      <Modal open={link !== null} onClose={() => setLink(null)} title="Send them this link">
        <div className="flex flex-col gap-3 min-w-0">
          <p className="text-[13.5px]">{link?.email} doesn't have an account yet. Send them this link to join. It only works with that email, lasts 14 days, and this is the only time you'll see it.</p>
          <Input aria-label="Invite link" readOnly value={link?.url ?? ''} onFocus={(e) => e.target.select()} className="fig" />
          <div className="flex justify-end gap-2">
            <button className={btn.plain} onClick={() => void navigator.clipboard.writeText(link?.url ?? '').then(() => toast.success('Link copied'))}>Copy link</button>
            <button className={btn.primary} onClick={() => setLink(null)}>Done</button>
          </div>
        </div>
      </Modal>
      <Modal open={adding} onClose={() => setAdding(false)} title="Add team member">
        <FormBody onSubmit={() => add.mutate()} submit="Add" pending={add.isPending} onCancel={() => setAdding(false)} disabled={!newEmail.trim()}>
          <Text label="Work email" hint="If they don't have an account yet, you'll get a link to send them." type="email" required value={newEmail} onChange={setNewEmail} />
          <Choice label="Role" value={role} onChange={setRole} hint={ASSIGNABLE.find((r) => r.value === role)?.hint} options={ASSIGNABLE} />
        </FormBody>
      </Modal>
    </Screen>
  )
}

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
  const Section = ({ title, children }: { title: string; children: React.ReactNode }) => <section className="sheet px-3.5 py-3 flex flex-col gap-2.5"><h2 className="font-semibold text-[13.5px]">{title}</h2><div className="grid sm:grid-cols-2 xl:grid-cols-4 gap-3">{children}</div></section>
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
        </> })}
      </FormBody>
    </Screen>
  )
}

export function Settings() {
  const { userId, profile, email, pro, setPro, orgs, org, setOrg } = useApp()
  const { dark, toggle } = useTheme()
  const [name, setName] = useState(profile?.full_name ?? '')
  const [phone, setPhone] = useState(profile?.phone ?? '')
  const [addingOrg, setAddingOrg] = useState(false)
  const save = useSave(() => call('DataService', 'updateUserProfile', [userId, { full_name: name.trim() || null, phone: phone.trim() || null }]), { success: 'Profile saved', refresh: ['bootstrap'] })
  const segment = (active: boolean) => cn('h-7 px-3 rounded-[5px] text-[13px] cursor-pointer', active ? 'bg-card font-medium shadow-[0_0_0_1px_var(--border)]' : 'text-muted-foreground')
  return (
    <Screen title="Settings" sub={email} tabs={<SettingsTabs />}>
      <div className="grid gap-3.5 lg:grid-cols-2 items-start">
      <section className="sheet px-3.5 py-3">
        <h2 className="font-semibold text-[13.5px] mb-2.5">Profile</h2>
        <FormBody onSubmit={() => save.mutate()} submit="Save profile" pending={save.isPending}>
          <div className="grid sm:grid-cols-2 gap-3">
            <Text label="Full name" autoComplete="name" value={name} onChange={setName} />
            <Text label="Phone" autoComplete="tel" value={phone} onChange={setPhone} />
          </div>
        </FormBody>
      </section>
      <section className="sheet px-3.5 py-3 flex flex-col gap-3">
        <h2 className="font-semibold text-[13.5px]">Preferences</h2>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex-1 basis-[220px] min-w-0"><p className="font-medium text-[13.5px]">Appearance</p><p className="text-[12.5px] text-muted-foreground">Light or dark theme.</p></div>
          <div className="flex p-0.5 rounded-[7px] border border-border bg-muted" role="group" aria-label="Appearance"><button aria-pressed={!dark} onClick={() => { if (dark) toggle() }} className={segment(!dark)}>Light</button><button aria-pressed={dark} onClick={() => { if (!dark) toggle() }} className={segment(dark)}>Dark</button></div>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex-1 basis-[220px] min-w-0"><p className="font-medium text-[13.5px]">Level of detail</p><p className="text-[12.5px] text-muted-foreground">Simple uses everyday words. Accountant shows codes, debits and credits.</p></div>
          <div className="flex p-0.5 rounded-[7px] border border-border bg-muted" role="group" aria-label="Level of detail"><button aria-pressed={!pro} onClick={() => setPro(false)} className={segment(!pro)}>Simple</button><button aria-pressed={pro} onClick={() => setPro(true)} className={segment(pro)}>Accountant</button></div>
        </div>
      </section>
      </div>
      <section className="sheet px-3.5 py-3">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div><h2 className="font-semibold text-[13.5px]">Organizations</h2><p className="text-[12.5px] text-muted-foreground">Choose the one to work in.</p></div>
          <button className={btn.plain} onClick={() => setAddingOrg(true)}>New organization</button>
        </div>
        <div role="group" aria-label="Organizations" className="flex flex-wrap gap-1.5 mt-2.5">
          {orgs.map((o) => <Chip key={o.id} active={o.id === org.id} onClick={() => setOrg(o.id)}>{o.name}<span className="opacity-70 text-[11.5px]">{ROLE_LABEL[o.role ?? ''] ?? ''}</span></Chip>)}
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
    <Screen search={<SearchIcon label="Search" placeholder="Search" value={search} onChange={setSearch} />} title="Super Admin" sub="Every user and organization on the platform.">
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
              <Chips label="Show" value={tab} onChange={(id) => setTab(id as typeof tab)} options={[{ id: 'users', label: 'Users', count: o.users.length }, { id: 'organizations', label: 'Organizations', count: o.organizations.length }, { id: 'memberships', label: 'Memberships', count: o.memberships.length }]} />
            </div>
            {tab === 'users' ? (
              <Paged rows={o.users.filter((u) => match(u.email, u.full_name))}>{(page, pager) => (
              <Table footer={pager}>
                <thead><tr><Head>Name</Head><Head>Email</Head><Head>Super admin</Head></tr></thead>
                <tbody>{page.map((u) => (
                  <tr key={u.id}><Cell>{u.full_name || u.email}{u.email === email ? <span className="ml-2"><Badge>You</Badge></span> : null}</Cell><Cell className="text-muted-foreground">{u.email}</Cell>
                  <Cell><label className="inline-flex items-center gap-2 cursor-pointer"><input type="checkbox" aria-label={`Super admin: ${u.email}`} checked={u.is_super_admin} disabled={setAdmin.isPending || u.email === email} onChange={(e) => setAdmin.mutate({ userId: u.id, isSuperAdmin: e.target.checked })} />{u.is_super_admin ? 'Yes' : 'No'}</label></Cell></tr>
                ))}</tbody>
              </Table>
              )}</Paged>
            ) : tab === 'organizations' ? (
              <Paged rows={o.organizations.filter((x) => match(x.name, x.owner_emails.join(' ')))}>{(page, pager) => (
              <Table footer={pager}>
                <thead><tr><Head>Organization</Head><Head>Owners</Head><Head right>Members</Head><Head>Created</Head></tr></thead>
                <tbody>{page.map((x) => <tr key={x.id}><Cell>{x.name}</Cell><Cell className="text-muted-foreground">{x.owner_emails.join(', ')}</Cell><Cell right>{x.member_count}</Cell><Cell className="text-muted-foreground whitespace-nowrap">{shortDate(x.created_at)}</Cell></tr>)}</tbody>
              </Table>
              )}</Paged>
            ) : (
              <Paged rows={o.memberships.filter((m) => match(m.email, m.organization_name, m.role))}>{(page, pager) => (
              <Table footer={pager}>
                <thead><tr><Head>Person</Head><Head>Organization</Head><Head>Role</Head></tr></thead>
                <tbody>{page.map((m) => (
                  <tr key={m.id}><Cell>{m.email}</Cell><Cell className="text-muted-foreground">{m.organization_name}</Cell>
                  <Cell>{m.role === 'organization_owner' ? <Badge tone="solid">Owner</Badge> : <select aria-label={`Role for ${m.email} in ${m.organization_name}`} value={m.role} disabled={setRole.isPending} onChange={(e) => setRole.mutate({ membershipId: m.id, role: e.target.value })} className={selectInline}>{ASSIGNABLE.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}</select>}</Cell></tr>
                ))}</tbody>
              </Table>
              )}</Paged>
            )}
          </>
        )}
      </Loaded>
    </Screen>
  )
}
